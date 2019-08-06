# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _
from odoo.exceptions import ValidationError

class account_journal(models.Model):
	_inherit = 'account.journal'
	
	register_sunat = fields.Selection((('1','Compras'),
									('2','Ventas'),
									('3','Honorarios'),
									('4','Retenciones'),
									('5','Percepciones')								
									),'Registro Sunat')

	asentar_automatic = fields.Boolean('Asentado Automatico')
	check_rendicion = fields.Boolean('Diario de Rendición')
	check_canje_letras = fields.Boolean('Se usa para Canje de Letras')

	@api.multi
	def generar_wizard(self):
		return self.env['sequence.wizard'].get_wizard(self.id)

	@api.one
	@api.constrains('code')
	def _check_amount(self):
		if self.code and self.id:
			otros = self.env['account.journal'].search([('code','=',self.code),('id','!=',self.id)])
			if len(otros)>0:
				raise ValidationError('Ya existe otro Diario con el mismo codigo')

				
class SequenceWizard(models.TransientModel):
	_name = 'sequence.wizard'

	fiscal_id = fields.Many2one('account.fiscalyear',u'Año Fiscal')
	journal_id = fields.Many2one('account.journal')

	@api.multi
	def get_wizard(self,journal_id):
		return {
			'name':_('Generar Secuencia'),
			'res_id':self.id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'sequence.wizard',
			'views':[[self.env.ref('account_journal_it.sequence_wizard_view').id,'form']],
			'type':'ir.actions.act_window',
			'target':'new',
			'context':{'default_journal_id':journal_id}
		}

	@api.multi
	def generar_secuencia(self):
		from datetime import datetime, timedelta	
		day = 1
		month = 1
		year = int(self.fiscal_id.name)
		self.journal_id.sequence_id.use_date_range = True
		self.journal_id.sequence_id.prefix = '%(month)s-'
		self.journal_id.sequence_id.padding = 6
		self.journal_id.sequence_id.code = 'account.journal'
		for fech in range(12):
			dia_1 = datetime(day=day,month=month,year=year)
			month+= 1
			if month == 13:
				month= 1
				year+= 1

			dia_2 = datetime(day=day,month=month,year=year) - timedelta(days=1)
			busqueda = self.env['ir.sequence.date_range'].search([('date_from','=',str(dia_1)[:10]),('date_to','=',str(dia_2)[:10]),('sequence_id','=',self.journal_id.sequence_id.id)])
			if len(busqueda)==0:
				data = {
					'date_from':str(dia_1)[:10],
					'date_to':str(dia_2)[:10],
					'sequence_id':self.journal_id.sequence_id.id,
					'number_next_actual':1,
				}
				self.env['ir.sequence.date_range'].create(data)

		return {
			'name':'Exitoso',
			'type':'ir.actions.act_window',
			'view_type':'form',
			'view_mode':'form',
			'res_model':'sh.message.wizard',
			'target':'new',
			'context':{'message':"Se ha generado las secuencias para el ejercicio fiscal '"+self.fiscal_id.name+"'" + ", y el diario '"+self.journal_id.name+"'"}
		}