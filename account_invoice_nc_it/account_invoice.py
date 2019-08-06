# -*- coding: utf-8 -*-

import json
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

from odoo.exceptions import UserError, RedirectWarning, ValidationError

import odoo.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)

TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale',
    'in_refund': 'purchase',
}

# mapping invoice type to refund type
TYPE2REFUND = {
    'out_invoice': 'out_refund',        # Customer Invoice
    'in_invoice': 'in_refund',          # Vendor Bill
    'out_refund': 'out_invoice',        # Customer Refund
    'in_refund': 'in_invoice',          # Vendor Refund
}

MAGIC_COLUMNS = ('id', 'create_uid', 'create_date', 'write_uid', 'write_date')

class main_parameter(models.Model):
	_inherit = 'main.parameter'
	type_document_id = fields.Many2one('einvoice.catalog.01', string='Tipo de documento')

class account_perception(models.Model):
	_inherit = 'account.perception'

	@api.onchange('comprobante','tipo_doc')
	def _changed_comprobante(self):
		if self.comprobante:
			self.comprobante = str(self.comprobante).replace(' ', '')

			if self.comprobante and self.tipo_doc.id:
				self.comprobante = str(self.comprobante).replace(' ', '')
				t = self.comprobante.split('-')
				n_serie = 0
				n_documento = 0
				self.env.cr.execute(
					"select coalesce(n_serie,0), coalesce(n_documento,0) from einvoice_catalog_01 where id = " + str(
						self.tipo_doc.id))

				forelemn = self.env.cr.fetchall()
				for ielem in forelemn:
					n_serie = ielem[0]
					n_documento = ielem[1]
				if len(t) == 2:
					parte1 = t[0]
					if len(t[0]) < n_serie:
						for i in range(0, n_serie - len(t[0])):
							parte1 = '0' + parte1
					parte2 = t[1]
					if len(t[1]) < n_documento:
						for i in range(0, n_documento - len(t[1])):
							parte2 = '0' + parte2
					self.comprobante = parte1 + '-' + parte2
				elif len(t) == 1:
					parte2 = t[0]
					if len(t[0]) < n_documento:
						for i in range(0, n_documento - len(t[0])):
							parte2 = '0' + parte2
					self.comprobante = parte2
				else:
					pass

class account_invoice(models.Model):
	_inherit = 'account.invoice'
	is_nota_credito = fields.Boolean('Es Nota credito Nacional', compute='calc_is_nota_credito')

	@api.one
	def calc_is_nota_credito(self):
		self.is_nota_credito = False
		parametro = self.env['main.parameter'].search([], limit=1)
		if parametro and parametro.type_document_id and self.it_type_document.id==parametro.type_document_id.id and self.state == 'open':
			self.is_nota_credito = True

	@api.model
	def _prepare_refund2(self, invoice, date_invoice=None, date=None, description=None, journal_id=None,it_type_document=None,reference=None):
		values = {}
		for field in ['name', 'reference', 'comment', 'date_due', 'partner_id', 'company_id', 'team_id',
					  'account_id', 'currency_id', 'payment_term_id', 'user_id', 'fiscal_position_id']:
			if invoice._fields[field].type == 'many2one':
				values[field] = invoice[field].id
			else:
				values[field] = invoice[field] or False

		values['invoice_line_ids'] = self._refund_cleanup_lines(invoice.invoice_line_ids)

		tax_lines = invoice.tax_line_ids
		values['tax_line_ids'] = self._refund_cleanup_lines(tax_lines)

		if journal_id:
			journal = self.env['account.journal'].browse(journal_id)
		elif invoice['type'] == 'in_invoice':
			journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
		else:
			journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
		values['journal_id'] = journal.id

		values['type'] = TYPE2REFUND[invoice['type']]
		values['date_invoice'] = date_invoice or fields.Date.context_today(invoice)
		values['state'] = 'draft'
		values['number'] = False
		values['origin'] = invoice.number
		values['refund_invoice_id'] = invoice.id

		if date:
			values['date'] = date
		if description:
			values['name'] = description
		if it_type_document:
			values['it_type_document'] = it_type_document
		if reference:
			values['reference'] = reference

		related_documents = []
		val = {}
		val['tipo_doc'] = self.it_type_document.id   #einvoice.catalog.01
		val['comprobante'] = self.reference
		val['fecha'] = self.date_invoice
		val['igv'] = self.amount_tax
		val['base_imponible'] = self.amount_untaxed
		val['perception'] = self.amount_total
		related_documents.append((0, 0, val))
		values['account_ids'] = related_documents

		return values


	def refund2(self, date_invoice=None, date=None, description=None, journal_id=None,it_type_document=None,reference=None):
		new_invoices = self.browse()
		for invoice in self:
			# create the new invoice
			values = self._prepare_refund2(invoice, date_invoice=date_invoice, date=date,
										  description=description, journal_id=journal_id, it_type_document=it_type_document,
										  reference=reference)
			refund_invoice = self.create(values)
			invoice_type = {'out_invoice': ('customer invoices refund'),
							'in_invoice': ('vendor bill refund')}
			message = _("This %s has been created from: <a href=# data-oe-model=account.invoice data-oe-id=%d>%s</a>") % (invoice_type[invoice.type], invoice.id, invoice.number)
			refund_invoice.message_post(body=message)
			new_invoices += refund_invoice
		return new_invoices

	@api.multi
	def genera_asiento_nota_credito(self):
		if self.it_type_document.id and self.is_nota_credito != True:			
			raise UserError('No es una nota de Credito.')

		# self.env['einvoice.catalog.01'].search([('code', '=', '08')], limit=1)
		parametro = self.env['main.parameter'].search([], limit=1)
		if not self.move_id or self.it_type_document.id != parametro.type_document_id.id:
			return
		asiento_id = self.account_id
		linea_fact = False
		for asiento in self.move_id.line_ids:
			if asiento.account_id.user_type_id.type == 'receivable' or  asiento.account_id.user_type_id.type == 'payable':
				#linea_fact = asiento
				self.env.cr.execute('delete from account_move_line where id ='+ str(asiento.id))

		company_id = self._context.get('company_id', self.env.user.company_id.id)

		for doc_ref in self.account_ids:
			amount_residual = doc_ref.perception
			debit = doc_ref.perception
			credit = 0
			if self.type == 'out_refund':
				amount_residual = -doc_ref.perception
				debit = 0
				credit = doc_ref.perception

			if self.currency_id.name == 'PEN':
				#if linea_fact and linea_fact.id:
				#	linea_fact.nro_comprobante =  doc_ref.comprobante
				#	linea_fact.type_document_it = doc_ref.tipo_doc.id
				insert ="""INSERT INTO account_move_line (journal_id,date_maturity, partner_id, company_id, debit,ref,
	            account_id,debit_cash_basis,reconciled,balance_cash_basis,date,move_id,company_currency_id,name,invoice_id,balance,quantity,type_document_it,nro_comprobante,
	            create_date,blocked,create_uid,credit_cash_basis,amount_residual_currency,write_date,write_uid,credit,amount_currency,sequence,amount_residual) """
				values = """VALUES("""+str(self.journal_id.id)+""",
				'"""+str(self.date_due)+"""',
				"""+str(self.partner_id.id)+""",
				"""+str(company_id)+""",
				"""+str("%.2f"%debit)+""",
				'"""+str(doc_ref.comprobante)+"""',
				"""+str(asiento_id.id)+""",
				"""+str("%.2f"%debit)+""",
				"""+str(False)+""",
				"""+str("%.2f"%debit)+""",
				'"""+str(self.date_invoice)+"""',
				"""+str(self.move_id.id)+""",
				"""+str(self.env.user.company_id.currency_id.id)+""",
				'Nota de Credito: """+str(self.reference)+"""',
				"""+str(self.id)+""",
				"""+str("%.2f"%amount_residual)+""",1,
				"""+str(doc_ref.tipo_doc.id)+""",
				'"""+str(doc_ref.comprobante)+"""',
				'"""+str(datetime.today())+"""',
				"""+str(False)+""",
				"""+str(self.env.user.id)+""",
				"""+str(0)+""",
				"""+str(0)+""",
				'"""+str(datetime.today())+"""',
				"""+str(self.env.user.id)+""",
				"""+str("%.2f"%credit)+""",
				"""+str(0)+""",
				"""+str(10)+""",
				"""+str("%.2f"%amount_residual)+"""
				)"""
				self.env.cr.execute(insert + values)
			else:


				#if linea_fact and linea_fact.id:
				#	linea_fact.nro_comprobante =  doc_ref.comprobante
				#	linea_fact.type_document_it = doc_ref.tipo_doc.id
				insert ="""INSERT INTO account_move_line (journal_id,date_maturity, partner_id, company_id, debit,ref,
	            account_id,debit_cash_basis,reconciled,balance_cash_basis,date,move_id,company_currency_id,name,invoice_id,balance,quantity,type_document_it,nro_comprobante,
	            create_date,blocked,create_uid,credit_cash_basis,amount_residual_currency,write_date,write_uid,credit,amount_currency,sequence,amount_residual,currency_id,tc) """
				values = """VALUES("""+str(self.journal_id.id)+""",
				'"""+str(self.date_due)+"""',
				"""+str(self.partner_id.id)+""",
				"""+str(company_id)+""",
				"""+str("%.2f"%(debit*self.currency_rate_auto))+""",
				'"""+str(doc_ref.comprobante)+"""',
				"""+str(asiento_id.id)+""",
				"""+str("%.2f"%(debit*self.currency_rate_auto))+""",
				"""+str(False)+""",
				"""+str("%.2f"%(debit*self.currency_rate_auto))+""",
				'"""+str(self.date_invoice)+"""',
				"""+str(self.move_id.id)+""",
				"""+str(self.env.user.company_id.currency_id.id)+""",
				'Nota de Credito: """+str(self.reference)+"""',
				"""+str(self.id)+""",
				"""+str("%.2f"%(amount_residual*self.currency_rate_auto))+""",1,
				"""+str(doc_ref.tipo_doc.id)+""",
				'"""+str(doc_ref.comprobante)+"""',
				'"""+str(datetime.today())+"""',
				"""+str(False)+""",
				"""+str(self.env.user.id)+""",
				"""+str(0)+""",
				"""+str("%.2f"%(amount_residual))+""",
				'"""+str(datetime.today())+"""',
				"""+str(self.env.user.id)+""",
				"""+str("%.2f"%(credit*self.currency_rate_auto))+""",
				"""+str("%.2f"%(debit-credit))+""",
				"""+str(10)+""",
				"""+str("%.2f"%(amount_residual*self.currency_rate_auto))+""",
				"""+str(self.currency_id.id)+""",
				"""+str(self.currency_rate_auto)+"""
				)"""
				self.env.cr.execute(insert + values)

		self.env.cr.execute("""

			select sum(aml.debit-aml.credit) as saldo, am.id 
			from account_move am
			inner join account_move_line aml on aml.move_id = am.id
			where am.id = """ +str(self.move_id.id)+ """
			group by am.id
			""")

		verif = self.env.cr.fetchall()[0]
		if verif[0] != 0:
			raise UserError('El asiento a generar se encuentra descuadrado.')

		contextn = dict(self._context or {})
		contextn['message']="Generado Exitosamente"
		return {
				'name':'Finalizado',
				'type':'ir.actions.act_window',
				'view_type':'form',
				'view_mode':'form',
				'res_model':'sh.message.wizard',
				'views': [(False,'form')],
				'target':'new',
				'context':contextn,
		}