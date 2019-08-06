# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class account_sequence(models.Model):
	_name = 'account.sequence'

	fiscalyear_id = fields.Many2one('account.fiscalyear','Año Fiscal')
	journal_id = fields.Many2one('account.journal','Libro')

	p0 = fields.Integer('Apertura',default=1)
	p1 = fields.Integer('Enero',default=1)
	p2 = fields.Integer('Febrero',default=1)
	p3 = fields.Integer('Marzo',default=1)
	p4 = fields.Integer('Abril',default=1)
	p5 = fields.Integer('Mayo',default=1)
	p6 = fields.Integer('Junio',default=1)
	p7 = fields.Integer('Julio',default=1)
	p8 = fields.Integer('Agosto',default=1)
	p9 = fields.Integer('Septiembre',default=1)
	p10 = fields.Integer('Octubre',default=1)
	p11 = fields.Integer('Noviembre',default=1)
	p12 = fields.Integer('Diciembre',default=1)
	p13 = fields.Integer('Cierre',default=1)