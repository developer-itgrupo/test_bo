# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api
import datetime


class res_partner(models.Model):
	_inherit='res.partner'
	@api.one
	def required_street(self):
		if self.is_company==True:
			if str(int(self.type_document_partner_it.code)) == '6':
				self.street_req=True

	street_req = fields.Boolean('sr',compute='required_street', store=False)

	@api.onchange('type_document_partner_it','is_company')
	def _onchange_required_street(self):
		if self.is_company:
			if str(int(self.type_document_partner_it.code))=='6' :
				self.street_req=True
			else:
				self.street_req=False
		else:
			self.street_req=False



class main_parameter(models.Model):
	_inherit='main.parameter'

	advance_product_id = fields.Many2one('product.product','Prod. Anticipo')
	resolution_nf = fields.Char(u'Resolución')
	web_qry_nf    = fields.Char(u'Web consulta')
	url_external_nf = fields.Char(u'URL Descarga Externa')
	serial_ids = fields.One2many('serial.nubefact','parameter_id','Series y Nubefact')




class serial_nubefact(models.Model):
	_name = 'serial.nubefact'
	is_einvoice = fields.Boolean(u'Fact. elecctrónica',default=True)
	serial_id   = fields.Many2one('it.invoice.serie','Serie')
	token_nf    = fields.Char(u'Token NubeFact')
	path_nf     = fields.Char(u'URL NubeFact')
	parameter_id = fields.Many2one('main.parameter','parametros')


class account_tax(models.Model):
	_inherit='account.tax'
	ebill_tax_type = fields.Selection([
		('1','Gravado - Operación Onerosa'),
		('2','Gravado – Retiro por premio'),
		('3','Gravado – Retiro por donación'),
		('4','Gravado – Retiro'),
		('5','Gravado – Retiro por publicidad'),
		('6','Gravado – Bonificaciones'),
		('7','Gravado – Retiro por entrega a trabajadores'),
		('8','Exonerado - Operación Onerosa'),
		('9','Inafecto - Operación Onerosa'),
		('10','Inafecto – Retiro por Bonificación'),
		('11','Inafecto – Retiro'),
		('12','Inafecto – Retiro por Muestras Médicas'),
		('13','Inafecto - Retiro por Convenio Colectivo'),
		('14','Inafecto – Retiro por premio'),
		('15','Inafecto - Retiro por publicidad'),
		('16','Exportación'),
		], 'F.E. Tipo de Impuesto')


