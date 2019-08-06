# -*- encoding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv


class main_parameter(models.Model):
	_inherit = 'main.parameter'
	
	account_detracciones = fields.Many2one('account.account','Cuenta para Detracciones')
	diario_detracciones = fields.Many2one('account.journal','Diario para Detracciones')



class res_partner(models.Model):
	_inherit = 'res.partner'

	porcentaje = fields.Float('Porcentaje Detracción')

class create_detraccion(models.Model):
	_name = 'create.detraccion'

	fecha = fields.Date('Fecha')
	monto = fields.Float('Monto',digits=(12,2))

	@api.multi
	def generar(self):
		invoice = self.env['account.invoice'].search( [('id','=',self.env.context['invoice_id'])])[0]

		m = self.env['main.parameter'].search([])[0]
		if not m.diario_detracciones.id:
			raise osv.except_osv('Alerta!', "No esta configurada el diario de Detracción en Parametros.")
		if not m.account_detracciones.id:
			raise osv.except_osv('Alerta!', "No esta configurada la cuenta de Detracción en Parametros.")



		flag_ver = True
		data = {
			'journal_id': m.diario_detracciones.id,
			'ref':(invoice.number if invoice.number else 'Borrador'),
			#'period_id': invoice.period_id.id,
			'date': self.fecha,
		}
		if invoice.name_move_detraccion and invoice.diario_move_detraccion.id == m.diario_detracciones.id and invoice.fecha_move_detraccion == invoice.date_invoice:
			data['name']= invoice.name_move_detraccion
			flag_ver = False
		else:
			invoice.diario_move_detraccion= m.diario_detracciones.id
			invoice.fecha_move_detraccion = invoice.date_invoice
			flag_ver = True
		lines = []

		if invoice.currency_id.name == 'USD':

			line_cc = (0,0,{
				'account_id': invoice.account_id.id,
				'debit': self.monto * invoice.currency_rate_auto,
				'credit':0,
				'name':'PROVISION DE LA DETRACCION',
				'partner_id': invoice.partner_id.id,
				'nro_comprobante': invoice.reference,
				'type_document_it': invoice.it_type_document.id,
				'amount_currency': self.monto,
				'tc': invoice.currency_rate_auto,
				#'currency_rate_it': invoice.currency_rate_auto,
				'currency_id': invoice.currency_id.id,				
				})
			lines.append(line_cc)

			line_cc = (0,0,{
				'account_id': m.account_detracciones.id ,
				'debit': 0,
				'credit':self.monto * invoice.currency_rate_auto,
				'name':'PROVISION DE LA DETRACCION',
				'partner_id': invoice.partner_id.id,
				'nro_comprobante': invoice.reference,
				#'currency_rate_it': invoice.currency_rate_auto,
				'type_document_it': invoice.it_type_document.id,
				})
			lines.append(line_cc)

		else:
			line_cc = (0,0,{
				'account_id': invoice.account_id.id,
				'debit': self.monto,
				'credit':0,
				'name':'PROVISION DE LA DETRACCION',
				'partner_id': invoice.partner_id.id,
				'nro_comprobante': invoice.reference,
				'type_document_it': invoice.it_type_document.id,
				})
			lines.append(line_cc)

			line_cc = (0,0,{
				'account_id': m.account_detracciones.id ,
				'debit': 0,
				'credit':self.monto,
				'name':'PROVISION DE LA DETRACCION',
				'partner_id': invoice.partner_id.id,
				'nro_comprobante': invoice.reference,
				'type_document_it': invoice.it_type_document.id,
				})
			lines.append(line_cc)


		data['line_ids'] = lines
		tt = self.env['account.move'].create(data)
		if tt.state =='draft':
			tt.post()
		invoice.move_detraccion_id = tt.id

		if flag_ver:
			invoice.name_move_detraccion = tt.name

		vals_data = {}
		ids_conciliar = []
		for i1 in tt.line_ids:
			if i1.debit >0:
				ids_conciliar.append(i1.id)

		for i2 in invoice.move_id.line_ids:
			if i2.account_id.id == invoice.account_id.id:
				ids_conciliar.append(i2.id)

		concile_move = self.with_context({'active_ids':ids_conciliar}).env['account.move.line.reconcile'].create(vals_data)
		concile_move.trans_rec_reconcile_partial_reconcile()
		return True




class account_invoice(models.Model):
	_inherit = 'account.invoice'

	name_move_detraccion = fields.Char('nombre detraccion')
	diario_move_detraccion = fields.Many2one('account.journal','nombre diario')
	fecha_move_detraccion = fields.Date('Periodo')

	@api.one
	def get_estado_buttom_detraccion(self):
		if self.state in ('open','paid'):
			if self.move_detraccion_id.id:
				self.ver_estado_buttom_detraccion= 1
			else:
				self.ver_estado_buttom_detraccion= 2
		else:
			self.ver_estado_buttom_detraccion= 3


	move_detraccion_id = fields.Many2one('account.move','Asiento Detracción',copy=False)
	
	ver_estado_buttom_detraccion = fields.Integer('ver estado distrib', compute='get_estado_buttom_detraccion')

	@api.multi
	def action_cancel(self):

		vals_data = {}
		ids_conciliar = []
		for i1 in self.move_detraccion_id.line_ids:
			if i1.debit >0:
				ids_conciliar.append(i1.id)
		"""
		for i2 in self.move_id.line_id:
			if i2.account_id.id == self.account_id.id:
				ids_conciliar.append(i2.id)
		"""
		concile_move = self.with_context({'active_ids':ids_conciliar}).env['account.unreconcile'].create(vals_data)
		concile_move.trans_unrec()


		if self.move_detraccion_id.id:
			if self.move_detraccion_id.state != 'draft':
				self.move_detraccion_id.button_cancel()
			self.move_detraccion_id.unlink()
		return super(account_invoice,self).action_cancel()


	@api.multi
	def remove_detraccion_gastos(self):

		vals_data = {}
		ids_conciliar = []
		for i1 in self.move_detraccion_id.line_ids:
			if i1.debit >0:
				ids_conciliar.append(i1.id)
		"""
		for i2 in self.move_id.line_id:
			if i2.account_id.id == self.account_id.id:
				ids_conciliar.append(i2.id)
		"""
		concile_move = self.with_context({'active_ids':ids_conciliar}).env['account.unreconcile'].create(vals_data)
		concile_move.trans_unrec()


		if self.move_detraccion_id.id:
			if self.move_detraccion_id.state != 'draft':
				self.move_detraccion_id.button_cancel()
			self.move_detraccion_id.unlink()
		return True

	@api.multi
	def create_detraccion_gastos(self):
		context = {'invoice_id': self.id,'default_fecha': self.date_invoice ,
		'default_monto':self.amount_total * float(self.partner_id.porcentaje)/100.0}
		return {
				'type': 'ir.actions.act_window',
				'name': "Generar Detracción",
				'view_type': 'form',
				'view_mode': 'form',
				'context': context,
				'res_model': 'create.detraccion',
				'target': 'new',
		}


