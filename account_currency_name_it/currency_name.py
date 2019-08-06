#-*- coding: utf-8 -*-

from odoo import models, fields, api
import dateutil.parser

class main_parameter(models.Model):
	_inherit='main.parameter'

	currency_name_id = fields.One2many('account_currency_name_it.currency_name','parameter_id', 'Nombre Monedas')


class currency_name(models.Model):
	_name = 'account_currency_name_it.currency_name'

	currency_id =  fields.Many2one('res.currency','Currency',required=True)
	name_plural = fields.Char(size=52, string='Nombre Prural',required=True)
	name_singular = fields.Char(size=52, string='Nombre Sigular',required=True)
	parameter_id = fields.Many2one('main.parameter','Parámetro')

class res_currency(models.Model):
	_inherit = 'res.currency'
	dets = fields.One2many('account_currency_name_it.currency_name','currency_id',string='Nombre')