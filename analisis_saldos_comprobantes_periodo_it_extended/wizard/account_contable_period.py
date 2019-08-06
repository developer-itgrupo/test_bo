# -*- coding: utf-8 -*-

from openerp import models, fields, api

class saldo_comprobante_periodo(models.Model):

	_inherit='saldo.comprobante.periodo'
	
	tc = fields.Float('T.C.',digits=(12,3))