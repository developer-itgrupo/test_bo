# -*- coding: utf-8 -*-

from odoo import api, fields, models, _ , exceptions

class account_period(models.Model):
	_inherit = 'account.period'

	journal_ids = fields.Many2many('account.journal','periods_journal_rel','period_id','journal_id','Diarios Cierre')


class account_move(models.Model):
	_inherit = 'account.move'

	@api.model
	def create(self,vals):
		t = super(account_move,self).create(vals)
		periodo = self.env['account.period'].search([('date_start','<=',t.fecha_contable),('date_stop','>=',t.fecha_contable),('special','<=',t.fecha_special)])
		if len(periodo)>0:
			periodo = periodo[0]
			if periodo.state == 'closed':
				raise exceptions.UserError('El periodo contable ' + periodo.code + ' ya se encuentra cerrado.')
			else:
				if t.journal_id.id in periodo.journal_ids.ids:
					raise exceptions.UserError('El periodo contable ' + periodo.code + ' ya se encuentra cerrado para este diario: ' + self.journal_id.code + '.')
		return t

	@api.one
	def write(self,vals):
		t = super(account_move,self).write(vals)
		periodo = self.env['account.period'].search([('date_start','<=',self.fecha_contable),('date_stop','>=',self.fecha_contable),('special','<=',self.fecha_special)])
		if len(periodo)>0:
			periodo = periodo[0]
			if periodo.state == 'closed':
				raise exceptions.UserError('El periodo contable ' + periodo.code + ' ya se encuentra cerrado.')
			else:
				if self.journal_id.id in periodo.journal_ids.ids:
					raise exceptions.UserError('El periodo contable ' + periodo.code + ' ya se encuentra cerrado para este diario: ' + self.journal_id.code + '.')
		return t

	@api.one
	def unlink(self):

		periodo = self.env['account.period'].search([('date_start','<=',self.fecha_contable),('date_stop','>=',self.fecha_contable),('special','<=',self.fecha_special)])
		if len(periodo)>0:
			periodo = periodo[0]
			if periodo.state == 'closed':
				raise exceptions.UserError('El periodo contable ' + periodo.code + ' ya se encuentra cerrado.')
			else:
				if self.journal_id.id in periodo.journal_ids.ids:
					raise exceptions.UserError('El periodo contable ' + periodo.code + ' ya se encuentra cerrado para este diario: ' + self.journal_id.code + '.')

		t = super(account_move,self).unlink()
		return t

		


class account_move_line(models.Model):
	_inherit = 'account.move.line'

	@api.model
	def create(self,vals):
		t = super(account_move_line,self).create(vals)
		periodo = self.env['account.period'].search([('date_start','<=',t.move_id.fecha_contable),('date_stop','>=',t.move_id.fecha_contable),('special','<=',t.move_id.fecha_special)])
		if len(periodo)>0:
			periodo = periodo[0]
			if periodo.state == 'closed':
				raise exceptions.UserError('El periodo contable ' + (periodo.code if periodo.code else '') + ' ya se encuentra cerrado.')
			else:
				if t.move_id.journal_id.id in periodo.journal_ids.ids:
					raise exceptions.UserError('El periodo contable ' + (periodo.code if periodo.code else '') + ' ya se encuentra cerrado para este diario: ' + (t.move_id.journal_id.name if t.move_id.journal_id.name else '') + '.')
		
		return t

	@api.one
	def write(self,vals):
		t = super(account_move_line,self).write(vals)
		if 'full_reconcile_id' in vals:
			return t
		periodo = self.env['account.period'].search([('date_start','<=',self.move_id.fecha_contable),('date_stop','>=',self.move_id.fecha_contable),('special','<=',self.move_id.fecha_special)])
		if len(periodo)>0:
			periodo = periodo[0]
			if periodo.state == 'closed':
				raise exceptions.UserError('El periodo contable ' + (periodo.code if periodo.code else '') + ' ya se encuentra cerrado.')
			else:
				if self.move_id.journal_id.id in periodo.journal_ids.ids:
					raise exceptions.UserError('El periodo contable ' + (periodo.code if periodo.code else '') + ' ya se encuentra cerrado para este diario: ' + (self.move_id.journal_id.name if self.move_id.journal_id.name else '') + '.')
		
		return t

	@api.one
	def unlink(self):
		periodo = self.env['account.period'].search([('date_start','<=',self.move_id.fecha_contable),('date_stop','>=',self.move_id.fecha_contable),('special','<=',self.move_id.fecha_special)])
		if len(periodo)>0:
			periodo = periodo[0]
			if periodo.state == 'closed':
				raise exceptions.UserError('El periodo contable ' + (periodo.code if periodo.code else '') + ' ya se encuentra cerrado.')
			else:
				if self.move_id.journal_id.id in periodo.journal_ids.ids:
					raise exceptions.UserError('El periodo contable ' + (periodo.code if periodo.code else '') + ' ya se encuentra cerrado para este diario: ' + (self.move_id.journal_id.name if self.move_id.journal_id.name else '') + '.')
		
		t = super(account_move_line,self).unlink()
		return t

		