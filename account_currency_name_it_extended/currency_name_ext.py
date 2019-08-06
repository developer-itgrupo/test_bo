#-*- coding: utf-8 -*-

from odoo import models, fields, api
import dateutil.parser

class Currency_name_extended(models.Model):
	_inherit = 'account_currency_name_it.currency_name'

	account_debit_id = fields.Many2one('account.account','Cuenta a Pagar')
	account_credit_id = fields.Many2one('account.account', 'Cuenta a Cobrar')

class account_invoice(models.Model):
	_inherit = 'account.invoice'

	@api.onchange('partner_id', 'company_id')
	def _onchange_partner_id(self):
		t = super(account_invoice,self)._onchange_partner_id()
		m = self.env['account_currency_name_it.currency_name'].search([('currency_id','=',self.currency_id.id)])
		if len(m) >0:
			if self.type in ('in_invoice','in_refund') and m[0].account_debit_id.id:
				self.account_id = m[0].account_debit_id.id

			elif self.type in ('out_invoice','out_refund') and m[0].account_credit_id.id:
				self.account_id = m[0].account_credit_id.id
		return t

	@api.depends('partner_id')
	@api.onchange('currency_id')
	def onchange_currency_id(self):
		m = self.env['account_currency_name_it.currency_name'].search([('currency_id','=',self.currency_id.id)])
		if len(m) >0:
			if self.type in ('in_invoice','in_refund') and m[0].account_debit_id.id:
				self.account_id = m[0].account_debit_id.id

			elif self.type in ('out_invoice','out_refund') and m[0].account_credit_id.id:
				self.account_id = m[0].account_credit_id.id

	@api.onchange('it_type_document')
	def update_account(self):
		self.onchange_currency_id()