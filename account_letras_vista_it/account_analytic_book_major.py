# -*- coding: utf-8 -*-

from openerp import models, fields, api

class view_estado_letras_final(models.Model):
	_name = 'view.estado.letras.final'
	_auto = False

	fecha_canje = fields.Date('Fecha Canje')
	fecha_vencimiento = fields.Date('Fecha Vencimiento')
	letra = fields.Char('Letra')
	nro_cliente = fields.Char('Nro. Cliente')
	cliente = fields.Char('Cliente')
	cuenta = fields.Char('Cuenta')
	moneda = fields.Char('Moneda')
	monto_canje_mn = fields.Float('Monto Canje MN')
	pagos_mn = fields.Float('Pagos MN')
	saldomn = fields.Float('Saldo MN')

	monto_canje_me = fields.Float('Monto Canje ME')
	pagos_me = fields.Float('Pagos ME')
	saldome = fields.Float('Saldo ME')
	estado = fields.Char('Estado')

	@api.model_cr    
	def init(self):
		self.env.cr.execute("""
			CREATE OR REPLACE VIEW public.estado_letras AS
SELECT a2.date,
   a2.date_maturity,
   a1.type_document_it,
   a1.nro_comprobante,
   a1.partner_id,
   a1.account_id,
       CASE
           WHEN a4.name IS NULL THEN 'PEN'::character varying
           ELSE a4.name
       END AS moneda,
   sum(a1.debit) AS monto_canje_mn,
   sum(a1.credit) AS pagos_mn,
   sum(a1.debit - a1.credit) AS saldomn,
   sum(
       CASE
           WHEN a1.amount_currency > 0::numeric THEN a1.amount_currency
           ELSE 0::numeric
       END) AS monto_canje_me,
   sum(
       CASE
           WHEN a1.amount_currency < 0::numeric THEN a1.amount_currency
           ELSE 0::numeric
       END) AS pagos_me,
   sum(a1.amount_currency) AS saldome
  FROM account_move_line a1
    LEFT JOIN ( SELECT a2_1.date,
           a1_1.date_maturity,
           a1_1.type_document_it,
           a1_1.nro_comprobante,
           a1_1.partner_id,
           a1_1.account_id
          FROM account_move_line a1_1
            LEFT JOIN account_move a2_1 ON a2_1.id = a1_1.move_id
            LEFT JOIN account_letras_payment a3_1 ON a3_1.asiento = a2_1.id
         WHERE (a1_1.account_id IN ( SELECT account_account.id
                  FROM account_account
                 WHERE "left"(account_account.code::text, 3) = '123'::text)) AND a3_1.asiento IS NOT NULL) a2 ON concat(a2.type_document_it, a2.nro_comprobante, a2.partner_id, a2.account_id) = concat(a1.type_document_it, a1.nro_comprobante, a1.partner_id, a1.account_id)
    LEFT JOIN account_account a3 ON a3.id = a1.account_id
    LEFT JOIN res_currency a4 ON a4.id = a3.currency_id
 WHERE (a1.account_id IN ( SELECT account_account.id
          FROM account_account
         WHERE "left"(account_account.code::text, 3) = '123'::text))
 GROUP BY a2.date, a2.date_maturity, a1.type_document_it, a1.nro_comprobante, a1.partner_id, a1.account_id, a4.name;


	CREATE OR REPLACE VIEW public.view_estado_letras_final AS
SELECT row_number() OVER () AS id,
lt.date AS fecha_canje,
   lt.date_maturity AS fecha_vencimiento,
   lt.nro_comprobante AS letra,
   cli.nro_documento AS nro_cliente,
   cli.name AS cliente,
   cta.code AS cuenta,
   lt.moneda,
   lt.monto_canje_mn,
   lt.pagos_mn,
   lt.saldomn,
   lt.monto_canje_me,
   lt.pagos_me,
   lt.saldome,
       CASE
           WHEN lt.moneda::text = 'PEN'::text THEN
           CASE
               WHEN lt.saldomn = 0::numeric THEN 'PAGADA'::text
               ELSE 'PENDIENTE'::text
           END
           ELSE
           CASE
               WHEN lt.saldome = 0::numeric THEN 'PAGADA'::text
               ELSE 'pendiente'::text
           END
       END AS estado
  FROM estado_letras lt
    LEFT JOIN account_account cta ON cta.id = lt.account_id
    LEFT JOIN res_partner cli ON cli.id = lt.partner_id;


 """)