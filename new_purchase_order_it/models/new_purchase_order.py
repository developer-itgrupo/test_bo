# -*- coding: utf-8 -*-

from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, AccessError
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp


class NewPurchaseOrder(models.Model):
	_inherit = ['purchase.order']
	_description = "New Model Purchase Order"
	_order = 'date_order desc, id desc'

	@api.multi
	def change_time_pdf(self):
		a=(datetime.strptime(self.date_planned, '%Y-%m-%d %H:%M:%S')-timedelta(hours=5))
		b=a.strftime('%Y-%m-%d %H:%M:%S')
		return b;
	@api.multi
	def change_time_pdf_order(self):
		a=(datetime.strptime(self.date_order, '%Y-%m-%d %H:%M:%S')-timedelta(hours=5))
		b=a.strftime('%Y-%m-%d %H:%M:%S')
		return b;

	