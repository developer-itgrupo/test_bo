# -*- encoding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

class saldo_comprobante_periodo_propietario_wizard(osv.TransientModel):
	_name='saldo.comprobante.periodo.propietario.wizard'

	@api.multi
	def do_rebuild(self):
 
		self.env.cr.execute("""
			drop view if exists vst_docs_apertura cascade;
			create view vst_docs_apertura as (

			 SELECT a1.account_id,
    a1.partner_id,
    a1.type_document_it,
    a1.nro_comprobante,
    a2.date,
    a1.date_maturity,
        CASE
            WHEN a3.name IS NULL THEN 'PEN'::text
            ELSE 'USD'::text
        END AS moneda,
        CASE
            WHEN a3.name IS NULL THEN a1.debit - a1.credit
            ELSE NULL::numeric
        END AS pventamn,
        CASE
            WHEN a3.name::text = 'USD'::text THEN a1.amount_currency
            ELSE NULL::numeric
        END AS pventame
   FROM account_move_line a1
     LEFT JOIN account_move a2 ON a2.id = a1.move_id
     LEFT JOIN res_currency a3 ON a3.id = a1.currency_id
     LEFT JOIN account_account a4 ON a4.id = a1.account_id
  WHERE a2.fecha_special = true AND date_part('year'::text, a2.date) = (( SELECT main_parameter.fiscalyear
           FROM main_parameter))::double precision AND date_part('month'::text, a2.date) <> '12'::double precision AND a4.internal_type::text = 'receivable'::text AND a2.state::text = 'posted'::text

			)""")



		self.env.cr.execute("""
			drop view if exists saldos_doc_apertura cascade;
			create view saldos_doc_apertura as (

			 SELECT a1.account_id,
    a1.partner_id,
    a1.type_document_it,
    a1.nro_comprobante,
    a1.date,
    a1.date_maturity,
    a1.moneda,
    a1.pventamn,
    a1.pventame,
    sum(a2.debit - a2.credit) AS saldomn,
    sum(a2.amount_currency) AS saldome,
    max(a2.create_uid) AS propietario
   FROM vst_docs_apertura a1
     LEFT JOIN account_move_line a2 ON concat(a2.account_id, a2.partner_id, a2.type_document_it, a2.nro_comprobante) = concat(a1.account_id, a1.partner_id, a1.type_document_it, a1.nro_comprobante)
  GROUP BY a1.account_id, a1.partner_id, a1.type_document_it, a1.nro_comprobante, a1.date, a1.date_maturity, a1.moneda, a1.pventamn, a1.pventame

			)""")




		self.env.cr.execute("""
			drop view if exists vst_ctasctes_apertura cascade;
			create view vst_ctasctes_apertura as (

			SELECT a1.date AS fecha_emi,
    a1.date_maturity AS fecha_ven,
    partner.nro_documento,
    partner.name AS cliente,
    doc.name AS tdoc,
    a1.nro_comprobante,
    a1.pventamn,
    a1.pventame,
        CASE
            WHEN a1.moneda = 'PEN'::text THEN a1.pventamn - a1.saldomn
            ELSE NULL::numeric
        END AS cancelamn,
        CASE
            WHEN a1.moneda = 'USD'::text THEN a1.pventame - a1.saldome
            ELSE NULL::numeric
        END AS cancelame,
    a1.saldomn,
    a1.saldome,
    a1.moneda,
    a1.propietario
   FROM saldos_doc_apertura a1
     LEFT JOIN res_partner partner ON partner.id = a1.partner_id
     LEFT JOIN einvoice_catalog_01 doc ON doc.id = a1.type_document_it

			)""")








		self.env.cr.execute("""
			drop view if exists vst_saldos_letras cascade;
			create view vst_saldos_letras as (
			 SELECT a1.account_id,
    a1.partner_id,
    a1.type_document_it,
    btrim(btrim(a1.nro_comprobante::text), chr(9)) AS nro_comprobante,
    min(a1.invoice_id) AS id_factura,
        CASE
            WHEN a3.name IS NULL THEN 'PEN'::text
            ELSE 'USD'::text
        END AS moneda,
    sum(a1.debit) AS debe,
    sum(a1.credit) AS haber,
    sum(a1.debit - a1.credit) AS saldomn,
    sum(a1.amount_currency) AS saldome
   FROM account_move_line a1
     LEFT JOIN account_account a2 ON a2.id = a1.account_id
     LEFT JOIN res_currency a3 ON a3.id = a2.currency_id
     LEFT JOIN account_move a4 ON a4.id = a1.move_id
  WHERE a2.internal_type::text = 'receivable'::text AND a2.centralized = true AND a4.state::text = 'posted'::text AND date_part('year'::text, a4.date) = (( SELECT main_parameter.fiscalyear
           FROM main_parameter))::double precision
  GROUP BY a1.account_id, a1.partner_id, a1.type_document_it, (btrim(btrim(a1.nro_comprobante::text), chr(9))), (
        CASE
            WHEN a3.name IS NULL THEN 'PEN'::text
            ELSE 'USD'::text
        END)

			)""")









		self.env.cr.execute("""
			drop view if exists vst_ctasctes_letras cascade;
			create view vst_ctasctes_letras as (

			 SELECT a7.fecha_canje AS fecha_emi,
    a2.fecha_vencimiento AS fecha_ven,
    a3.nro_documento,
    a3.name AS cliente,
    'LETRA'::text AS tdoc,
    a1.nro_comprobante,
        CASE
            WHEN a1.moneda = 'PEN'::text THEN a1.debe
            ELSE 0::numeric
        END AS pventamn,
        CASE
            WHEN a1.moneda = 'USD'::text THEN a2.monto_divisa
            ELSE 0::numeric
        END AS pventame,
        CASE
            WHEN a1.moneda = 'PEN'::text THEN a1.haber
            ELSE 0::numeric
        END AS cancelamn,
        CASE
            WHEN a1.moneda = 'USD'::text THEN a2.monto_divisa - a1.saldome
            ELSE 0::numeric
        END AS cancelame,
        CASE
            WHEN a1.moneda = 'PEN'::text THEN a1.saldomn
            ELSE 0::numeric
        END AS saldomn,
        CASE
            WHEN a1.moneda = 'USD'::text THEN a1.saldome
            ELSE 0::numeric
        END AS saldome,
    a1.moneda,
    t10.user AS propietario
   FROM vst_saldos_letras a1
     INNER JOIN account_letras_payment_letra_manual a2 ON a2.nro_letra::text = a1.nro_comprobante
     INNER JOIN res_partner a3 ON a3.id = a1.partner_id
     INNER JOIN account_letras_payment a7 ON a7.id = a2.letra_payment_id and a7.partner_id = a3.id

     LEFT JOIN (select letra_payment_id, max(ai.create_uid) as user from account_invoice ai
     inner join account_letras_payment_factura alpf on alpf.invoice_id = ai.id
     group by letra_payment_id) t10 on t10.letra_payment_id = a7.id




			)""")








		self.env.cr.execute("""
			drop view if exists vst_saldos_factura cascade;
			create view vst_saldos_factura as (
 SELECT a1.account_id,
    a1.partner_id,
    a1.type_document_it,
    btrim(btrim(a1.nro_comprobante::text), chr(9)) AS nro_comprobante,
    min(a1.invoice_id) AS id_factura,
    min(a1.id) AS id_apunte,
    sum(a1.debit) AS debe,
    sum(a1.credit) AS haber,
    sum(a1.debit - a1.credit) AS saldomn,
    sum(a1.amount_currency) AS saldome
   FROM account_move_line a1
     LEFT JOIN account_account a2 ON a2.id = a1.account_id
     LEFT JOIN account_move a3 ON a3.id = a1.move_id
  WHERE a2.internal_type::text = 'receivable'::text AND a3.state::text = 'posted'::text AND date_part('year'::text, a3.date) = (( SELECT main_parameter.fiscalyear
           FROM main_parameter))::double precision AND COALESCE(a2.centralized, false) = false
  GROUP BY a1.account_id, a1.partner_id, a1.type_document_it, (btrim(btrim(a1.nro_comprobante::text), chr(9)))

			)""")








		self.env.cr.execute("""
			drop view if exists vst_ctasctes_facturas cascade;
			create view vst_ctasctes_facturas as (

			SELECT a2.date_invoice AS fecha_emi,
    a2.date_due AS fecha_ven,
    a3.nro_documento,
    a3.name AS cliente,
    a4.name AS tdoc,
    a1.nro_comprobante,
        CASE
            WHEN a6.name::text = 'PEN'::text THEN a2.amount_total_company_signed
            ELSE 0::numeric
        END AS pventamn,
        CASE
            WHEN a6.name::text = 'USD'::text THEN a2.amount_total_signed
            ELSE 0::numeric
        END AS pventame,
        CASE
            WHEN a6.name::text = 'PEN'::text THEN a1.haber
            ELSE 0::numeric
        END AS cancelamn,
        CASE
            WHEN a6.name::text = 'USD'::text THEN a2.amount_total_signed - a1.saldome
            ELSE 0::numeric
        END AS cancelame,
        CASE
            WHEN a6.name::text = 'PEN'::text THEN a1.saldomn
            ELSE 0::numeric
        END AS saldomn,
        CASE
            WHEN a6.name::text = 'USD'::text THEN a1.saldome
            ELSE 0::numeric
        END AS saldome,
    a6.name AS moneda,
    a2.user_id AS propietario
   FROM vst_saldos_factura a1
     JOIN account_invoice a2 ON a2.id = a1.id_factura
     LEFT JOIN res_partner a3 ON a3.id = a1.partner_id
     LEFT JOIN einvoice_catalog_01 a4 ON a4.id = a1.type_document_it
     LEFT JOIN res_currency a6 ON a6.id = a2.currency_id

			)""")

		self.env.cr.execute("""
			drop view if exists vst_ctasctes_integral cascade;
			create view vst_ctasctes_integral as (
			SELECT vst_ctasctes_facturas.fecha_emi,
    vst_ctasctes_facturas.fecha_ven,
    vst_ctasctes_facturas.nro_documento,
    vst_ctasctes_facturas.cliente,
    vst_ctasctes_facturas.tdoc,
    vst_ctasctes_facturas.nro_comprobante,
    vst_ctasctes_facturas.pventamn,
    vst_ctasctes_facturas.pventame,
    vst_ctasctes_facturas.cancelamn,
    vst_ctasctes_facturas.cancelame,
    vst_ctasctes_facturas.saldomn,
    vst_ctasctes_facturas.saldome,
    vst_ctasctes_facturas.moneda,
    vst_ctasctes_facturas.propietario
   FROM vst_ctasctes_facturas
  WHERE (vst_ctasctes_facturas.saldomn + vst_ctasctes_facturas.saldome) <> 0::numeric
UNION ALL
 SELECT vst_ctasctes_letras.fecha_emi,
    vst_ctasctes_letras.fecha_ven,
    vst_ctasctes_letras.nro_documento,
    vst_ctasctes_letras.cliente,
    vst_ctasctes_letras.tdoc,
    vst_ctasctes_letras.nro_comprobante,
    vst_ctasctes_letras.pventamn,
    vst_ctasctes_letras.pventame,
    vst_ctasctes_letras.cancelamn,
    vst_ctasctes_letras.cancelame,
    vst_ctasctes_letras.saldomn,
    vst_ctasctes_letras.saldome,
    vst_ctasctes_letras.moneda,
    vst_ctasctes_letras.propietario
   FROM vst_ctasctes_letras
  WHERE (vst_ctasctes_letras.saldomn + vst_ctasctes_letras.saldome) <> 0::numeric
UNION ALL
 SELECT vst_ctasctes_apertura.fecha_emi,
    vst_ctasctes_apertura.fecha_ven,
    vst_ctasctes_apertura.nro_documento,
    vst_ctasctes_apertura.cliente,
    vst_ctasctes_apertura.tdoc,
    vst_ctasctes_apertura.nro_comprobante,
    vst_ctasctes_apertura.pventamn,
    vst_ctasctes_apertura.pventame,
    vst_ctasctes_apertura.cancelamn,
    vst_ctasctes_apertura.cancelame,
    vst_ctasctes_apertura.saldomn,
    vst_ctasctes_apertura.saldome,
    vst_ctasctes_apertura.moneda,
    vst_ctasctes_apertura.propietario
   FROM vst_ctasctes_apertura
  WHERE (vst_ctasctes_apertura.saldomn + vst_ctasctes_apertura.saldome) <> 0::numeric)

			""")	
		filtro = []
		#usuario = self.env['res.users'].browse(self.env.uid)

		#permisos = self.env['res.groups'].search([('name','=','Venta:Vendedor Normal')])[0]
		#if self.env.uid in permisos.users.ids:
		#	filtro.append( ('propietario','=',self.env.uid) )

		#permisos = self.env['res.groups'].search([('name','=','Venta:Vendedor Coorporativo')])[0]
		#if self.env.uid in permisos.users.ids:
		#	filtro.append( ('propietario','=',self.env.uid) )

		#permisos = self.env['res.groups'].search([('name','=','Venta:Jefe de Equipo')])[0]
		#if self.env.uid in permisos.users.ids:
		#	contenedor = [self.env.uid]
		#	teams = self.env['crm.team'].search([('user_id','=',self.env.uid)])
		#	for team in teams:
		#		for i in team.member_ids:
		#			if i.id not in contenedor:
		#				contenedor.append(i.id)
			# allpartner = self.env['res.users'].search([])
			# for i in allpartner:
			# 	if i.partner_id.team_id.id == usuario.partner_id.team_id.id:
			# 		contenedor.append(i.id)

		#	filtro.append( ('propietario','in',contenedor ) )


		#permisos = self.env['res.groups'].search([('name','=','Venta:Gerente')])[0]
		#if self.env.uid in permisos.users.ids:
		#	filtro = []


		self.env.cr.execute("""  DROP VIEW IF EXISTS saldo_comprobante_periodo_propietario;
			create or replace view saldo_comprobante_periodo_propietario as (

			select row_number() OVER () AS id,* from
			(
				select * from vst_ctasctes_integral 

				) T
			)

			""")
		
		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})

		direccion = self.env['main.parameter'].search([])[0].dir_create_file

		workbook = Workbook(direccion +'reporteperiodo.xlsx')
		worksheet = workbook.add_worksheet("Saldo Comprobantes x Periodo")
		#Print Format
		worksheet.set_landscape() #Horizontal
		worksheet.set_paper(9) #A-4
		worksheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
		worksheet.fit_to_pages(1, 0)  # Ajustar por Columna	

		bold = workbook.add_format({'bold': True})
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_text_wrap()
		boldbord.set_font_size(9)
		boldbord.set_bg_color('#DCE6F1')
		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		bord = workbook.add_format()
		bord.set_border(style=1)
		bord.set_text_wrap()
		numberdos.set_border(style=1)
		numbertres.set_border(style=1)	


		title = workbook.add_format({'bold': True})
		title.set_align('center')
		title.set_align('vcenter')
		title.set_text_wrap()
		title.set_font_size(20)
		worksheet.set_row(0, 30)

		x= 4				
		tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tam_letra = 1.2
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		worksheet.merge_range(0,0,0,11, u"Cuenta Corriente a la fecha", title)


		worksheet.write(3,0, u"Propietario",boldbord)
		worksheet.write(3,1, u"Fecha Emision",boldbord)
		worksheet.write(3,2, u"Fecha Vencimiento",boldbord)
		worksheet.write(3,3, u"Nro Documento",boldbord)
		worksheet.write(3,4, u"Cliente",boldbord)
		worksheet.write(3,5, u"TD",boldbord)
		worksheet.write(3,6, u"Nro Comprobante",boldbord)
		worksheet.write(3,7, u"Precio Venta MN",boldbord)
		worksheet.write(3,8, u"Precio Venta ME",boldbord)
		worksheet.write(3,9, u"Cancela MN",boldbord)
		worksheet.write(3,10, u"Cancela ME",boldbord)
		worksheet.write(3,11, u"Saldo MN",boldbord)
		worksheet.write(3,12, u"Saldo ME",boldbord)
		worksheet.write(3,13, u"Moneda",boldbord)



		for line in self.env['saldo.comprobante.periodo.propietario'].search(filtro):
			worksheet.write(x,0,line.propietario_name if line.propietario_name else '' ,bord )
			worksheet.write(x,1,line.fecha_emi if line.fecha_emi else '' ,bord )
			worksheet.write(x,2,line.fecha_ven if line.fecha_ven  else '',bord )
			worksheet.write(x,3,line.nro_documento if line.nro_documento  else '',bord)
			worksheet.write(x,4,line.cliente if line.cliente  else '',bord)
			worksheet.write(x,5,line.tdoc if line.tdoc  else '',bord)
			worksheet.write(x,6,line.nro_comprobante if line.nro_comprobante  else '',bord)
			worksheet.write(x,7,line.pventamn ,numberdos)
			worksheet.write(x,8,line.pventame ,numberdos)
			worksheet.write(x,9,line.cancelamn ,numberdos)
			worksheet.write(x,10,line.cancelame ,numberdos)
			worksheet.write(x,11,line.saldomn ,numberdos)
			worksheet.write(x,12,line.saldome ,numberdos)
			worksheet.write(x,13,line.moneda if line.moneda  else '',bord)
			
			

			x = x +1

		tam_col = [15,11,14,14,14,12,13,11,10,14,14,10,14,13,14,10,16,16,20,36]


		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])
		worksheet.set_column('H:H', tam_col[7])
		worksheet.set_column('I:I', tam_col[8])
		worksheet.set_column('J:J', tam_col[9])
		worksheet.set_column('K:K', tam_col[10])
		worksheet.set_column('L:L', tam_col[11])
		worksheet.set_column('M:M', tam_col[12])
		worksheet.set_column('N:N', tam_col[13])
		worksheet.set_column('O:O', tam_col[14])
		worksheet.set_column('P:P', tam_col[15])
		worksheet.set_column('Q:Q', tam_col[16])
		worksheet.set_column('R:R', tam_col[17])
		worksheet.set_column('S:S', tam_col[18])
		worksheet.set_column('T:T', tam_col[19])

		workbook.close()
		
		f = open(direccion + 'reporteperiodo.xlsx', 'rb')
		
		
		sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
		vals = {
			'output_name': 'ReportePeriodo.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		sfs_id = self.env['export.file.save'].create(vals)

		#import os
		#os.system('c:\\eSpeak2\\command_line\\espeak.exe -ves-f1 -s 170 -p 100 "Se Realizo La exportación exitosamente Y A EDWARD NO LE GUSTA XDXDXDXDDDDDDDDDDDD" ')

		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id.id,
		    "target": "new",
		}


	