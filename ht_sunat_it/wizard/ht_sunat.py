# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

class ht_sunat(models.Model):
	_name = 'ht.sunat'
	_auto = False
	
	cuenta = fields.Char('cuenta', size=50)
	debe_si = fields.Float('Debe Saldo Inicial',digits=(12,2))
	haber_si = fields.Float('Debe Saldo Inicial',digits=(12,2))
	debe = fields.Float('Debe',digits=(12,2))
	haber = fields.Float('Haber',digits=(12,2))
	debe_trans = fields.Float('Debe Transferencia',digits=(12,2))
	haber_trans = fields.Float('Haber Transferencia',digits=(12,2))

	