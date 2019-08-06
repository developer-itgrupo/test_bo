# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _

class account_move(models.Model):
	_inherit = "account.move"
	
	hide = fields.Boolean('Hide',compute='get_hide')
	small_cash_id = fields.Many2one('small.cash.another', 'Nro Caja Chica')
	
	@api.one
	@api.depends('journal_id')
	def get_hide(self):
		self.hide = True if self.journal_id.is_small_cash else False
	
	@api.model
	def create(self, vals):
		x = super(account_move, self).create(vals)
		if x.journal_id.is_small_cash:
			for line in x.line_ids:
				if line.account_id.id == x.journal_id.default_debit_account_id.id:
					line.write({'small_cash_id': x.small_cash_id.id})
		return x
	
	@api.one
	def write(self, vals):
		x = super(account_move, self).write(vals)
		if self.journal_id.is_small_cash:
			for line in self.line_ids:
				if line.account_id.id == self.journal_id.default_debit_account_id.id:
					line.write({'small_cash_id': self.small_cash_id.id})
		return x