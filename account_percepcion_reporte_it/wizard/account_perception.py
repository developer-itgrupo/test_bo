# -*- coding: utf-8 -*-

from openerp import models, fields, api




class account_perception_report(models.Model):

	_name='account.perception.report'
	_auto = False
	
	libro = fields.Char(string='Libro',size=200)
	voucher = fields.Char(string='Voucher',size=200)
	tipo_doc = fields.Char(string='Tipo Percepción', size=30)
	partner = fields.Char(string='Partner', size=200)
	ruc = fields.Char(string='RUC Agente',size=200)
	serie = fields.Char(string='Serie CP',size=200)
	numero = fields.Char('Número CP',size=200)
	fecha = fields.Date('Fecha CP')
	percepcion = fields.Float('Percepción',digits=(12,2))
	tipo_doc_2 = fields.Char('Tipo Com. Pago',size=200)
	serie_2 = fields.Char('Serie Com. Pago',size=200)
	numero_2 = fields.Char(string='Número Com. Pago',size=100)
	fecha_2 = fields.Date(string='Fecha Com. Pago')
	monto = fields.Float(string='Monto',digits=(12,2))
	periodo = fields.Char(string='Periodo',size=200)
	periodo_p = fields.Char(string='Periodo',size=200)

	@api.model_cr
	def init(self):
		self._cr.execute("""
			DROP VIEW IF EXISTS account_perception_report;
			create or replace view account_perception_report as (
select row_number() OVER() as id,* from (
select
aj.name as libro,
am.name as voucher,
itd.code as tipo_doc,
rp.name as partner,
rp.nro_documento as ruc,
substring(ai.reference from 0 for (position('-' in ai.reference) )) as serie,
substring(ai.reference from (position('-' in ai.reference)+1 )) as numero,
am.date as fecha, 
aml.tax_amount as percepcion,
CASE WHEN itd2.code is not NULL THEN CASE WHEN itd2.code in ('01','07','08','12') THEN itd2.code ELSE '99' END ELSE '' END as tipo_doc_2,
substring(aper.comprobante from 0 for (position('-' in aper.comprobante) )) as serie_2,
substring(aper.comprobante from (position('-' in aper.comprobante)+1 )) as numero_2,
aper.fecha as fecha_2,
aper.perception as monto,
ap.code as periodo,
ap_p.code as periodo_p
from account_move_line aml
cross join main_parameter mp
inner join account_move am on am.id = aml.move_id
inner join account_invoice ai on ai.move_id = am.id
inner join account_period ap on ap.date_start <= am.date and ap.date_stop >= am.date
inner join account_period ap_p on ap_p.date_start <= ai.fecha_perception and ap_p.date_stop >= ai.fecha_perception  
inner join einvoice_catalog_01 itd on itd.id = ai.it_type_document
inner join res_partner rp on am.partner_id = rp.id
inner join account_journal aj on aj.id = am.journal_id
left join account_perception aper on aper.father_invoice_id = ai.id  and ai.it_type_document = mp.account_perception_tipo_documento
left join einvoice_catalog_01 itd2 on itd2.id = aper.tipo_doc
where
aml.tax_code_id = mp.account_perception_igv) AS T
						)""")



class account_perception_reducida_report(models.Model):

	_name='account.perception.reducida.report'
	_auto = False
	
	libro = fields.Char(string='Libro',size=200)
	voucher = fields.Char(string='Voucher',size=200)
	tipo_doc = fields.Char(string='Tipo Percepción', size=30)
	partner = fields.Char(string='Partner', size=200)
	ruc = fields.Char(string='RUC Agente',size=200)
	serie = fields.Char(string='Serie CP',size=200)
	numero = fields.Char('Número CP',size=200)
	fecha = fields.Date('Fecha CP')
	percepcion = fields.Float('Percepción',digits=(12,2))
	periodo = fields.Char(string='Periodo',size=200)
	periodo_p = fields.Char(string='Periodo',size=200)

	@api.model_cr
	def init(self):
		self._cr.execute("""
			DROP VIEW IF EXISTS account_perception_reducida_report;
			create or replace view account_perception_reducida_report as (
select row_number() OVER() as id,* from (
select
aj.name as libro,
am.name as voucher,
itd.code as tipo_doc,
rp.name as partner,
rp.nro_documento as ruc,
substring(ai.reference from 0 for (position('-' in ai.reference) )) as serie,
substring(ai.reference from (position('-' in ai.reference)+1 )) as numero, 
am.date as fecha, 
aml.tax_amount as percepcion,
ap.code as periodo,
ap_p.code as periodo_p
from account_move_line aml
cross join main_parameter mp
inner join account_move am on am.id = aml.move_id
inner join account_invoice ai on ai.move_id = am.id
inner join account_period ap on ap.date_start <= am.date and ap.date_stop >= am.date
inner join account_period ap_p on ap_p.date_start <= ai.fecha_perception and ap_p.date_stop >= ai.fecha_perception  
inner join einvoice_catalog_01 itd on itd.id = ai.it_type_document
inner join res_partner rp on am.partner_id = rp.id
inner join account_journal aj on aj.id = am.journal_id
where
aml.tax_code_id = mp.account_perception_igv) AS T

)""")

