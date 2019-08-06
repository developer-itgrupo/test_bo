from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError

class account_invoice_refund_ext(models.TransientModel):
	_inherit = 'account.invoice.refund'
	
	@api.model
	def _get_reason(self):
		val = super(account_invoice_refund_ext,self)._get_reason()
		return ''

	pruebis = fields.Char(string='Reason', default=_get_reason)
	description = fields.Char(string='Reason', required=True, default=_get_reason)