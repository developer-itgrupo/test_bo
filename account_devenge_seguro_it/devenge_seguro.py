# -*- encoding: utf-8 -*-
from odoo import models, fields, api , exceptions
from odoo.exceptions import UserError
import base64
from datetime import datetime
from functools import reduce
import datetime
from odoo.exceptions import UserError, ValidationError

class crear_asiento_devenge(models.Model):
	_name = 'crear.asiento.devenge'

	diario = fields.Many2one('account.journal','Diario')

	@api.multi
	def do_rebuild(self):
		asiento_ids = []
		for i in self.env['ctrl.insurance.line'].browse(self.env.context['active_ids']):
			asiento = {
				'journal_id':self.diario.id,
				'date':i.date_due,
				'fecha_contable':i.date_due,
				'ref':i.parent_contract,
			}
			asi = self.env['account.move'].create(asiento)
			i.asiento = asi.id

			line = {
				'move_id':asi.id,
				'partner_id':i.parent_partner_id.id,
				'type_document_it':self.env['einvoice.catalog.01'].search([('code','=','00')])[0].id,
				'nro_comprobante':i.parent_contract,
				'account_id':i.parent_due_account_id.id,
				'debit':i.amount_due,
				'credit':0,
				'analytic_account_id':i.parent_analitic_account_id.id,
				'name':'DEVENGO ' + i.parent_name,
			}
			self.env['account.move.line'].create(line)


			line = {
				'move_id':asi.id,
				'partner_id':i.parent_partner_id.id,
				'type_document_it':self.env['einvoice.catalog.01'].search([('code','=','00')])[0].id,
				'nro_comprobante':i.parent_contract,
				'account_id':i.parent_insurance_account_id.id,
				'debit':0,
				'credit':i.amount_due,
				'name':'DEVENGO ' + i.parent_name,
			}
			self.env['account.move.line'].create(line)

			i.asiento.post()
			asiento_ids.append(i.asiento.id)

		return {
		    'name': 'Asientos de Devengo de Seguro',
            'view_mode': 'tree,form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'domain': [('id','in', asiento_ids )],
		}




class importacion_detalle_insurance(models.Model):
	_name = 'importacion.detalle.insurance'

	csv = fields.Binary('Csv Importacion',help="El csv del Cronograma es sin cabecera con estas columnas: Nro de Cuota, Fecha Devenge, Monto Inicial, Monto Devengado, Saldo")
	nombre = fields.Char('Nombre',default="Cronograma.csv")
	delimitador = fields.Char('Delimitador',default=',')


	@api.one
	def do_rebuild(self):
		parametros = self.env['main.parameter'].search([])[0]
		import_file = base64.b64decode(self.csv)
		import_lineas = import_file.split('\n')
		for i in import_lineas:
			detalle = i.split(self.delimitador)
			if len(detalle)== 5:
				datos = {
					'insurance_id':self.env.context['active_id'],
					'number_due':detalle[0],
					'date_due':detalle[1],
					'amount_ini':detalle[2],
					'amount_due':detalle[3],
					'insurance_balance':detalle[4],					
				}
				self.env['ctrl.insurance.line'].create(datos)



class ctrl_insurance(models.Model):
	_name='ctrl.insurance'

	name = fields.Char('Concepto')

	partner_id = fields.Many2one('res.partner','Partner')
	date = fields.Date('Fecha Inicial')

	amount_ins = fields.Float('Monto Seguro')
	insurance_account_id = fields.Many2one('account.account','Cuenta de Gasto Diferido')


	nro_dues = fields.Integer('Nro. de Cuotas')
	amount_due =  fields.Float('Monto Cuota')
	due_account_id = fields.Many2one('account.account','Cuenta de Gasto')

	analitic_account_id = fields.Many2one('account.analytic.account','Cuenta Analitica')
	contract = fields.Char('Nro. de Contrato')

	state  = fields.Selection([('draft','Borrador'),('process','Ejecucion'),('done','Finalizado')],'Estado',default='draft')
	line_ids = fields.One2many('ctrl.insurance.line','insurance_id','Detalle')

	saldo = fields.Float('Saldo',compute="get_saldo")


	@api.onchange('amount_ins','nro_dues')
	def onchange_monto_cuota(self):
		if self.amount_ins and self.nro_dues and self.nro_dues != 0:
			self.amount_due = self.amount_ins / self.nro_dues

	@api.one
	def validar(self):
		self.state = 'process'

	@api.one
	def finalizar(self):
		self.state = 'done'

	@api.one
	def cancelar(self):
		if self.state == 'done':
			self.state = 'process'
		elif self.state == 'process':
			self.state = 'draft'

	@api.one
	def unlink(self):
		if self.state != 'draft':
			raise UserError(u'No se puede eliminar un Seguro en proceso o finalizado.')
		t = super(ctrl_insurance,self).unlink()
		return t		

	@api.one
	def get_saldo(self):
		tmp = 0
		for i in self.line_ids:
			fecha = str(i.date_due).split('-')
			hoy = str(datetime.datetime.today())[:10].split('-')
			if fecha[0] == hoy[0] and fecha[1] == hoy[1]:
				tmp = i.insurance_balance
		self.saldo = tmp

	@api.multi
	def importacion_detalle(self):
		return {
		    'name': 'Importar Detalle',
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'importacion.detalle.insurance',
            'type': 'ir.actions.act_window',
            'target': 'new',
		}


class ctrl_insurance_line(models.Model):
	_name='ctrl.insurance.line'

	insurance_id = fields.Many2one('ctrl.insurance','Insurance')
	number_due = fields.Integer('Nro de Cuota')
	date_due = fields.Date('Fecha Devenge')
	amount_ini = fields.Float('Monto Inicial')
	amount_due = fields.Float('Monto Devengado')
	insurance_balance = fields.Float('Saldo')

	parent_partner_id = fields.Many2one(related='insurance_id.partner_id')
	parent_date = fields.Date(related="insurance_id.date")
	parent_amount_ins = fields.Float(related="insurance_id.amount_ins")
	parent_insurance_account_id = fields.Many2one(related="insurance_id.insurance_account_id")
	parent_nro_dues = fields.Integer(related="insurance_id.nro_dues")
	parent_amount_due =  fields.Float(related="insurance_id.amount_due")
	parent_due_account_id = fields.Many2one(related="insurance_id.due_account_id")
	parent_analitic_account_id = fields.Many2one(related="insurance_id.analitic_account_id")
	parent_contract = fields.Char(related="insurance_id.contract")
	parent_state = fields.Selection(related="insurance_id.state")
	parent_name = fields.Char(related='insurance_id.name')
	asiento = fields.Many2one('account.move','Asiento')


	@api.multi
	def create_move(self):
		return {		
		    'name': 'Crear Asiento Devenge',
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'crear.asiento.devenge',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'active_ids':self.env.context['active_ids']},
		}
