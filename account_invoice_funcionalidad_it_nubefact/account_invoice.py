# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import json
from odoo.tools import float_is_zero, float_compare


class account_invoice(models.Model):
	_inherit = 'account.invoice'

	

	@api.one
	def write(self,vals):
		t = super(account_invoice,self).write(vals)
		param = self.env['main.parameter'].search([])[0]
		self.refresh()
		for i in self.invoice_line_ids:
			if param.advance_product_id.id and param.advance_product_id.id == i.product_id.id and self.sunat_transaction_type != '4' and self.state == 'open':
				raise UserError('Esta factura contiene producto(s) de Anticipo, debe seleccionar en SUNAT Transaccion "Venta Interna - Anticipos"')
		return t