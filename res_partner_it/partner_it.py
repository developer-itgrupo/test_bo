# -*- encoding: utf-8 -*-
from openerp.osv import osv, expression
import base64
from openerp import models, fields, api , exceptions, _

class res_partner(models.Model):
	_inherit='res.partner'

	is_resident = fields.Boolean('No Domiciliado')
	es_empleado = fields.Boolean('Es Un Empleado')
	has_agree = fields.Boolean('Convenio Doble Imposicion')
	pais_residencia_nd = fields.Char('País de la residencia del sujeto no domiciliado')
	domicilio_extranjero_nd =fields.Char('Domicilio  en el extranjero del sujeto no domiciliado')
	numero_identificacion_nd =fields.Char('Número de identificación del sujeto no domiciliado')

	vinculo_contribuyente_residente_extranjero = fields.Char('Vinculo entre el contribuyente y el residente en el extranjero')
	convenios_evitar_doble_imposicion = fields.Char('Convenios para evitar la doble imposición')

	nombre = fields.Char('Nombre')
	apellido_p = fields.Char('Apellido Paterno')
	apellido_m = fields.Char('Apellido Materno')
	
	type_document_partner_it = fields.Many2one('einvoice.catalog.06','Tipo de Documento')
	nro_documento = fields.Char('Nro de Documento')

	@api.multi
	@api.onchange('type_document_partner_it','nro_documento')
	def onchange_type_nrodocumento(selfs):
		for self in selfs:
			'''
			if self.nro_documento and self.type_document_partner_it.id and self.type_document_partner_it.code == '6':
				self.write({'vat': 'PER' +  self.nro_documento,'no_mod':'1'})
			else:
				self.write({'vat':'','no_mod':'1'})	
			'''
			if self.nro_documento and self.type_document_partner_it.id and self.type_document_partner_it.code == '6':
				self.write({'vat': 'PER' +  self.nro_documento})
			else:
				self.write({'vat':''})

	'''
	@api.one
	def write(self,vals):
		t = super(res_partner,self).write(vals)
		if 'no_mod' in vals:
			pass
		else:
			self.onchange_type_nrodocumento()
		return t
	'''

	@api.model
	def create(self,vals):
		if not self.ref:
			vals['ref'] = self.nro_documento
		t = super(res_partner,self).create(vals)
		t.onchange_type_nrodocumento()
		return t

	@api.one
	def write(self,vals):
		print(self.ref)
		if not self.ref:
			vals['ref'] = self.nro_documento
		t = super(res_partner,self).write(vals)
		return t

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		partners =  self.search([] + args,limit=limit)
		if name:
			namex = name.split(' ')
			do = []
			for i in namex:
				do.append( ('name','ilike',i) )
			partners = self.search(do+args,limit=limit)
		if not partners:
			domain = [ ('nro_documento','=',name) ]
			partners = self.search(domain+args,limit=limit)
		return partners.name_get()
