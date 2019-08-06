# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.osv import expression

class account_move(models.Model):
	_inherit = 'account.move'

	@api.model
	def create(self,vals):
		t = super(account_move,self).create(vals)
		anio = self.env['main.parameter'].search([])[0].fiscalyear
		if t.fecha_contable:
			if str(t.fecha_contable)[:4] != str(anio):
				raise ValidationError('La fecha contable esta en otro año fiscal.')
		return t


	@api.one
	def write(self,vals):
		t = super(account_move,self).write(vals)		
		anio = self.env['main.parameter'].search([])[0].fiscalyear
		if self.fecha_contable:
			if str(self.fecha_contable)[:4] != str(anio):
				raise ValidationError('La fecha contable esta en otro año fiscal.')
		return t