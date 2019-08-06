# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class account_fiscalyear(models.Model):
	_name = 'account.fiscalyear'

	name = fields.Char('Año Fiscal',required=True)

	date_start = fields.Date('Fecha inicial',compute="get_date_start")
	date_stop = fields.Date('Fecha Final',compute="get_date_stop")

	@api.one
	def get_date_start(self):
		self.date_start = self.name + '-01-01'

	@api.one
	def get_date_stop(self):
		self.date_stop = self.name + '-12-31'

class account_period(models.Model):
	_name = 'account.period'

	name = fields.Char(u'Periodo')
	code = fields.Char('Codigo')
	date_start = fields.Date('Fecha Inicial')
	date_stop = fields.Date('Fecha Final')
	fiscalyear_id = fields.Many2one('account.fiscalyear','Año Fiscal')
	state = fields.Selection([('draft','Abierto'),('closed','Cerrado')],'Estado',default='draft')
	special = fields.Boolean('Es Periodo Apertura o Cierre',default=False)