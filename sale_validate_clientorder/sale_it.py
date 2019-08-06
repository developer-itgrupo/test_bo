# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _
from openerp.exceptions import  Warning

class sale_order(models.Model):
	_inherit = 'sale.order'
	client_order_ref_state = fields.Char(' ', compute='calc_client_order_ref_state')

	@api.one
	def calc_client_order_ref_state(self):
		if self.client_order_ref:
			where = [('client_order_ref','=',self.client_order_ref),('partner_id','=',self.partner_id.id),('state','!=','cancel')]
			if self.id:
				where.append(('id','!=',self.id))

			order = self.env['sale.order'].search(where)
			if order:
				if len(order)>0:
					order = order[0]
				self.client_order_ref_state = 'Ya existe una orden de compra con ese numero ' + order.name
			else:
				self.client_order_ref_state = ' '

	@api.onchange('client_order_ref')
	def onchange_client_order_ref(self):
		self.calc_client_order_ref_state()


	# @api.onchange('client_order_ref')
	# def onchange_client_order_ref(self):
	# 	for record in self:
	# 		if record.client_order_ref:
	# 			if record.client_order_ref!='' and record.client_order_ref!=False:
	# 				existe = self.search([('partner_id','=',record.partner_id.id),('client_order_ref','=',record.client_order_ref),('state','!=','cancel')])
	# 				if len(existe)>0:
	# 					 raise Warning(u'La Orden de Compra del cliente '+record.partner_id.name+' ya fue registrada: '+existe[0].name)
    #
	# 	return
    #
	# @api.one
	# def write(self,vals):
    #
	# 	if 'client_order_ref' in vals:
	# 		if vals['client_order_ref']!='' and vals['client_order_ref']!=False:
	# 			valorcambiado = vals['client_order_ref']
	# 			existe = self.search([('partner_id','=',self.partner_id.id),('client_order_ref','=',valorcambiado),('state','!=','cancel')])
	# 			if len(existe)>0:
	# 				raise Warning(u'La Orden de Compra del cliente '+self.partner_id.name+' ya fue registrada: '+existe[0].name)
	# 	return super(sale_order,self).write(vals)
    #
	# @api.model
	# def create(self,vals):
	# 	print 1
	# 	if 'client_order_ref' in vals:
	# 		print 2
	# 		if vals['client_order_ref']!='' and vals['client_order_ref']!=False:
	# 			print 3
	# 			existe = self.search([('partner_id','=',vals['partner_id']),('client_order_ref','=',vals['client_order_ref']),('state','!=','cancel')])
	# 			if len(existe)>0:
	# 				raise Warning(u'La Orden de Compra ya fue registrada: '+existe[0].name)
	# 	return super(sale_order,self).create(vals)
