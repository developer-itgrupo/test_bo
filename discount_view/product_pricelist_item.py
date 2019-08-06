# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import chain

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

import odoo.addons.decimal_precision as dp

class PricelistItem(models.Model):
    _inherit = "sale.order.line"


    