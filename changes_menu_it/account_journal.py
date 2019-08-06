# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from odoo import models, fields, api , exceptions, _


class account_journal(models.Model):
	_inherit = 'account.journal'
	
	