# -*- coding: utf-8 -*-

from openerp import models, fields, api
import base64
from openerp.osv import osv

class anticipo_proveedor(models.Model):
	_inherit = 'anticipo.proveedor'
	
	hide = fields.Boolean('Hide', default=False)
	small_cash_id = fields.Many2one('small.cash.another', 'Nro Caja Chica')
	
	
	@api.onchange('tipo','metodo_pago')
	def onchange_tipo_metodo_pago(self):
		if self.metodo_pago:
			self.hide = self.metodo_pago.is_small_cash
		return super(anticipo_proveedor,self).onchange_tipo_metodo_pago()
	
	@api.multi
	def entregar_button(self):
		x = super(anticipo_proveedor, self).entregar_button()
		if self.metodo_pago.is_small_cash:
			if self.move_id:
				for line in self.move_id.line_ids:

					if line.account_id.id == self.metodo_pago.default_debit_account_id.id:
						line.write({'small_cash_id': self.small_cash_id.id})
						line.move_id.write({'small_cash_id': self.small_cash_id.id})
		return x