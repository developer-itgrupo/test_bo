# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_account_analytic_rep(models.Model):

	_name='account.account.analytic.rep'
	_auto = False

	periodo = fields.Char(string='Periodo',size=30)
	libro = fields.Char(string='Libro',size=30)
	voucher = fields.Char(string='Voucher',size=30)
	fecha = fields.Date('Fecha')
	partner = fields.Char(string='Partner',size=100)
	comprobante = fields.Char(string='Comprobante',size=100)
	tipo = fields.Char(string='TC',size=100)
	cuenta = fields.Char(string='Cuenta Financiera',size=100)
	debe = fields.Float('Debe',digits=(12,2))
	haber = fields.Float('Haber',digits=(12,2))
	divisa = fields.Char(string='Divisa', size=30)
	importedivisa = fields.Float(string='Importe Divisa', digits=(12,2))
	ruc = fields.Char(string='RUC',size=11)
	ctaanalitica = fields.Char(string='Cta. Analítica',size=100)
	destinodebe = fields.Char(string='Destino Debe',size=100)
	destinodebename = fields.Char(string='Cuenta Destino Debe')
	destinohaber = fields.Char(string='Destino Haber',size=100)
	glosa = fields.Char(string='Glosa',size=100)
	fecha_ini = fields.Date('Fecha')
	fecha_fin = fields.Date('Fecha')
	
	@api.model_cr    
	def init(self):
		self.env.cr.execute("""
			drop view if exists account_account_analytic_rep;
			create or replace view account_account_analytic_rep as (

SELECT row_number() OVER () AS id,
	t.divisa,
	t.importedivisa,
	t.ruc,
	t.periodo,
	t.fecha,
	t.libro,
	t.tipo,
	t.voucher,
	t.partner,
	t.comprobante,
	t.cuenta,
	t.debe,
	t.haber,
	t.ctaanalitica,
	t.destinodebe,
	t.destinodebename,
	t.destinohaber,
	t.glosa,
	t.fecha_ini,
	t.fecha_fin
   FROM ( SELECT res_currency.name AS divisa,
			account_move_line.amount_currency AS importedivisa,
			res_partner.nro_documento AS ruc,
			account_period.name AS periodo,
			account_move.date AS fecha,
			account_journal.code AS libro,
			itd.code AS tipo,
			account_move.name AS voucher,
			res_partner.display_name AS partner,
			account_move_line.nro_comprobante AS comprobante,
			aa1.code AS cuenta,
			account_move_line.debit AS debe,
			account_move_line.credit AS haber,
			account_analytic_account.code AS ctaanalitica,
			aa3.code AS destinodebe,
			aa3.name AS destinodebename,
			aa2.code AS destinohaber,
			account_move_line.name AS glosa,
			account_period.date_start AS fecha_ini,
			account_period.date_stop AS fecha_fin
		   FROM account_move
			 JOIN account_period ON account_period.date_start <= account_move.fecha_contable and account_period.date_stop >= account_move.fecha_contable and account_period.special = account_move.fecha_special
			 JOIN account_journal ON account_move.journal_id = account_journal.id
			 JOIN account_move_line ON account_move_line.move_id = account_move.id
			 JOIN account_account aa1 ON aa1.id = account_move_line.account_id
			 JOIN account_account_type aat on aat.id = aa1.user_type_id
			 LEFT JOIN einvoice_catalog_01 itd ON itd.id = account_move_line.type_document_it
			 LEFT JOIN res_currency ON res_currency.id = account_move_line.currency_id
			 LEFT JOIN res_partner ON account_move_line.partner_id = res_partner.id
			 LEFT JOIN account_analytic_account ON account_analytic_account.id = account_move_line.analytic_account_id
			 LEFT JOIN account_account aa2 ON aa2.id =
				CASE
					WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id
					ELSE account_analytic_account.account_account_moorage_credit_id
				END
			 LEFT JOIN account_account aa3 ON aa3.id =
				CASE
					WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id
					ELSE account_analytic_account.account_account_moorage_id
				END
		  WHERE account_move.state::text = 'posted'::text AND (aa2.id > 0 OR aa3.id > 0) AND aat.type::text <> 'view'::text AND account_analytic_account.id IS NULL 
		UNION ALL
		 SELECT res_currency.name AS divisa,
			aml.amount_currency AS importedivisa,
			res_partner.nro_documento AS ruc,
			ap.name AS periodo,
			am.date AS fecha,
			account_journal.code AS libro,
			itd.code AS tipo,
			am.name AS voucher,
			res_partner.display_name AS partner,
			aml.nro_comprobante AS comprobante,
			aa1.code AS cuenta,
				CASE
					WHEN aal.amount < 0::numeric THEN (-1)::numeric * aal.amount
					ELSE 0::numeric
				END AS debe,
				CASE
					WHEN aal.amount > 0::numeric THEN aal.amount
					ELSE 0::numeric
				END AS haber,
			account_analytic_account.code AS ctaanalitica,
			aa3.code AS destinodebe,
			aa3.name AS destinodebename,
			aa2.code AS destinohaber,
			aml.name AS glosa,
			ap.date_start AS fecha_ini,
			ap.date_stop AS fecha_fin
		   FROM account_analytic_line aal
			 JOIN account_account aa1 ON aa1.id = aal.general_account_id
			 JOIN account_move_line aml ON aml.id = aal.move_id
			 JOIN account_move am ON am.id = aml.move_id
			 JOIN account_journal ON am.journal_id = account_journal.id
			 LEFT JOIN einvoice_catalog_01 itd ON itd.id = aml.type_document_it
			 LEFT JOIN res_currency ON res_currency.id = aml.currency_id
			 LEFT JOIN res_partner ON aml.partner_id = res_partner.id
			 LEFT JOIN account_analytic_account ON account_analytic_account.id = aal.account_id
			 JOIN account_account aa2 ON aa2.id =
				CASE
					WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id
					ELSE account_analytic_account.account_account_moorage_credit_id
				END
			 JOIN account_account aa3 ON aa3.id =
				CASE
					WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id
					ELSE account_analytic_account.account_account_moorage_id
				END
			 JOIN account_period ap ON  ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable  and ap.special = am.fecha_special 
		  WHERE aa1.check_moorage = true
  ORDER BY 4, 6, 8) t


						)""")





class account_account_analytic_rep_contable_unico(models.Model):
	_name='account.account.analytic.rep.contable.unico'
	_auto = False
	period = fields.Integer(string='Periodo')
	debe = fields.Float('Debe',digits=(12,2))
	haber = fields.Float('Haber',digits=(12,2))
	cuenta = fields.Integer('existencia')

	@api.model_cr    
	def init(self):
		self.env.cr.execute("""
			drop view if exists account_account_analytic_rep_contable_unico;
			create or replace view account_account_analytic_rep_contable_unico as (


select row_number() OVER() as id,*
from(
select cuenta, period, 
CASE WHEN sum(debe)-sum(haber)>0 THEN sum(debe)-sum(haber) else 0 END as debe,
CASE WHEN -sum(debe)+sum(haber)>0 THEN -sum(debe)+sum(haber) else 0 END as haber from 
(
select 
aa3.id as cuenta,
account_period.id as period,
case when sum(account_move_line.debit) - sum(account_move_line.credit) > 0 then sum(account_move_line.debit) - sum(account_move_line.credit)
else 0 end as debe,
case when sum(account_move_line.debit) - sum(account_move_line.credit) > 0 then 0
else -sum(account_move_line.debit) + sum(account_move_line.credit) end as haber
from account_move
inner join account_period on account_period.date_start <= account_move.fecha_contable and account_period.date_stop >= account_move.fecha_contable and account_period.special = account_move.fecha_special
inner join account_journal on account_move.journal_id = account_journal.id
inner join account_move_line on account_move_line.move_id = account_move.id   ----154
inner join account_account aa1 on aa1.id = account_move_line.account_id
inner join account_account_type aat on aat.id = aa1.user_type_id
left join account_analytic_account on account_analytic_account.id = account_move_line.analytic_account_id
inner join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
inner join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)
where account_move.state = 'posted' 
and aa2.id is not null and aa3.id is not null and account_analytic_account.id is null 
and aat.type != 'view'
group by account_period.id, aa3.id

union all


select 
aa3.id as cuenta,
ap.id as period,

case when aal.amount > 0 then 0
else -1*aal.amount end as debe,

case when aal.amount > 0 then aal.amount
else 0 end as haber
from account_analytic_line aal
inner join account_account aa1 on aa1.id = aal.general_account_id
inner join account_move_line aml on aml.id = aal.move_id
inner join account_move am on am.id = aml.move_id
left join account_analytic_account on account_analytic_account.id = aal.account_id
inner join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
inner join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)

			 JOIN account_period ap ON  ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable and ap.special = am.fecha_special
where aa1.check_moorage = True


union all


select 
aa2.id as cuenta,
ap.id as period,

case when aal.amount > 0 then aal.amount
else 0 end as debe,
case when aal.amount > 0 then 0
else -1*aal.amount end as haber
from account_analytic_line aal
inner join account_account aa1 on aa1.id = aal.general_account_id
inner join account_move_line aml on aml.id = aal.move_id
inner join account_move am on am.id = aml.move_id
left join account_analytic_account on account_analytic_account.id = aal.account_id
inner join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
inner join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)

			 JOIN account_period ap ON  ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable and ap.special = am.fecha_special
where aa1.check_moorage = True


union all
select 
aa2.id as cuenta,
account_period.id as period,
case when sum(account_move_line.debit) - sum(account_move_line.credit) > 0 then 0
else -sum(account_move_line.debit) + sum(account_move_line.credit) end as debe,
case when sum(account_move_line.debit) - sum(account_move_line.credit) > 0 then sum(account_move_line.debit) - sum(account_move_line.credit)
else 0 end as haber

from account_move
inner join account_period on account_period.date_start <= account_move.fecha_contable and account_period.date_stop >= account_move.fecha_contable and account_period.special = account_move.fecha_special
inner join account_journal on account_move.journal_id = account_journal.id
inner join account_move_line on account_move_line.move_id = account_move.id   ----154
inner join account_account aa1 on aa1.id = account_move_line.account_id
inner join account_account_type aat on aat.id = aa1.user_type_id
left join account_analytic_account on account_analytic_account.id = account_move_line.analytic_account_id
inner join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
inner join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)
where account_move.state = 'posted' 
and aa2.id is not null and aa3.id is not null and account_analytic_account.id is null 
and aat.type != 'view'
group by account_period.id, aa2.id

order by period,haber,debe
) AS M

group by period, cuenta
order by period,haber,debe
) AS T



)""")


