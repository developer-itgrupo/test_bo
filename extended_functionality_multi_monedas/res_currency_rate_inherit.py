# -*- coding: utf-8 -*-

from openerp import models, fields, api
from odoo.exceptions import UserError, RedirectWarning, ValidationError

class res_currency_rate(models.Model):
	_inherit = 'res.currency.rate'


	@api.onchange('type_sale')
	def _onchange_price(self):
		# set auto-changing field

		this = self.env['res.currency.rate'].browse(self._origin.id)	
		if self.type_sale == 0.00:
			self.rate = 0
			this.write({'rate': (0.0)})
		else:
			self.rate = 1.0 / (self.type_sale)
			this.write({'rate': 1.0 / (self.type_sale)})
			
	
	@api.onchange('rate')
	def _onchange_rate(self):

		this = self.env['res.currency.rate'].browse(self._origin.id)
		if self.rate == 0.00:
			self.type_sale = 0
			this.write({'type_sale': (0.0)})
		else:
			self.type_sale = 1.0 / (self.rate)
			this.write({'type_sale': 1.0 / (self.rate)})
		# Can optionally return a warning and domains