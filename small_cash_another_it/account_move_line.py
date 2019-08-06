# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _

class account_move_line(models.Model):
	_inherit = 'account.move.line'
	
	small_cash_id = fields.Many2one('small.cash.another', string="Caja Chica ID")
	small_cash_name = fields.Char('Caja Chica', size=64)

	@api.one
	def write(self,vals):
		if 'small_cash_id' in vals:
			small_cash = self.env['small.cash.another'].browse(vals['small_cash_id'])
			vals.update({'small_cash_name': small_cash.name})
		return super(account_move_line, self).write(vals)