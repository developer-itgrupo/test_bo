# -*- encoding: utf-8 -*-
from odoo import models, fields, api , exceptions
from odoo.exceptions import UserError
import base64
from datetime import datetime
from functools import reduce

class MultipaymentInvoice(models.Model):
	_name='multipayment.invoice'


	@api.onchange('payment_date')
	def onchange_get_exchange_type(self):
		if self.custom_exchange:
			pass
		else:
			exchange = self.env['res.currency.rate'].search([('name','=',self.payment_date)])
			if len(exchange)>0:
				self.exchange_type = exchange[0].type_sale


	@api.one
	def write(self,vals):
		t = super(MultipaymentInvoice,self).write(vals)		
		self.refresh()
		if self.asiento.id:
			self.asiento.means_payment_it = self.medio_pago.id
		if 'never' in self.env.context:
			pass
		else:
			if not self.custom_exchange:				
				exchange = self.env['res.currency.rate'].search([('name','=',self.payment_date)])
				if len(exchange)>0:
					self.with_context({'never':'1'}).write({'exchange_type': exchange[0].type_sale })
				else:
					self.with_context({'never':'1'}).write({'exchange_type': 1 })
		return t
			

	name = fields.Char('Nro. Canje', related="partner_id.name")
	partner_id = fields.Many2one('res.partner','Partner')
	payment_date = fields.Date('Fecha de pago')
	glosa = fields.Char('Glosa')
	nro_operation = fields.Char(u'Nro Operación Caja')
	journal_id = fields.Many2one('account.journal','Diario')
	invoice_ids = fields.One2many('multipayment.invoice.line','main_id','Facturas')
	state = fields.Selection([('draft','Borrador'),('done','Finalizado')],'Estado',default='draft')
	type_invoices = fields.Selection([('receivable','Ingreso'),('payable','Egreso')],'Tipo',default="receivable")
	ammount_total = fields.Float('MontoTotal',digits=(12,2))
	exchange_type = fields.Float('Tipo de cambio',default=1,digits=(12,3))
	unbalance_ammount = fields.Float(string='Monto Desbalance',compute="get_unbalance_ammount")
	custom_exchange = fields.Boolean(string='Tipo de cambio Personalizado?')
	asiento = fields.Many2one('account.move','Asiento Contable')
	medio_pago = fields.Many2one('einvoice.means.payment','Medio de Pago')
	cuenta_desbalance = fields.Many2one('account.account','Cuenta Desbalance')


	#Nuevos elementos
	medio_pago = fields.Many2one('einvoice.means.payment','Medio de Pago')
	nro_entra = fields.Many2one('account.rendicion.it','Nro. de Entrega')
	caja_chica = fields.Many2one('small.cash.another','Caja Chica')


	@api.one
	def actualizar(self):
		dif = 0
		if len(self.invoice_ids)>0:
			dif =reduce(lambda x,y: x+y,self.invoice_ids.mapped('amount_sol'))
		self.ammount_total = dif if not self.journal_id.currency_id.id  else ((dif / self.exchange_type) if self.exchange_type!= 0 else 0)

	@api.one
	def get_unbalance_ammount(self):
		diferencia = 0
		if len(self.invoice_ids)>0:
			diferencia =reduce(lambda x,y: x+y,self.invoice_ids.mapped('amount_sol'))
		dif = float(self.ammount_total if not self.journal_id.currency_id.id else "%.2f"%(self.ammount_total*self.exchange_type) ) - diferencia
		self.unbalance_ammount =dif if not self.journal_id.currency_id.id  else ((dif / self.exchange_type) if self.exchange_type!= 0 else 0)


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
		if self.type_invoices == 'payable':

			move_id = False

			data_cabe = {
				'journal_id':self.journal_id.id,
				'date':self.payment_date,
			}
			move_id = self.env['account.move'].create(data_cabe)

			data_line= {
				'name':self.glosa,
				'partner_id':self.partner_id.id,
				'type_document_it':False,
				'nro_comprobante':self.nro_operation,
				'account_id':self.journal_id.default_debit_account_id.id,
				'currency_id':self.journal_id.currency_id.id,
				'amount_currency': (-self.ammount_total) if self.journal_id.currency_id.id else 0,
				'debit':0,
				'credit':float("%.2f"%(self.ammount_total*self.exchange_type)) if self.journal_id.currency_id.id else self.ammount_total,
				'move_id': move_id.id,
			}
			self.env['account.move.line'].create(data_line)

			dif = float(self.ammount_total if not self.journal_id.currency_id.id else "%.2f"%(self.ammount_total*self.exchange_type) ) - reduce(lambda x,y: x+y,self.invoice_ids.mapped('amount_sol'))
			
			if abs(dif) >= 0.01:
				data_line= {
					'name':self.glosa,
					'partner_id':self.partner_id.id,
					'type_document_it':False,
					'nro_comprobante':self.nro_operation,
					'account_id':self.cuenta_desbalance.id,
					'currency_id':False,
					'amount_currency': False,
					'debit':0 if dif <0  else abs(dif),
					'credit':0 if dif >0  else abs(dif),
					'move_id': move_id.id,
				}
				self.env['account.move.line'].create(data_line)

			for i in self.invoice_ids:
				if i.amount_sol != 0:
					data_lin = {
						'name':self.glosa,
						'partner_id':i.invoice_id.partner_id.id,
						'type_document_it':i.doc_type.id,
						'nro_comprobante':i.invoice_number,
						'account_id':i.account_id.id,
						'currency_id':i.currency_id.id,
						'amount_currency': i.amount_cc if i.currency_id.id else False,
						'debit':abs(i.amount_sol) if i.amount_sol >0 else 0,
						'credit':abs(i.amount_sol) if i.amount_sol <0 else 0,
						'move_id': move_id.id,
					}
					newl= self.env['account.move.line'].create(data_lin)

					conciliar = self.env['account.move.line'].browse([newl.id,i.invoice_id.id])
					conciliar.reconcile()

			self.asiento = move_id.id
		else:
			move_id = False

			data_cabe = {
				'journal_id':self.journal_id.id,
				'date':self.payment_date,
			}
			move_id = self.env['account.move'].create(data_cabe)

			data_line= {
				'name':self.glosa,
				'partner_id':self.partner_id.id,
				'type_document_it':False,
				'nro_comprobante':self.nro_operation,
				'account_id':self.journal_id.default_debit_account_id.id,
				'currency_id':self.journal_id.currency_id.id,
				'amount_currency': (self.ammount_total) if self.journal_id.currency_id.id else False,
				'debit':float("%.2f"%(self.ammount_total*self.exchange_type)) if self.journal_id.currency_id.id else self.ammount_total,
				'credit':0,
				'move_id': move_id.id,
			}
			self.env['account.move.line'].create(data_line)
			dif = float(self.ammount_total if not self.journal_id.currency_id.id else "%.2f"%(self.ammount_total*self.exchange_type) ) - reduce(lambda x,y: x+y,self.invoice_ids.mapped('amount_sol'))
			
			if abs(dif) >= 0.01:
				data_line= {
					'name':self.glosa,
					'partner_id':self.partner_id.id,
					'type_document_it':False,
					'nro_comprobante':self.nro_operation,
					'account_id':self.cuenta_desbalance.id,
					'currency_id':False,
					'amount_currency': False,
					'debit':0 if dif >0  else abs(dif),
					'credit':0 if dif <0  else abs(dif),
					'move_id': move_id.id,
				}
				self.env['account.move.line'].create(data_line)

			for i in self.invoice_ids:
				if i.amount_sol != 0:
					data_lin = {
						'name':self.glosa,
						'partner_id':i.invoice_id.partner_id.id,
						'type_document_it':i.doc_type.id,
						'nro_comprobante':i.invoice_number,
						'account_id':i.account_id.id,
						'currency_id':i.currency_id.id,
						'amount_currency': -i.amount_cc if i.currency_id.id else False,
						'debit':abs(i.amount_sol) if i.amount_sol <0 else 0,
						'credit':abs(i.amount_sol) if i.amount_sol >0 else 0,
						'move_id': move_id.id,
					}
					newl = self.env['account.move.line'].create(data_lin)

					conciliar = self.env['account.move.line'].browse([newl.id,i.invoice_id.id])
					conciliar.reconcile()

			self.asiento = move_id.id

		self.asiento.rendicion_id = self.nro_entra.id
		self.asiento.small_cash_id = self.caja_chica.id
		self.asiento.means_payment_it = self.medio_pago.id
		self.asiento.post()
		self.state = 'done'


class MultipaymentInvoiceLine(models.Model):
	_name = 'multipayment.invoice.line'


	tipo_documento = fields.Many2one('einvoice.catalog.01','Tipo de Documento')
	main_id    = fields.Many2one('multipayment.invoice')
	invoice_id = fields.Many2one('account.move.line','Factura')
	doc_type   = fields.Many2one(related='invoice_id.type_document_it',readonly=True)
	partner_rel = fields.Many2one(related='invoice_id.partner_id',readonly=True)
	currency_id = fields.Many2one(related='invoice_id.currency_id',string='Moneda',readonly=True)	
	invoice_number = fields.Char(related='invoice_id.nro_comprobante',readonly=True)
	rest = fields.Float(string='Saldo MN',compute='_get_rest')
	rest_ext  = fields.Float('Saldo ME',digits=(12,2),compute="_get_rest_ext")


	rest_saldo_mo = fields.Float('Saldo',digits=(12,2),compute="_get_saldo_mo")
	rest_historico = fields.Float(string='Saldo')

	amount_cc = fields.Float('Monto Pago',digits=(12,2))
	amount_ci = fields.Float('Monto M. caja',digits=(12,2),compute="_get_amount_ci")
	amount_sol = fields.Float('MM N', compute="_get_amount_sol", digits=(12,2))


	account_id = fields.Many2one(related='invoice_id.account_id',readonly=True)
	account_code = fields.Char(related='invoice_id.account_id.code',readonly=True)
	moneda_visible= fields.Many2one('res.currency','Moneda',compute="get_moneda")


	@api.one
	def _get_saldo_mo(self):
		print self.currency_id.name
		print self.rest_ext
		print self.rest
		self.rest_saldo_mo = self.rest_ext if self.currency_id.name == 'USD'  else self.rest


	@api.one
	def get_moneda(self):
		self.moneda_visible = self.currency_id.id if self.currency_id.id else ( self.env['res.currency'].search([('name','=','PEN')])[0].id )


	@api.model
	def create(self,vals):
		t = super(MultipaymentInvoiceLine,self).create(vals)
		t.write({'rest_historico':t.rest_saldo_mo})
		return t


	@api.one
	def write(self,vals):
		t = super(MultipaymentInvoiceLine,self).write(vals)

		if 'never' in self.env.context:
			pass
		else:
			if 'invoice_id' in vals:				
				self.with_context({'never':'1'}).write({'rest_historico':self.rest_saldo_mo})
		return t


	@api.onchange('invoice_id')
	@api.depends('invoice_id')
	def onchange_invoice_idmonto(self):
		self.rest_historico = self.rest_saldo_mo

	@api.depends('currency_id','currency_id')
	def _get_amount_sol(self):
		for rec in self:
			if not rec.main_id.journal_id.currency_id.id:				
				rec.amount_sol = float("%.2f"%rec.amount_ci)
			else:
				rec.amount_sol = float("%.2f"%(rec.amount_ci * rec.main_id.exchange_type)) 


	#@api.onchange('amount_cc')
	#def _onchange_amount_cc(self):
	#	if not self.currency_id.id:
	#		if self.amount_cc > self.rest:
	#			raise UserError('La cantidad ingresada debe ser inferior o igual al saldo: '+(self.currency_id.symbol if self.currency_id.id else 'S/.')+str(self.rest))
	#	else:
	#		if self.amount_cc > self.rest_ext:
	#			raise UserError('La cantidad ingresada debe ser inferior o igual al saldo en Moneda Extranjera: '+(self.currency_id.symbol if self.currency_id.id else 'S/.')+str(self.rest_ext))

	@api.depends('currency_id','invoice_id')
	def _get_rest_ext(self):
		for rec in self:
			rec.rest_ext = rec.invoice_id.amount_residual_currency

			if rec.main_id.type_invoices == 'payable':
				rec.rest_ext = -rec.rest_ext


	@api.depends('currency_id','invoice_id')
	def _get_rest(self):
		for rec in self:
			rec.rest = rec.invoice_id.amount_residual

			if rec.main_id.type_invoices == 'payable':
				rec.rest = -rec.rest

	
	@api.depends('amount_cc','main_id','currency_id')
	def _get_amount_ci(self):
		for rec in self:
			if rec.currency_id.id == rec.main_id.journal_id.currency_id.id:
				rec.amount_ci = rec.amount_cc
			else:
				if rec.main_id.journal_id.currency_id.id:
					rec.amount_ci = (rec.amount_cc / rec.main_id.exchange_type) if rec.main_id.exchange_type != 0 else 0
				else:
					rec.amount_ci = rec.amount_cc * rec.main_id.exchange_type



	#@api.constrains('amount_cc')
	#def _verify_amount_cc(self):
	#	if not self.currency_id.id:
	#		if self.amount_cc > self.rest or self.amount_cc <= 0:
	#			raise UserError('La cantidad ingresada en la factura "'+self.invoice_number+u'" es inválida')
	#	else:
	#		if self.amount_cc > self.rest_ext or self.amount_cc <= 0:
	#			raise UserError('La cantidad ingresada en la factura "'+self.invoice_number+u'" es inválida')
	