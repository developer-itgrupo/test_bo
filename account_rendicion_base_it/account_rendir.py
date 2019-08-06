# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class account_rendicion_it(models.Model):
	_name = 'account.rendicion.it'

	name = fields.Char('Nombre',default='/')
