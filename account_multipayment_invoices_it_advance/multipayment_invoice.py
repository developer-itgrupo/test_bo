# -*- encoding: utf-8 -*-
from odoo import models, fields, api , exceptions
from odoo.exceptions import UserError
import base64
from datetime import datetime
from functools import reduce

class MultipaymentadvanceInvoice(models.Model):
	_name='multipayment.advance.invoice'


	@api.onchange('payment_date')
	def onchange_get_exchange_type(self):
		if self.payment_date:
			exchange = self.env['res.currency.rate'].search([('name','=',self.payment_date)])
			if len(exchange)>0:
				self.exchange_type = exchange[0].type_sale


	@api.one
	def write(self,vals):
		t = super(MultipaymentadvanceInvoice,self).write(vals)		
		self.refresh()
		if self.asiento.id:
			self.asiento.means_payment_it = self.medio_pago.id
		return t


	payment_date = fields.Date('Fecha de pago')
	glosa = fields.Char('Glosa')
	nro_operation = fields.Char(u'Nro Operación Caja')
	journal_id = fields.Many2one('account.journal','Diario')	
	invoice_ids = fields.One2many('multipayment.advance.invoice.line','main_id','Facturas')
	state = fields.Selection([('draft','Borrador'),('done','Finalizado')],'Estado',default='draft')
	
	total_debe = fields.Float('Total Debe',digits=(12,2), compute="get_debe")
	total_haber = fields.Float('Total Haber',digits=(12,2), compute="get_haber")
	total_importe_div = fields.Float('Total Importe Divisa',digits=(12,2), compute="get_total_importe")
	diferencia = fields.Float('Diferencia',digits=(12,2), compute="get_diferencia")
	diferencia_visible= fields.Float('Diferencia',digits=(12,2),compute="get_dif_v")

	#Nuevos elementos
	medio_pago = fields.Many2one('einvoice.means.payment','Medio de Pago')
	nro_entra = fields.Many2one('account.rendicion.it','Nro. de Entrega')
	caja_chica = fields.Many2one('small.cash.another','Caja Chica')
	asiento = fields.Many2one('account.move','Asiento')
	exchange_type = fields.Float('Tipo cambio', digits=(12,3))

	_rec_name = 'payment_date'


	@api.one
	def get_diferencia(self):
		self.diferencia = self.total_debe - self.total_haber

	@api.one
	def get_dif_v(self):
		self.diferencia_visible =  self.total_haber - self.total_debe 

	@api.one
	def get_total_importe(self):
		tot = 0
		for i in self.invoice_ids:
			tot += i.importe_divisa
		self.total_importe_div = tot

	@api.one
	def get_debe(self):
		tot = 0
		for i in self.invoice_ids:
			tot += i.debe
		self.total_debe = tot


	@api.one
	def get_haber(self):
		tot = 0
		for i in self.invoice_ids:
			tot += i.haber
		self.total_haber = tot


	@api.one
	def cancelar(self):
		if self.asiento.id:
			for i in self.asiento.line_ids:
				i.remove_move_reconcile()

			if self.asiento.state != 'draft':
				self.asiento.button_cancel()

			self.asiento.unlink()
		self.state = 'draft'


	@api.one
	def crear_asiento(self):
		if True:

			move_id = False

			data_cabe = {
				'journal_id':self.journal_id.id,
				'date':self.payment_date,
				'ref':self.nro_operation,
			}
			move_id = self.env['account.move'].create(data_cabe)

			if self.diferencia != 0:
				data_line= {
					'name':self.glosa,
					'partner_id':False,
					'type_document_it':False,
					'nro_comprobante':self.nro_operation,
					'account_id':self.journal_id.default_debit_account_id.id,
					'currency_id':self.journal_id.currency_id.id,
					'amount_currency': (-self.total_importe_div) if self.journal_id.currency_id.id else 0,
					'debit':abs(self.diferencia) if self.diferencia<0 else 0,
					'credit':abs(self.diferencia) if self.diferencia>0 else 0,
					'move_id': move_id.id,
				}
				self.env['account.move.line'].create(data_line)

			
			for i in self.invoice_ids:
				if i.debe != 0 or i.haber != 0:
					data_lin = {
						'name':self.glosa,
						'partner_id':i.partner_id.id,
						'type_document_it':i.tipo_documento.id,
						'nro_comprobante':i.invoice_id.nro_comprobante if i.invoice_id.id else i.nro_comprobante_edit,
						'account_id':i.account_id.id,
						'currency_id':i.currency_id.id,
						'amount_currency': i.importe_divisa if i.importe_divisa else False,
						'debit':i.debe,
						'credit':i.haber,
						'move_id': move_id.id,
						'analytic_account_id': i.cta_analitica.id,
					}
					if i.fecha_vencimiento:
						data_lin['date_maturity'] = i.fecha_vencimiento
					newl= self.env['account.move.line'].create(data_lin)

					if i.invoice_id.id:
						conciliar = self.env['account.move.line'].browse([newl.id,i.invoice_id.id])
						conciliar.reconcile()

			self.asiento = move_id.id

		self.asiento.rendicion_id = self.nro_entra.id
		self.asiento.small_cash_id = self.caja_chica.id
		self.asiento.means_payment_it = self.medio_pago.id
		self.asiento.post()
		self.state = 'done'


class MultipaymentAdvanceInvoiceLine(models.Model):
	_name = 'multipayment.advance.invoice.line'

	main_id    = fields.Many2one('multipayment.advance.invoice')

	partner_id = fields.Many2one('res.partner','Partner')
	tipo_documento = fields.Many2one('einvoice.catalog.01','Tipo de Documento')	
	invoice_id = fields.Many2one('account.move.line','Factura')	
	account_id = fields.Many2one('account.account','Cuenta')
	currency_id = fields.Many2one('res.currency',string='Moneda',readonly=False)	
	fecha_vencimiento = fields.Date('Fecha Vencimiento')

	rest = fields.Float(string='Saldo MN',compute='_get_rest')
	rest_ext  = fields.Float('Saldo ME',digits=(12,2),compute="_get_rest_ext")
	rest_saldo_mo = fields.Float('Saldo',digits=(12,2),compute="_get_saldo_mo")
	rest_historico = fields.Float(string='Saldo')


	nro_comprobante_edit = fields.Char('Nro Comprobante') 
	cta_analitica = fields.Many2one('account.analytic.account','Cta. Analitica')
	importe_divisa = fields.Float('Importe Divisa')
	debe = fields.Float('Debe')
	haber = fields.Float('Haber')

	@api.onchange('importe_divisa')
	def onchange_importe_divisa(self):
		if self.importe_divisa:
			if self.importe_divisa >0:
				self.debe = self.importe_divisa * self.main_id.exchange_type
				self.haber = 0
			else:
				self.debe = 0
				self.haber = abs(self.importe_divisa) * self.main_id.exchange_type

	@api.one
	def _get_saldo_mo(self):
		self.rest_saldo_mo = self.rest_ext if self.currency_id.name == 'USD'  else self.rest	

	@api.model
	def create(self,vals):
		t = super(MultipaymentAdvanceInvoiceLine,self).create(vals)
		t.write({'rest_historico':t.rest_saldo_mo})
		return t


	@api.one
	def write(self,vals):
		t = super(MultipaymentAdvanceInvoiceLine,self).write(vals)

		if 'never' in self.env.context:
			pass
		else:
			if 'invoice_id' in vals:
				self.with_context({'never':'1'}).write({'rest_historico':self.rest_saldo_mo})
			self.refresh()
			if self.invoice_id.id:
				self.with_context({'never':'1'}).write({'nro_comprobante_edit':self.invoice_id.nro_comprobante})
		return t


	@api.onchange('invoice_id')
	def onchange_invoice_idmonto(self):
		self.rest_historico = self.rest_saldo_mo
		self.account_id = self.invoice_id.account_id.id
		self.currency_id = self.invoice_id.account_id.currency_id.id
		self.nro_comprobante_edit = self.invoice_id.nro_comprobante
		self.rest_historico = self.rest_ext if self.currency_id.name == 'USD'  else self.rest


	@api.depends('currency_id','invoice_id')
	def _get_rest_ext(self):
		for rec in self:
			rec.rest_ext = rec.invoice_id.amount_residual_currency

			if rec.invoice_id.account_id.internal_type  == 'payable':
				rec.rest_ext = -rec.rest_ext


	@api.depends('currency_id','invoice_id')
	def _get_rest(self):
		for rec in self:
			rec.rest = rec.invoice_id.amount_residual

			if rec.invoice_id.account_id.internal_type  == 'payable':
				rec.rest = -rec.rest

	
