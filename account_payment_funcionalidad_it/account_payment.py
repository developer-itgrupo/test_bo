# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError

class account_payment(models.Model):
	_inherit = 'account.payment'

	move_name_second = fields.Char('Move_name_second')

	@api.model
	def default_get(self, default_fields):
		default_it_type_document = False
		default_nro_comprobante = False

		t = self.env['account.invoice'].browse(self._context.get('active_id'))
		if t:
			default_it_type_document = t.it_type_document.id
			default_nro_comprobante = t.reference

		contextual_self = self.with_context(default_it_type_document=default_it_type_document, default_nro_comprobante=default_nro_comprobante)
		return super(account_payment, contextual_self).default_get(default_fields)

	@api.multi
	def cancel(self):
		for rec in self:
			for move in rec.move_line_ids.mapped('move_id'):
				move.line_ids.remove_move_reconcile()
				move.button_cancel()
				move.unlink()
			rec.state = 'draft'

			
	@api.multi
	def unlink(self):
		for rec in self:
			rec.move_name = False
		return super(account_payment,self).unlink()



	@api.multi
	def post(self):
		for inv in self:
			if inv.currency_id.name == 'USD':
				currency_obj = self.env['res.currency'].search([('name','=','USD')])
				if len(currency_obj)>0:
					currency_obj = currency_obj[0]
				else:
					raise UserError( 'Error!\nNo existe la moneda USD' )

				eliminar = False

				fecha = inv.payment_date if inv.payment_date else fields.Date.context_today(inv)
				tipo_cambio = self.env['res.currency.rate'].search([('name','=',fecha),('currency_id','=',currency_obj.id)])

				if len(tipo_cambio)>0:
					tipo_cambio = tipo_cambio[0]
				else:
					if self.check_currency_rate:
						tipo_cambio = self.env['res.currency.rate'].create({'currency_id':currency_obj.id,'name':fecha,'type_sale':1,'rate':1,})
						eliminar = True

						vactual = 0
						ractual = 0

						if inv.check_currency_rate:
							vactual = tipo_cambio.type_sale
							ractual = tipo_cambio.rate

							tipo_cambio.type_sale = inv.change_type
							tipo_cambio.rate = 1.0 / inv.change_type

						else:
							inv.change_type = tipo_cambio.type_sale


					t = super(account_payment,inv).post()

					inv.refresh()
					for i in inv.move_line_ids[0].move_id.line_ids:
						i.tc = tipo_cambio.type_sale
						if i.tax_amount:
							i.tax_amount = i.debit + i.credit

					if inv.check_currency_rate:
						tipo_cambio.type_sale = vactual
						tipo_cambio.rate = ractual

					if eliminar:
						tipo_cambio.unlink()


					if inv.move_line_ids.ids:
						inv.move_line_ids[0].move_id.means_payment_it = inv.means_payment_id
						for elem in inv.move_line_ids:
							nro_c = inv.nro_comprobante
							if elem.account_id.id == inv.journal_id.default_debit_account_id.id:
								elem.move_id.rendicion_id = inv.rendicion_id.id
								elem.rendicion_id = inv.rendicion_id.id
								nro_c = inv.rendicion_id.name
							elem.nro_comprobante = nro_c 
							elem.type_document_it = inv.it_type_document.id
							if elem.account_id.user_type_id.type == 'liquidity':								
								elem.nro_comprobante =  self.nro_caja
								elem.type_document_it = False

					t = self.env['account.invoice'].browse(self._context.get('active_id'))
					if t:
						t.write({})



					else:
						#raise UserError( 'Error!\nNo existe el tipo de cambio para la fecha: '+ str(fecha) )
						pass
				

						t = super(account_payment,inv).post()


			else:
				t = super(account_payment,inv).post()

				if inv.move_line_ids.ids:
					inv.move_line_ids[0].move_id.means_payment_it = inv.means_payment_id
					for elem in inv.move_line_ids:
						nro_c = inv.nro_comprobante
						if elem.account_id.id == inv.journal_id.default_debit_account_id.id and inv.rendicion_id.id:
							elem.move_id.rendicion_id = inv.rendicion_id.id
							elem.rendicion_id = inv.rendicion_id.id
							nro_c = inv.rendicion_id.name
						elem.nro_comprobante = nro_c 
						elem.type_document_it = inv.it_type_document.id
						if elem.account_id.user_type_id.type == 'liquidity' and  not inv.rendicion_id.id:
							elem.nro_comprobante =  self.nro_caja
							elem.type_document_it = False
							
				t = self.env['account.invoice'].browse(self._context.get('active_id'))
				if t:
					t.write({})
			for i in inv.move_line_ids:
				i.move_id.write({'means_payment_it':self.means_payment_id.id})
				i.write({'name':self.communication,
						'type_document_it':self.it_type_document.id if self.it_type_document else 0})
				if i.account_id.internal_type == 'liquidity':
					if i.journal_id:
						if i.journal_id.default_debit_account_id.id == i.account_id.id:
							i.write({'nro_comprobante':self.nro_caja})
						else:
							i.write({'nro_comprobante':self.nro_comprobante})

				if self.payment_type == 'transfer':
					if not i.full_reconcile_id:
						if i.debit > 0:
							if self.destination_journal_id.check_rendicion:
								i.move_id.write({'rendicion_id':self.rendicion_destino_id.id if self.rendicion_destino_id.id else 0,
												'journal_id':self.destination_journal_id.id})
							if self.destination_journal_id.is_small_cash:
								i.move_id.write({'small_cash_id':self.small_cash_destino.id if self.small_cash_destino.id else 0,
												'journal_id':self.destination_journal_id.id})
						if i.credit > 0:
							if self.journal_id.check_rendicion:
								i.move_id.write({'rendicion_id':self.rendicion_id.id if self.rendicion_id.id else 0,
												'journal_id':self.journal_id.id})
							if self.journal_id.is_small_cash:
								i.move_id.write({'small_cash_id':self.small_cash.id if self.small_cash.id else 0,
												'journal_id':self.journal_id.id})
			

	def _get_move_vals(self, journal=None):
		""" Return dict to create the payment move
		"""
		if journal:
			journal = journal
			if not journal.sequence_id:
				raise UserError( (u'Error de Configuracion!'), ('El diario %s no tiene secuencia, por favor especificarla.') % journal.name)
			if not journal.sequence_id.active:
				raise UserError( (u'Error de Configuracion!'), ('La secuencia del diario %s esta desactivada.') % journal.name)
			name = self.move_name_second or journal.with_context(ir_sequence_date=self.payment_date).sequence_id.next_by_id()
			self.move_name_second = name
			return {
				'name': name,
				'date': self.payment_date,
				'ref': self.communication or '',
				'company_id': self.company_id.id,
				'journal_id': journal.id,
			}
		else:
			journal = self.journal_id
			if not journal.sequence_id:
				raise UserError( (u'Error de Configuracion!'), ('El diario %s no tiene secuencia, por favor especificarla.') % journal.name)
			if not journal.sequence_id.active:
				raise UserError( (u'Error de Configuracion!'), ('La secuencia del diario %s esta desactivada.') % journal.name)
			name = self.move_name or journal.with_context(ir_sequence_date=self.payment_date).sequence_id.next_by_id()
			return {
				'name': name,
				'date': self.payment_date,
				'ref': self.communication or '',
				'company_id': self.company_id.id,
				'journal_id': journal.id,
			}