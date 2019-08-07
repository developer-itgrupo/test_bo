# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import json
from odoo.tools import float_is_zero, float_compare


class account_invoice(models.Model):
	_inherit = 'account.invoice'

	def _check_invoice_reference(self):
		for invoice in self:
			#refuse to validate a vendor bill/refund if there already exists one with the same reference for the same partner,
			#because it's probably a double encoding of the same bill/refund
			if invoice.type in ('in_invoice', 'in_refund') and invoice.reference:
				if self.search([('type','=',invoice.type),('it_type_document','=',invoice.it_type_document.id),('type', '=', invoice.type), ('reference', '=', invoice.reference),('state','not in',('draft','cancel')),('company_id', '=', invoice.company_id.id), ('partner_id', '=', invoice.partner_id.id), ('id', '!=', invoice.id)]):
					raise UserError(_("Duplicated vendor reference detected. You probably encoded twice the same vendor bill/refund."))
			if invoice.type in ('out_invoice', 'out_refund') and invoice.reference:
				if self.search([('type','=',invoice.type),('it_type_document','=',invoice.it_type_document.id), ('reference', '=', invoice.reference),('state','not in',('draft','cancel')),('company_id', '=', invoice.company_id.id), ('id', '!=', invoice.id)]):
					raise UserError(_("Detectada una referencia duplicada. Probablemente haya codificado dos veces la misma factura/rectificativa."))


	@api.one
	def renumber(self):
		self.move_name = False

	@api.one
	def write(self,vals):
		if self.type == 'in_invoice' or self.type == 'in_refund':
			if self.fecha_perception:
				pass
			else:
				if self.date_invoice:
					vals['fecha_perception'] = self.date_invoice
		t = super(account_invoice,self).write(vals)
		self.validacion_dimension()
		return t


	@api.model
	def create(self,vals):
		t = super(account_invoice,self).create(vals)
		t.validacion_dimension()
		return t

	@api.one
	def action_number(self):
		t = super(account_invoice,self).action_number()
		
		if self.type == 'in_invoice' or self.type == 'in_refund':
			
			if self.fecha_perception:
				pass
			else:
				if self.date_invoice:
					self.fecha_perception = self.date_invoice
		return t



	@api.onchange('serie_id')
	def onchange_serie_id(self):
		if self.serie_id:
			next_number = self.serie_id.sequence_id.number_next_actual
			if self.serie_id.sequence_id.prefix == False:
				raise UserError("No existe un prefijo configurado en la secuencia de la serie.")
			prefix = self.serie_id.sequence_id.prefix
			padding = self.serie_id.sequence_id.padding
			self.reference = prefix + "0"*(padding - len(str(next_number))) + str(next_number)
		else:
			self.reference = ""


	@api.multi
	def invoice_validate(self):
		for i in self:
			moneda = i.account_id.currency_id.name if i.account_id.currency_id.id else 'PEN'

			if moneda == i.currency_id.name:
				pass 
			else:
				#raise UserError("La moneda de la factura no coincide con la moneda de la cuenta.")
				pass

			if i.serie_id.id and i.serie_id_internal.id and i.serie_id.id == i.serie_id_internal.id:
				i.number = i.nro_internal
				i.reference = i.nro_internal
			elif i.serie_id.id and i.serie_id_internal.id != i.serie_id.id:
				i.serie_id_internal = i.serie_id.id
				i.nro_internal = i.serie_id.sequence_id.next_by_id()
				i.number = i.nro_internal
				i.reference =i.nro_internal

			i.onchange_suplier_invoice_number_it()
			if  i.serie_id.id or i.reference:
				i.number = i.reference

		t = super(account_invoice,self).invoice_validate()
		for inv in self:
			if inv.move_id.id:
				for elem in inv.move_id.line_ids:
					elem.nro_comprobante = inv.reference 
					elem.type_document_it = inv.it_type_document.id

				if inv.name:
					for elem in inv.move_id.line_ids:
						elem.name = inv.name
			#fecha = inv.date if inv.date else inv.date_invoice

			#if inv.it_type_document.code == '14':
			#	if not inv.date_due:
			#		raise UserError("Factura por servicios publicos es obligatorio fecha de vencimiento.")
			#	if inv.fecha.split('-')[0] == inv.date_due.split('-')[0] and inv.fecha.split('-')[1] == inv.date_due.split('-')[1]:
			#		pass
			#	else:
			#		raise UserError("El periodo de la fecha de vencimiento debe ser el mismo de la factura.")

		return t


	@api.one
	def validacion_dimension(self):
		if self.reference:
			n_serie = 0
			n_documento = 0
			self.env.cr.execute("select coalesce(n_serie,0), coalesce(n_documento,0) from einvoice_catalog_01 where id = "+ str(self.it_type_document.id))
			
			forelemn = self.env.cr.fetchall()
			for ielem in forelemn:
				n_serie = ielem[0]
				n_documento = ielem[1]

			t = self.reference.split('-')

			if len(t) == 2:				
				if n_serie + n_documento >0 and n_serie + n_documento + 1 != len( self.reference ) :
					raise ValidationError('El nro de dígitos es incorrecto en el Nro. Comprobante.')
			elif len(t) == 1:
				if n_documento >0 and n_documento != len( self.reference ) :
					raise ValidationError('El nro de dígitos es incorrecto en el Nro. Comprobante.')

		


	@api.onchange('reference','it_type_document')
	def onchange_suplier_invoice_number_it(self):
		if self.reference:
			self.reference = str(self.reference).replace(' ','')
			
			if self.reference and self.it_type_document.id:
				self.reference = str(self.reference).replace(' ','')
				t = self.reference.split('-')
				n_serie = 0
				n_documento = 0
				self.env.cr.execute("select coalesce(n_serie,0), coalesce(n_documento,0) from einvoice_catalog_01 where id = "+ str(self.it_type_document.id))
				
				forelemn = self.env.cr.fetchall()
				for ielem in forelemn:
					n_serie = ielem[0]
					n_documento = ielem[1]
				if len(t) == 2:
					parte1= t[0]
					if len(t[0]) < n_serie:
						for i in range(0,n_serie-len(t[0])):
							parte1 = '0'+parte1
					parte2= t[1]
					if len(t[1]) < n_documento:
						for i in range(0,n_documento-len(t[1])):
							parte2 = '0'+parte2
					self.reference = parte1 + '-' + parte2
					
					if n_serie + n_documento >0 and n_serie + n_documento + 1 != len( parte1 + '-' + parte2 ) :
						raise ValidationError('El nro de dígitos es incorrecto en el Nro. Comprobante.')
				elif len(t) == 1:
					parte2= t[0]
					if len(t[0]) < n_documento:
						for i in range(0,n_documento-len(t[0])):
							parte2 = '0'+parte2
					self.reference = parte2

					if n_documento >0 and n_documento != len( parte2 ) :
						raise ValidationError('El nro de dígitos es incorrecto en el Nro. Comprobante.')

				else:
					pass
				
				


	@api.one
	def _get_outstanding_info_JSON(self):
		self.outstanding_credits_debits_widget = json.dumps(False)
		if self.state == 'open':
			domain = [('nro_comprobante','=',self.reference),('type_document_it','=',self.it_type_document.id),('account_id', '=', self.account_id.id), ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id), ('reconciled', '=', False), ('amount_residual', '!=', 0.0)]
			if self.type in ('out_invoice', 'in_refund'):
				domain.extend([('credit', '>', 0), ('debit', '=', 0)])
				type_payment = _('Outstanding credits')
			else:
				domain.extend([('credit', '=', 0), ('debit', '>', 0)])
				type_payment = _('Outstanding debits')
			info = {'title': '', 'outstanding': True, 'content': [], 'invoice_id': self.id}
			lines = self.env['account.move.line'].search(domain)
			currency_id = self.currency_id
			if len(lines) != 0:
				for line in lines:
					# get the outstanding residual value in invoice currency
					if line.currency_id and line.currency_id == self.currency_id:
						amount_to_show = abs(line.amount_residual_currency)
					else:
						amount_to_show = line.company_id.currency_id.with_context(date=line.date).compute(abs(line.amount_residual), self.currency_id)
					if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
						continue
					info['content'].append({
						'journal_name': line.ref or line.move_id.name,
						'amount': amount_to_show,
						'currency': currency_id.symbol,
						'id': line.id,
						'position': currency_id.position,
						'digits': [69, self.currency_id.decimal_places],
					})
				info['title'] = type_payment
				self.outstanding_credits_debits_widget = json.dumps(info)
				self.has_outstanding = True