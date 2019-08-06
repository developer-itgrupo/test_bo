# -*- coding: utf-8 -*-
import pprint
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class account_invoice(models.Model):
	_inherit = 'account.invoice'

	@api.multi
	def duplicate_fact_comp(selfs):
		for self in selfs:


			new_invoice = self.copy({'prueba':'1'})


			return {
        'type': 'ir.actions.act_window',
        'name': 'account.invoice_supplier_form',
        'res_model': 'account.invoice',
        'res_id': new_invoice.id,
        'view_type': 'form',
        'view_mode': 'form',
        'target' : 'self',
   		 }

