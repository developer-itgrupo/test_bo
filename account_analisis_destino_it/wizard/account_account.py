# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_account(models.Model):
	_inherit = 'account.account'

	had_account_analytic = fields.Boolean(string ="Necesita Cuenta Analítica", default=False)
	had_product = fields.Boolean(string ="Debe Tener Producto", default=False)

