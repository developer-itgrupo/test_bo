# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _
from odoo.osv import expression
from odoo.tools import float_is_zero
from odoo.tools import float_compare, float_round, float_repr
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError
import time		
import codecs

class account_bank_statement_import_it(models.Model):
	_name = 'account.bank.statement.import.it'

	csv = fields.Binary('CSV Importación')
	separador = fields.Char('Separador',default=',')
	output_name = fields.Char('CSV NAME',default='Importacion.csv')
	@api.one
	def importar(self):		
		parametros = self.env['main.parameter'].search([])[0]
		import_file = base64.b64decode(self.csv)
		import_lineas = import_file.split('\n')
		for i in import_lineas:
			detalle = i.split(self.separador)
			if len(detalle)> 5:

				datos = {
					'date':detalle[0],
					'name':detalle[1],
					'partner_id': ( self.env['res.partner'].search([('nro_documento','=',detalle[2])])[0].id if len( self.env['res.partner'].search([('nro_documento','=',detalle[2])]) ) >0 else False ) if detalle[2] else False,
					'ref':detalle[3],
					'medio_pago': self.env['einvoice.means.payment'].search([('code','=',detalle[4])])[0].id if len( self.env['einvoice.means.payment'].search([('code','=',detalle[4])]) ) >0 else False ,
					'amount':float(detalle[5]),
					'statement_id': self.env.context['active_id'],
				}

				if not datos['medio_pago']:
					if detalle[4]== '':
						raise UserError( 'Medio de Pago es obligatorio y una linea no contiene información' )
					else:
						raise UserError( 'No existe el Medio de Pago: ' + detalle[4] )

				self.env['account.bank.statement.line'].create(datos)



class account_bank_statement(models.Model):
	_inherit='account.bank.statement'



	@api.multi
	def importar_lineas(self):
		return {		
			'type': 'ir.actions.act_window',
			'res_model': 'account.bank.statement.import.it',			    
			'views': [[False, 'form']],
			'target': 'new',
		}

	@api.multi
	@api.depends('name')
	def name_get(self):
		result = []
		for table in self:
			l_name =  table.name if table.name else '/'
			result.append((table.id, l_name ))
		return result

class account_bank_statement_line(models.Model):
	_inherit='account.bank.statement.line'

	medio_pago = fields.Many2one('einvoice.means.payment','Medio de Pago',required=False)

	def process_reconciliation(self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None):
		t = super(account_bank_statement_line,self).process_reconciliation(counterpart_aml_dicts, payment_aml_rec, new_aml_dicts)
		for i in t:
			for elem in i.line_ids:
				if elem.full_reconcile_id.id:
					other_l = self.env['account.move.line'].search([('id','!=',elem.id),('full_reconcile_id','=',elem.full_reconcile_id.id),('nro_comprobante','!=',False)])
					if len(other_l)>0:
						other_l = other_l[0]
						elem.nro_comprobante = other_l.nro_comprobante
						elem.type_document_it = other_l.type_document_it.id
			i.means_payment_it = self.medio_pago.id
		return t

	@api.one
	@api.constrains('amount')
	def _check_amount(self):
		return True

	@api.multi
	def button_cancel_reconciliation(self):
		t = super(account_bank_statement_line,self).button_cancel_reconciliation()
		for i in self:
			i.move_name = False
		return t


	@api.multi
	def edit_note(self):
		view_rec = self.env['ir.model.data'].get_object_reference('account_bank_statement_it', 'view_bank_statement_line_form_personalizado')
		view_id = view_rec and view_rec[1] or False		
		return {
			'view_id': [view_id],
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'account.bank.statement.line',
			'res_id': self.id,
			'type': 'ir.actions.act_window',
			'target': 'new',
			'context': self.env.context,
		}