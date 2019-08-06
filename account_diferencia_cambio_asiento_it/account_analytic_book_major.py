# -*- coding: utf-8 -*-

from openerp import models, fields, api


class view_diferencia_cambio_it(models.Model):
	_name = 'view.diferencia.cambio.it'
	_auto = False

	period_id = fields.Many2one('account.period','Periodo')
	tipo = fields.Char('Tipo')
	cuenta = fields.Char('Cuenta')
	debe = fields.Float('Debe')
	haber = fields.Float('Haber')
	saldomn = fields.Float('Saldo MN')
	saldome = fields.Float('Saldo ME')
	tc = fields.Float('TC',digits=(12,3))
	saldomn_act = fields.Float('Sañdp Mn Act')
	diferencia = fields.Float('Diferencia')
	resultado = fields.Char('Resultado')