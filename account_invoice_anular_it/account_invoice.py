# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv
import datetime

class mensaje_anulacion_it(models.Model):
	_name = 'mensaje.anulacion.it'

	@api.one
	def mensaje_anulacion_op(self):
		invoice_heredado = self.env['account.invoice'].search([('id','=',self.env.context['active_id'])])[0]
		invoice_heredado.anular_action_factura_it()   


class account_invoice(models.Model):
	_inherit = 'account.invoice'

	@api.multi
	def anular_factura_it(self):
		return {
				'type': 'ir.actions.act_window',
				'res_model': 'mensaje.anulacion.it',
				'view_mode': 'form',
				'view_type': 'form',
				'target': 'new',
			}

	@api.one
	def anular_action_factura_it(self):
		if "%.2f"%self.residual != "%.2f"%self.amount_total:
			raise osv.except_osv('Alerta','Existen pagos relacionados a esta Factura.')
 
		parametros = self.env['main.parameter'].search([])[0]
		if not parametros.partner_null_id.id:
			raise osv.except_osv('Alerta','No tienen el partner Anulados Configurado en Parametros.')
			
		self.env.cr.execute("update account_invoice set partner_id = " + str(parametros.partner_null_id.id) + " where id = " + str(self.id) )
		self.env.cr.execute("update account_invoice set amount_untaxed = 0 where id = " + str(self.id) )
		self.env.cr.execute("update account_invoice set amount_tax = 0 where id = " + str(self.id) )
		self.env.cr.execute("update account_invoice set amount_total = 0 where id = " + str(self.id) )
		self.env.cr.execute("update account_invoice set residual = 0 where id = " + str(self.id) )
		self.env.cr.execute("update account_invoice set amount_total_signed = 0 where id = " + str(self.id) )
		self.env.cr.execute("update account_invoice set residual_signed = 0 where id = " + str(self.id) )
		self.env.cr.execute("update account_invoice set state = 'paid' where id = " + str(self.id) )
		lineas = self.invoice_line_ids.ids
		borrados = []
		if len(lineas)==1:
			pass
		elif len(lineas)>1:
			borrados= lineas[1:]
		else:
			raise osv.except_osv('Alerta','No contiene lineas la Factura.')

		for i in borrados:
			self.env.cr.execute("delete from account_invoice_line where id = " + str(i) )

		self.refresh()

		for i in self.invoice_line_ids:
			#self.env.cr.execute("update account_invoice_line set location_id = null  where id = " + str(i.id) )
			self.env.cr.execute("update account_invoice_line set product_id = null  where id = " + str(i.id) )
			self.env.cr.execute("update account_invoice_line set name = 'Anulado'  where id = " + str(i.id) )
			self.env.cr.execute("update account_invoice_line set quantity = 0  where id = " + str(i.id) )
			self.env.cr.execute("update account_invoice_line set price_unit = 0  where id = " + str(i.id) )
			self.env.cr.execute("update account_invoice_line set price_subtotal = 0  where id = " + str(i.id) )
			self.env.cr.execute("update account_invoice_line set price_subtotal_signed = 0  where id = " + str(i.id) )

		for l in self.tax_line_ids:
			self.env.cr.execute("delete from account_invoice_tax where id = " + str(l.id) )

		asiento = self.move_id

		self.env.cr.execute("update account_move set partner_id = " + str(parametros.partner_null_id.id) + " where id = " + str(asiento.id) )

		if len(asiento.line_ids)==0:
			raise osv.except_osv('Alerta','El asiento no contiene lineas')
		salvado = []

		account = self.account_id.id

		for i in asiento.line_ids:
			if i.account_id.id == account:
				if len(salvado)==0 :
					salvado.append(i.id)
		if len(salvado) == 0:
			salvado=[asiento.line_ids[0].id]

		for j in asiento.line_ids:
			if j.id == salvado[0]:
				pass
			else:
				self.env.cr.execute("delete from account_move_line where id = " + str(j.id) )

		asiento.refresh()



		if parametros.product_null_id.id and len(parametros.product_null_id.taxes_id)>0 and len(parametros.product_null_id.supplier_taxes_id)>0 and parametros.product_null_id.property_account_income_id.id and parametros.product_null_id.property_account_expense_id.id:
			pass
		else:
			raise osv.except_osv('Alerta','Se requiere configurar en Parametros el producto Anulado, sus impuestos y cuentas del mismo para Anular la Factura.')

		for j in asiento.line_ids:
			self.env.cr.execute("update account_move_line set name = 'Anulado'  where id = " + str(j.id) )
			self.env.cr.execute("update account_move_line set partner_id = " + str(parametros.partner_null_id.id) + " where id = " + str(j.id) )

			self.env.cr.execute("update account_move_line set debit = 0  where id = " + str(j.id) )
			self.env.cr.execute("update account_move_line set credit = 0  where id = " + str(j.id) )
			self.env.cr.execute("update account_move_line set amount_currency = 0  where id = " + str(j.id) )
			self.env.cr.execute("update account_move_line set tax_amount = 0  where id = " + str(j.id) )
			self.env.cr.execute("update account_move_line set amount_residual = 0  where id = " + str(j.id) )
			self.env.cr.execute("update account_move_line set amount_residual_currency = 0  where id = " + str(j.id) )
			self.env.cr.execute("update account_move_line set credit_cash_basis = 0  where id = " + str(j.id) )
			self.env.cr.execute("update account_move_line set debit_cash_basis = 0  where id = " + str(j.id) )
			self.env.cr.execute("update account_move_line set balance_cash_basis = 0  where id = " + str(j.id) )
			self.env.cr.execute("update account_move_line set balance = 0  where id = " + str(j.id) )
			self.env.cr.execute("update account_move_line set quantity = 0  where id = " + str(j.id) )
			self.env.cr.execute("update account_move_line set product_id = null  where id = " + str(j.id) )
			self.env.cr.execute("update account_move_line set tax_code_id = " + str( ( parametros.product_null_id.taxes_id[0].base_code_id.id if self.type in ('out_invoice','out_refund') else parametros.product_null_id.supplier_taxes_id[0].base_code_id.id ) if parametros.product_null_id.id else 'null') + " where id = " + str(j.id) )
			self.env.cr.execute("update account_move_line set account_id = " + str( ( parametros.product_null_id.property_account_income_id.id if self.type in ('out_invoice','out_refund') else parametros.product_null_id.property_account_expense_id.id ) if parametros.product_null_id.id else 'null') + " where id = " + str(j.id) )
			

		account = self.account_id.id
		lines = []
		for i in self.move_id.line_ids:
			lines.append(i)

		
		#self.move_id.line_ids.reconcile( [line.id for line in lines] )

