# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _


class account_transfer_it(models.Model):
	_inherit = 'account.transfer.it'
	


	@api.onchange('monto','caja_origen','caja_destino','fecha','tc_personalizado')
	def onchange_monto(self):
		t = super(account_transfer_it,self).onchange_monto()
		if self.caja_origen.id:
			self.origin_hide = self.caja_origen.is_small_cash
		else:
			self.origin_hide = False


		if self.caja_destino.id:
			self.destiny_hide = self.caja_destino.is_small_cash
		else:
			self.destiny_hide = False
		return t

	
	origin_hide = fields.Boolean('Origin Hide', default=False, related="")
	destiny_hide = fields.Boolean('Destiny Hide', default=False)
	small_cash_origin_id = fields.Many2one('small.cash.another', 'Nro Caja Chica Origen')
	small_cash_destiny_id = fields.Many2one('small.cash.another', 'Nro Caja Chica Destino')


	
	@api.one
	def transferir(self):
		x = super(account_transfer_it, self).transferir()

		if  self.caja_origen.is_small_cash:
			for line in self.asiento_origen.line_ids:
				if line.account_id.id == self.caja_origen.default_debit_account_id.id:
					line.write({'small_cash_id': self.small_cash_origin_id.id})
		if self.caja_destino.is_small_cash:
			for line in self.asiento_destino.line_ids:
				if line.account_id.id == self.caja_destino.default_debit_account_id.id:
					line.write({'small_cash_id': self.small_cash_destiny_id.id})	
		return x
		