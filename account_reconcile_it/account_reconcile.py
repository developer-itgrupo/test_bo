# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountMove(models.Model):
	_inherit = 'account.move'

	@api.multi
	def reverse_moves(self,date=None, journal_id=None):
		t = super(AccountMove,self).reverse_moves()
		if date == None:
			if t:
				ac_move = self.env['account.move'].browse(t)
				ac_move.button_cancel()
				ac_move.unlink()
			ac_move_change = self.env['account.move'].browse(self.id)
			ac_move_change.button_cancel()
			ac_move_change.unlink()
		return t