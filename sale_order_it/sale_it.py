# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _


class sale_order_line(models.Model):
	_inherit = 'sale.order.line'

	analytic_id = fields.Many2one('account.analytic.account','Cuenta Analitica')
	
	@api.multi
	def _prepare_invoice_line(self, qty):
		t = super(sale_order_line,self)._prepare_invoice_line(qty)
		if 'account_analytic_id' in t and t['account_analytic_id'] and self.analytic_id.id:
			t['account_analytic_id'] = self.analytic_id.id
		return t
