# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions

class DeleteActionIT(models.Model):
	_name = "delete.action.it"

	@api.model
	def delete_function(self):
		self.env.ref('account.action_account_payment_from_invoices').unlink()
	
