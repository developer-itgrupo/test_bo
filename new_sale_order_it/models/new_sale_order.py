# -*- coding: utf-8 -*-

from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang

import odoo.addons.decimal_precision as dp

class NewPurchaseOrder(models.Model):
	_inherit = ['sale.order']
	_description = "New Model Sale Order"
	_order = 'date_order desc, id desc'

	@api.multi
	def change_time_pdf(self):
		a=(datetime.strptime(self.date_order, '%Y-%m-%d %H:%M:%S')-timedelta(hours=5))
		b=a.strftime('%Y-%m-%d %H:%M:%S')
		return b;
	@api.multi
	def print_quotation(self):
		self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
		return self.env['report'].get_action(self, 'new_sale_order_it.new_report_saleorder')


	