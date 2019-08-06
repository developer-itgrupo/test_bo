# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
import base64
import sys
from odoo.exceptions import UserError
import pprint
from odoo.exceptions import ValidationError

#FUNCION ONCHANGE DE LA FECHA DE EMISION DE LA FACTURA
#SI ESTA VA VACIO SE ACTUALIZA CON FECHA DE EMISION O FECHA ACTUAL
class AccountInvoice(models.Model):
	_inherit = "account.invoice"
	prueba = fields.Char("prueba")

	@api.onchange('payment_term_id', 'date_invoice')
	def _onchange_payment_term_date_invoice(self):
		date_invoice = self.date_invoice
		date_due = self.date_due
		if not date_invoice:
			date_invoice = fields.Date.context_today(self)
			if not date_due:
				date_due = fields.Date.context_today(self)	
		elif not self.payment_term_id.id:
			self.fecha_perception = date_invoice
			if self.partner_id.id:
				if self.type == 'out_invoice':
					if self.partner_id.property_payment_term_id.id:
						self.payment_term_id = self.partner_id.property_payment_term_id.id
					else:
						self.payment_term_id = 1
				if  self.type == 'in_invoice':
					if self.partner_id.property_supplier_payment_term_id.id:
						self.payment_term_id = self.partner_id.property_supplier_payment_term_id.id
					else:
						self.payment_term_id = 1
					# pay_days = 0
					# if self.partner_id.property_supplier_payment_term_id.id ==2:
					#	 pay_days = 15
					#	 pass
					# elif self.partner_id.property_supplier_payment_term_id.id ==3:
					#	 pay_days = 30
					#	 pass
					# from datetime import date, timedelta, datetime
					# dat_t = datetime.strptime(date_invoice, '%Y-%m-%d')
					# date_pay = dat_t+timedelta(days=pay_days)
					# date_pay_str=date_pay.strftime('%Y-%m-%d')
					# #import pdb; pdb.set_trace()
					# self.date_due = date_pay_str

		if not self.payment_term_id:
			# When no payment term defined
			self.date_due = date_due
			if not self.date_due:
				self.date_due = date_invoice
		else:
			pterm = self.payment_term_id
			pterm_list = pterm.with_context(currency_id=self.company_id.currency_id.id).compute(value=1, date_ref=date_invoice)[0]
			self.date_due = max(line[0] for line in pterm_list)


	# CREACION DE LOS ASIENTOS CONTABLES, SE MODIFICO PARA 
	# QUE JALE LA FECHA DE FENCIMIENTO DE LA FACTURA A LA FECHA DE FENCIMIENTO
	# DE LOS APUNTES CONTABLES
	@api.multi
	def action_move_create(self):
		""" Creates invoice related analytics and financial move lines """
		account_move = self.env['account.move']
		for inv in self:
			if not inv.journal_id.sequence_id:
				raise UserError(_('Please define sequence on the journal related to this invoice.'))
			if not inv.invoice_line_ids:
				raise UserError(_('Please create some invoice lines.'))
			if inv.move_id:
				continue

			ctx = dict(self._context, lang=inv.partner_id.lang)

			if not inv.date_invoice:
				inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
			company_currency = inv.company_id.currency_id

			# create move lines (one per invoice line + eventual taxes and analytic lines)
			iml = inv.invoice_line_move_line_get()
			iml += inv.tax_line_move_line_get()

			diff_currency = inv.currency_id != company_currency
			# create one move line for the total and possibly adjust the other lines amount
			total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)

			name = inv.name or '/'
			if inv.payment_term_id:
				totlines = inv.with_context(ctx).payment_term_id.with_context(currency_id=company_currency.id).compute(total, inv.date_invoice)[0]
				res_amount_currency = total_currency
				ctx['date'] = inv._get_currency_rate_date()
				for i, t in enumerate(totlines):
					if inv.currency_id != company_currency:
						amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
					else:
						amount_currency = False

					# last line: add the diff
					res_amount_currency -= amount_currency or 0
					if i + 1 == len(totlines):
						amount_currency += res_amount_currency

					iml.append({
						'type': 'dest',
						'name': name,
						'price': t[1],
						'account_id': inv.account_id.id,
						'date_maturity': inv.date_due,
						'amount_currency': diff_currency and amount_currency,
						'currency_id': diff_currency and inv.currency_id.id,
						'invoice_id': inv.id
					})
			else:
				iml.append({
					'type': 'dest',
					'name': name,
					'price': total,
					'account_id': inv.account_id.id,
					'date_maturity': inv.date_due,
					'amount_currency': diff_currency and total_currency,
					'currency_id': diff_currency and inv.currency_id.id,
					'invoice_id': inv.id
				})
			part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
			line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
			line = inv.group_lines(iml, line)

			journal = inv.journal_id.with_context(ctx)
			line = inv.finalize_invoice_move_lines(line)

			date = inv.date or inv.date_invoice
			move_vals = {
				'ref': inv.reference,
				'line_ids': line,
				'journal_id': journal.id,
				'date': date,
				'narration': inv.comment,
			}
			ctx['company_id'] = inv.company_id.id
			ctx['invoice'] = inv
			ctx_nolang = ctx.copy()
			ctx_nolang.pop('lang', None)
			move = account_move.with_context(ctx_nolang).create(move_vals)
			# Pass invoice in context in method post: used if you want to get the same
			# account move reference when creating the same invoice after a cancelled one:
			move.post()
			# make the invoice point to that move
			vals = {
				'move_id': move.id,
				'date': date,
				'move_name': move.name,
			}
			inv.with_context(ctx).write(vals)
		return True

	#FUNCION DE MODULO ACCOUNT QUE LLAMA AL ONCHANGE DE FECHA DE EMISION AL APRETAR EL BOTON VALIDAR 
	@api.multi
	def action_date_assign(self):
		pass