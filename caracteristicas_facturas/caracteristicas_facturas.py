# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _
from odoo.exceptions import UserError
import datetime

	
class AccountInvoiceLine(models.Model):
	_inherit = "account.invoice.line"
	


	@api.onchange('product_id')
	def _onchange_product_id(self):

		t = super(AccountInvoiceLine,self)._onchange_product_id()
		if self.product_id.id:
			self.name = self.product_id.name_get()[0][1]


		return t






