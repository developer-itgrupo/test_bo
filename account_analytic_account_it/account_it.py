# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _

class account_analytic_account(models.Model):
	_inherit = 'account.analytic.account'

	account_account_moorage_id = fields.Many2one('account.account',string ="Amarre al Debe",index = True)
	account_account_moorage_credit_id = fields.Many2one('account.account',string ="Amarre al Haber",index = True)
	parent_id = fields.Many2one('account.analytic.account','Padre')
	type = fields.Selection([('view','Vista'),('account','Cuenta Analítica')],'Tipo')
	
