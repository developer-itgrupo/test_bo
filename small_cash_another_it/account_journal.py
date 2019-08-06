# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _

class account_journal(models.Model):
	_inherit = 'account.journal'
	
	max_import_cash = fields.Float('Max. Caja Chica', digits=(12,2))
	is_small_cash = fields.Boolean('Es Caja Chica', default=False)

