# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from odoo import models, fields, api , exceptions, _


class account_account_type_it(models.Model):
	_inherit = 'account.account.type.it'
	
	code = fields.Char('Codigo',size=8)