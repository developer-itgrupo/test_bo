# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError

from odoo.osv import expression

class account_move(models.Model):
	_inherit = 'account.move'

	means_payment_it = fields.Many2one('einvoice.means.payment','Medio de Pago')
	fecha_contable = fields.Date('Fecha Contable')

	fecha_modify_ple = fields.Date('Fecha para PLE Diario')
	ple_diariomayor = fields.Selection([('1','FECHA DEL COMPROBANTE CORRESPONDE AL PERIODO'),('8', 'CORRESPONDE A UN PERIODO ANTERIOR Y NO HA SIDO ANOTADO EN DICHO PERIODO'), ('9', 'CORRESPONDE A UN PERIODO ANTERIOR Y SI HA SIDO ANOTADO EN DICHO PERIODO')], 'PLE Diario y Mayor',default="1" )

	fecha_modify_ple_compra = fields.Date('Fecha para PLE Compra')
	ple_compra = fields.Selection([('0', 'ANOTACION OPTATIVAS SIN EFECTO EN EL IGV'), ('1', 'FECHA DEL DOCUMENTO CORRESPONDE AL PERIODO EN QUE SE ANOTO'), ('6', 'FECHA DE EMISION ES ANTERIOR AL PERIODO DE ANOTACION, DENTRO DE LOS 12 MESES'), ('7','FECHA DE EMISION ES ANTERIOR AL PERIODO DE ANOTACION, LUEGO DE LOS 12 MESES'),('9','ES AJUSTE O RECTIFICACION')], 'PLE Compras',default="1")

	fecha_modify_ple_venta = fields.Date('Fecha para PLE Venta')
	ple_venta = fields.Selection([('0', 'ANOTACION OPTATIVA SIN EFECTO EN EL IGV'), ('1', 'FECHA DEL COMPROBANTE CORRESPONDE AL PERIODO'), ('2', 'DOCUMENTO ANULADO'), ('8', 'CORRESPONDE A UN PERIODO ANTERIOR'), ('9', 'SE ESTA CORRIGIENDO UNA ANOTACION DEL PERIODO ANTERIOR')], 'PLE Ventas',default="1")
	
			
	fecha_special = fields.Boolean('Apertura/Cierre',default=False)	
				

	rendicion_id = fields.Many2one('account.rendicion.it','Rendicion',compute="get_rendicion_id",inverse="set_rendicion_id",store=True)
	check_rendicion_rel = fields.Boolean('Check',related='journal_id.check_rendicion')

	es_editable = fields.Boolean('Es editable',related='journal_id.editar_nombre_asiento')

	@api.one
	def post(self):
		invoice = self._context.get('invoice', False)
		if self.name == '/':
			journal = self.journal_id

			if invoice and invoice.move_name and invoice.move_name != '/':
				pass
			else:
				if journal.sequence_id:
					# If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
					sequence = journal.sequence_id
					if invoice and invoice.type in ['out_refund', 'in_refund'] and journal.refund_sequence:
						if not journal.refund_sequence_id:
							raise UserError( ('Falta definir una secuencia de Rectificaciones'))
						sequence = journal.refund_sequence_id
														
					flag = True
					for i in sequence.date_range_ids:
						if i.date_from<= self.date and i.date_to >= self.date:
							flag = False

					if flag:
						pass
						#raise UserError( ('NO HAY SECUENCIA GENERADA PARA  LA FECHA CONTABLE INGRESADA,  DEBE IR AL MENU  CONTABILIDAD/CONFIGURACION/CONTABILIDAD/GENERAR SECUENCIAS, ELEGIR EL PERIODO FISCAL, LUEGO EL DIARIO Y A CONTINUACION DARLE CLICK EN EL BOTON MOSTRAR.'))
				else:
					pass
					#raise UserError( ('Falta definir una secuencia de Diario.'))


		t = super(account_move,self).post()
		return t

	@api.one
	def set_rendicion_id(self):

		param = self.env['main.parameter'].search([])[0]
		for i in self.line_ids:
			if i.account_id.id in (param.deliver_account_me.id,param.deliver_account_mn.id):
				i.rendicion_id = self.rendicion_id.id

	@api.one
	def get_rendicion_id(self):
		t = False
		for i in self.line_ids:
			if i.rendicion_id.id:
				t = i.rendicion_id.id
		self.rendicion_id = t


	@api.onchange('date')
	def onchange_date(self):
		self.fecha_contable = self.date


	@api.model
	def create(self,vals):

		t = super(account_move,self).create(vals)

		if not t.fecha_contable:
			t.fecha_contable = t.date

		if t.journal_id.asentar_automatic:
			#t.post()
			pass
		t.write({'rendicion_id':t.rendicion_id.id})
		return t

	@api.one
	def change_name(self):
		self.name = '/'

	@api.multi
	def assert_balanced(self):
		for i in self:
			if i.state == 'draft':
				pass
			else:
				super(account_move,i).assert_balanced()
				

	@api.one
	def write(self,vals):
		rendicion = self.rendicion_id.id
		if 'rendicion_id' in vals:
			rendicion = vals['rendicion_id']
		vals['rendicion_id'] = rendicion
		t = super(account_move,self).write(vals)
		self.refresh()
		self.assert_balanced()
		self.env.cr.execute('UPDATE account_invoice SET move_name=%s WHERE move_id=%s',
					   (self.name, self.id))

		self.env.cr.execute("""UPDATE account_payment SET move_name=%s WHERE id in (
							select distinct ap.id from account_payment ap
inner join account_move_line aml on aml.payment_id = ap.id
inner join account_move am on am.id = aml.move_id
where am.id = %s)""",  (self.name, self.id))

		return t

class account_move_line(models.Model):
	_inherit = 'account.move.line'

	tax_amount = fields.Float('Importe impuestos/base',digits=(12,2))

	nro_comprobante = fields.Char('Nro. Comprobante')
	type_document_it = fields.Many2one('einvoice.catalog.01','Tipo de Documento')
	sequence = fields.Integer(help='Used to order Journals in the dashboard view', default=10)
	rendicion_id = fields.Many2one('account.rendicion.it','Rendicion')
	cuo_ple = fields.Char('CUO PLE')
	invoice_line_id = fields.Many2one('account.invoice.line','Linea Factura',copy=False)


	tc = fields.Float('T.C.',digits=(12,3))

	@api.multi
	def prepare_move_lines_for_reconciliation_widget(self, target_currency=False, target_date=False):
		""" Returns move lines formatted for the manual/bank reconciliation widget

			:param target_currency: currency (browse_record or ID) you want the move line debit/credit converted into
			:param target_date: date to use for the monetary conversion
		"""
		t = super(account_move_line,self).prepare_move_lines_for_reconciliation_widget(target_currency,target_date)
		for i in range(len(t)):
			lineas = self.env['account.move.line'].browse(t[i]['id'])
			t[i]['nro_comprobante']= lineas.nro_comprobante
			t[i]['type_document_it']= lineas.type_document_it.code
		return t

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|', ('name', '=ilike', '%' + name + '%'), ('nro_comprobante', '=ilike', '%' + name + '%')]
			if operator in expression.NEGATIVE_TERM_OPERATORS:
				domain = ['&', '!'] + domain[1:]
		accounts = self.search(domain + args, limit=limit)
		return accounts.name_get()

	@api.multi
	@api.depends('ref','move_id')
	def name_get(self):
		result = []
		for table in self:
			l_name =  table.nro_comprobante if table.nro_comprobante else (self.name if self.name else '/')
			result.append((table.id, l_name ))
		return result



		
class account_chart_template(models.Model):
	_inherit = 'account.chart.template'

	code_sunat = fields.Char('Codigo Sunat',size=10)






class product_product(models.Model):
	_inherit = "product.product"

	@api.model
	def _convert_prepared_anglosaxon_line(self, line, partner):
		t = super(product_product,self)._convert_prepared_anglosaxon_line(line,partner)
		linea = line.get('invl_id',False)
		t['invoice_line_id'] = linea
		if linea:
			inv_id = self.env['account.invoice.line'].browse(linea)
		return t





class account_journal(models.Model):
	_inherit = 'account.journal'

	editar_nombre_asiento = fields.Boolean('Editar Asiento')



class AccountPartialReconcile(models.Model):
	_inherit = 'account.partial.reconcile'

	def create_exchange_rate_entry(self, aml_to_fix, amount_diff, diff_in_currency, currency, move_date):
		""" Automatically create a journal entry to book the exchange rate difference.
			That new journal entry is made in the company `currency_exchange_journal_id` and one of its journal
			items is matched with the other lines to balance the full reconciliation.
		"""
		for rec in self:
			if not rec.company_id.currency_exchange_journal_id:
				raise UserError(_("You should configure the 'Exchange Rate Journal' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
			if not rec.company_id.income_currency_exchange_account_id.id:
				raise UserError(_("You should configure the 'Gain Exchange Rate Account' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
			if not rec.company_id.expense_currency_exchange_account_id.id:
				raise UserError(_("You should configure the 'Loss Exchange Rate Account' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
			move_vals = {'journal_id': rec.company_id.currency_exchange_journal_id.id}

			# The move date should be the maximum date between payment and invoice (in case
			# of payment in advance). However, we should make sure the move date is not
			# recorded after the end of year closing.
			if move_date > rec.company_id.fiscalyear_lock_date:
				move_vals['date'] = move_date
			move = rec.env['account.move'].create(move_vals)
			amount_diff = rec.company_id.currency_id.round(amount_diff)
			diff_in_currency = currency.round(diff_in_currency)
			line_to_reconcile = rec.env['account.move.line'].with_context(check_move_validity=False).create({
				'name': _('Currency exchange rate difference'),
				'debit': amount_diff < 0 and -amount_diff or 0.0,
				'credit': amount_diff > 0 and amount_diff or 0.0,
				'account_id': rec.debit_move_id.account_id.id,
				'move_id': move.id,
				'currency_id': currency.id,
				'amount_currency': -diff_in_currency,
				'partner_id': rec.debit_move_id.partner_id.id,
				'type_document_it': rec.debit_move_id.type_document_it.id,
				'nro_comprobante': rec.debit_move_id.nro_comprobante,
			})
			rec.env['account.move.line'].create({
				'name': _('Currency exchange rate difference'),
				'debit': amount_diff > 0 and amount_diff or 0.0,
				'credit': amount_diff < 0 and -amount_diff or 0.0,
				'account_id': amount_diff > 0 and rec.company_id.currency_exchange_journal_id.default_debit_account_id.id or rec.company_id.currency_exchange_journal_id.default_credit_account_id.id,
				'move_id': move.id,
				'currency_id': currency.id,
				'amount_currency': diff_in_currency,
				'partner_id': rec.debit_move_id.partner_id.id,
				'type_document_it': rec.debit_move_id.type_document_it.id,
				'nro_comprobante': rec.debit_move_id.nro_comprobante,
			})
			for aml in aml_to_fix:
				partial_rec = rec.env['account.partial.reconcile'].create({
					'debit_move_id': aml.credit and line_to_reconcile.id or aml.id,
					'credit_move_id': aml.debit and line_to_reconcile.id or aml.id,
					'amount': abs(aml.amount_residual),
					'amount_currency': abs(aml.amount_residual_currency),
					'currency_id': currency.id,
				})
			move.post()
		return line_to_reconcile, partial_rec

	# Do not forwardport in master as of 2017-07-20
	def _fix_multiple_exchange_rates_diff(self, amls_to_fix, amount_diff, diff_in_currency, currency, move):
		self.ensure_one()
		move_lines = self.env['account.move.line'].with_context(check_move_validity=False)
		partial_reconciles = self.with_context(skip_full_reconcile_check=True)
		amount_diff = self.company_id.currency_id.round(amount_diff)
		diff_in_currency = currency.round(diff_in_currency)

		for aml in amls_to_fix:
			account_payable_line = move_lines.create({
				'name': _('Currency exchange rate difference'),
				'debit': amount_diff < 0 and -aml.amount_residual or 0.0,
				'credit': amount_diff > 0 and aml.amount_residual or 0.0,
				'account_id': self.debit_move_id.account_id.id,
				'move_id': move.id,
				'currency_id': currency.id,
				'amount_currency': -aml.amount_residual_currency,
				'partner_id': self.debit_move_id.partner_id.id,
				'type_document_it': self.debit_move_id.type_document_it.id,
				'nro_comprobante': self.debit_move_id.nro_comprobante,
			})

			move_lines.create({
				'name': _('Currency exchange rate difference'),
				'debit': amount_diff > 0 and aml.amount_residual or 0.0,
				'credit': amount_diff < 0 and -aml.amount_residual or 0.0,
				'account_id': amount_diff > 0 and self.company_id.currency_exchange_journal_id.default_debit_account_id.id or self.company_id.currency_exchange_journal_id.default_credit_account_id.id,
				'move_id': move.id,
				'currency_id': currency.id,
				'amount_currency': aml.amount_residual_currency,
				'type_document_it': self.debit_move_id.type_document_it.id,
				'nro_comprobante': self.debit_move_id.nro_comprobante,
				'partner_id': self.debit_move_id.partner_id.id})

			partial_rec = super(AccountPartialReconcile, partial_reconciles).create({
					'debit_move_id': aml.credit and account_payable_line.id or aml.id,
					'credit_move_id': aml.debit and account_payable_line.id or aml.id,
					'amount': abs(aml.amount_residual),
					'amount_currency': abs(aml.amount_residual_currency),
					'currency_id': currency.id,
			})

			move_lines |= account_payable_line
			partial_reconciles |= partial_rec

		partial_reconciles._compute_partial_lines()
		return move_lines, partial_reconciles
