# -*- coding: utf-8 -*-

from openerp import models, fields, api
from odoo.exceptions import UserError, RedirectWarning, ValidationError

class res_currency(models.Model):
	_inherit = 'res.currency'

	
	@api.multi
	def compute(self, from_amount, to_currency, round=True):
		""" Convert `from_amount` from currency `self` to `to_currency`. """
		self, to_currency = self or to_currency, to_currency or self
		assert self, "compute from unknown currency"
		assert to_currency, "compute to unknown currency"
		# apply conversion rate
		if self == to_currency:
			to_amount = from_amount
		else:
			monto = self._get_conversion_rate(self, to_currency)
			to_amount = from_amount * ( float("%.4f"%(monto)) if monto>1 else monto)
		# apply rounding
		return to_currency.round(to_amount) if round else to_amount

class res_currency_rate(models.Model):
	_inherit = 'res.currency.rate'

	name = fields.Date('Fecha',required=True,selected=True)
	type_sale = fields.Float('Tipo de Venta', digits=(16,3))
	type_purchase = fields.Float('Tipo de Compra', digits=(16,3))


	@api.onchange('type_sale','rate')
	def _onchange_price(self):
		# set auto-changing field
		if self.type_sale == 0.00:
			self.rate = 0
			self.write({'rate': (0.0)})
		else:
			self.rate = 1.0 / (self.type_sale)
			self.write({'rate': (1.0 / (self.type_sale))})
	
		if self.rate == 0.00:
			self.type_sale = 0
		else:
			self.type_sale = 1.0 / (self.rate)
		# Can optionally return a warning and domains


class account_invoice(models.Model):
	_inherit = 'account.invoice'

	@api.one
	def write(self,vals):
		t = super(account_invoice,self).write(vals)
		self.refresh()
		if 'nomore' in vals:
			pass
		else:
			if self.currency_id.name != 'PEN' and self.state == 'draft':
				currency_obj = self.env['res.currency'].search([('name','=',self.currency_id.name)])
				if len(currency_obj)>0:
					currency_obj = currency_obj[0]
				else:
					raise UserError( 'Error!\nNo existe la moneda' )

				fecha = self.date_invoice if self.date_invoice else fields.Date.context_today(self)
				tipo_cambio = self.env['res.currency.rate'].search([('name','=',fecha),('currency_id','=',currency_obj.id)])

				if len(tipo_cambio)>0:
					tipo_cambio = tipo_cambio[0]
				else:
					raise UserError( 'Error!\nNo existe el tipo de cambio para la fecha: '+ str(fecha) )		
				vactual = 0
				ractual = 0
				if self.check_currency_rate:
					pass
				else:
					self.write({'currency_rate_auto':tipo_cambio.type_sale,'nomore':1})  
		return t



	@api.multi
	def action_move_create(selfs):
		for self in selfs:
			if self.currency_id.name != 'PEN':
				currency_obj = self.env['res.currency'].search([('name','=',self.currency_id.name)])
				if len(currency_obj)>0:
					currency_obj = currency_obj[0]
				else:
					raise UserError( 'Error!\nNo existe la moneda' )

				fecha = self.date if self.date else ( self.date_invoice if self.date_invoice else fields.Date.context_today(self) )
				tipo_cambio = self.env['res.currency.rate'].search([('name','=',fecha),('currency_id','=',currency_obj.id)])

				if len(tipo_cambio)>0:
					tipo_cambio = tipo_cambio[0]
				else:
					raise UserError( 'Error!\nNo existe el tipo de cambio para la fecha: '+ str(fecha) )
				
				vactual = 0
				ractual = 0

				#if self.check_currency_rate:
				if True:
					vactual = tipo_cambio.type_sale
					ractual = tipo_cambio.rate

					tipo_cambio.type_sale = self.currency_rate_auto
					print(self.currency_rate_auto)
					tipo_cambio.rate = 1.0 / self.currency_rate_auto

				else:
					self.currency_rate_auto = tipo_cambio.type_sale

				t = super(account_invoice,self).action_move_create()
				self.refresh()
				for i in self.move_id.line_ids:
					i.tc = tipo_cambio.type_sale
					if i.tax_amount:
						i.tax_amount = (i.debit + i.credit)* (1 if i.tax_amount > 0 else -1)

				if self.check_currency_rate:
					tipo_cambio.type_sale = vactual
					tipo_cambio.rate = ractual
			else:
				t = super(account_invoice,self).action_move_create()
		return True