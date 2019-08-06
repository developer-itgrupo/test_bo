# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _


class account_invoice(models.Model):
	_inherit = 'account.invoice'

	@api.onchange('partner_id', 'company_id')
	def _onchange_partner_id(self):
		res = super(account_invoice, self)._onchange_partner_id()
		if self.purchase_id.id:
			self.currency_id = self.purchase_id.currency_id.id
		return res

	@api.onchange('purchase_id')
	def purchase_order_change(self):
		flag = False
		curr = False
		if self.purchase_id.id:
			flag = True
			curr = self.purchase_id.currency_id.id		
		res = super(account_invoice, self).purchase_order_change()
		if flag:
			self.currency_id = curr
		return res


	@api.onchange('journal_id')
	def _onchange_journal_id(self):
		if self.journal_id and not 'default_purchase_id' in self.env.context:
			self.currency_id = self.journal_id.currency_id.id or self.journal_id.company_id.currency_id.id