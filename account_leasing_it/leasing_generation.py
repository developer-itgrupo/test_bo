# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
import base64
from decimal import *

class LeasingGeneration(models.TransientModel):
	_name = 'leasing.generation'

	tc = fields.Float(digits=(12,3))
	mora = fields.Float('Mora')
	factura_cuota = fields.Char('Factura Cuota')
	tc_cuota = fields.Float('Tipo Cambio Cuota',digits=(12,3))
	factura_mora = fields.Char('Factura Mora')
	tc_mora = fields.Float('Tipo Cambio Mora',digits=(12,3))
	journal_id = fields.Many2one('account.journal','Diario de Facturacion')
	account_leasing_id = fields.Many2one('account.leasing')
	account_leasing_line_id = fields.Many2one('account.leasing.line')

	@api.multi
	def get_wizard(self,tc,leasing,line):
		return {
			'name':_('Generacion de Factura'),
			'res_id':self.id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'leasing.generation',
			'views':[[self.env.ref('account_leasing_it.leasing_generation_wizard_view').id,'form']],
			'type':'ir.actions.act_window',
			'target':'new',
			'context':{
				'default_tc':tc,
				'default_account_leasing_id':leasing,
				'default_account_leasing_line_id':line
			}
		}

	@api.multi
	def generar_factura(self):
		parametros = self.env['main.parameter'].search([])[0]
		error = ''
		cantidades = []
		devengo = []
		error += "Falta Cuenta Capital configurada.\n" if not parametros.account_capital_id else ''
		error += "Falta Cuenta Gatos configurada.\n" if not parametros.account_gastos_id else ''
		error += "Falta Cuenta Comision configurada.\n" if not parametros.account_comision_id else ''
		error += "Falta Seguro configurado.\n" if not parametros.account_seguro_id else ''
		error += "Falta Intereses configurado.\n" if not parametros.account_intereses_id else ''
		error += "Falta Cuenta Cargo Devengamiento configurada.\n" if not parametros.account_cargo_devengamiento_id else ''
		error += "Falta Cuenta Abono Devengamiento configurada.\n" if not parametros.account_abono_devengamiento_id else ''
		error += "Falta Cuenta Cargo Interes Monetario configurada.\n" if not parametros.account_cargo_interes_monetario_id else ''
		error += "Falta Diario Asiento de Compra configurado.\n" if not parametros.journal_asiento_compra_id else ''
		error += "Falta Tipo de Comprobante Cuotas configurada.\n" if not parametros.catalog_comprobante_cuotas_id else ''

		if error != '':
			raise UserError('Faltan las siguientes configuraciones en Contabilidad/Configuracion/Parametros/Leasings:\n\n'+error)
		else:
			cantidades.append([self.account_leasing_line_id.capital,parametros.account_capital_id.id,
							parametros.tax_capital.ids if parametros.tax_capital else 0,'CUOTA DE LEASING CAPITAL'])
			cantidades.append([self.account_leasing_line_id.gastos,parametros.account_gastos_id.id,
							parametros.tax_gastos.ids if parametros.tax_gastos else 0,'CUOTA DE LEASING GASTOS'])
			cantidades.append([self.account_leasing_line_id.comision,parametros.account_comision_id.id,
							parametros.tax_comision.ids if parametros.tax_comision else 0,'CUOTA DE LEASING COMISION'])
			cantidades.append([self.account_leasing_line_id.seguro,parametros.account_seguro_id.id,
							parametros.tax_seguro.ids if parametros.tax_seguro else 0,'CUOTA DE LEASING SEGURO'])
			cantidades.append([self.account_leasing_line_id.intereses,parametros.account_intereses_id.id,
							parametros.tax_intereses.ids if parametros.tax_intereses else 0,'CUOTA DE LEASING INTERESES'])

			devengo.append([self.account_leasing_line_id.intereses,parametros.account_cargo_interes_monetario_id.id])
			devengo.append([0,parametros.account_abono_devengamiento_id.id])
			
		vals = {
			'date_invoice':self.account_leasing_line_id.fecha,
			'partner_id':self.account_leasing_id.partner_id.id,
			'account_id':self.account_leasing_id.partner_id.property_account_payable_id.id,
			'journal_id':self.journal_id.id,
			'it_type_document':parametros.catalog_comprobante_cuotas_id.id,
			'currency_id':self.account_leasing_id.currency_id.id,
			'reference':self.factura_cuota if self.factura_cuota else 'S.N.',
			'check_currency_rate':True if self.tc_cuota else False,
			'currency_rate_auto':self.tc_cuota if self.tc_cuota else 0,
			'type':'in_invoice',
			'leasing_line_id':self.account_leasing_line_id.id,
			'line_identifier':'1'
		}
		t = self.env['account.invoice'].create(vals)
		self.account_leasing_line_id.write({'invoice_1':True})
		for c,i in enumerate(cantidades):
			if i[0] > 0: 
				vals_line = {
					'name':i[3],
					'account_id':i[1],
					'price_unit':i[0],
					'invoice_line_tax_ids':[(6,0,i[2])],
					'invoice_id':t.id
				}
				self.env['account.invoice.line'].create(vals_line)

		vals_factura_line = {
			'nro_cuota':self.account_leasing_line_id.nro_cuota,
			'factura':t.id,
			'libro':t.journal_id.id,
			'nro_comprobante':t.reference,
			'fecha_emision':t.date_invoice,
			'fecha_contable':t.date,
			'leasing_id':self.account_leasing_id.id
		}
		obj_factura_line = self.env['factura.line'].create(vals_factura_line)
		t.write({'leasing_factura_line_id':obj_factura_line.id})
		t.button_reset_taxes()
		if self.factura_mora and self.tc_mora:
			vals2 = {
				'date_invoice':self.account_leasing_line_id.fecha,
				'partner_id':self.account_leasing_id.partner_id.id,
				'account_id':self.account_leasing_id.partner_id.property_account_payable_id.id,
				'journal_id':self.journal_id.id,
				'it_type_document':parametros.catalog_comprobante_cuotas_id.id,
				'currency_id':self.account_leasing_id.currency_id.id,
				'reference':self.factura_mora,
				'check_currency_rate':True,
				'currency_rate_auto':self.tc_mora,
				'type':'in_invoice',
				'leasing_line_id':self.account_leasing_line_id.id,
				'line_identifier':'2'
			}
			t2 = self.env['account.invoice'].create(vals2)
			self.account_leasing_line_id.write({'invoice_2':True})
			if self.mora > 0:
				vals_line2 = {
					'name':'MORA EN LA CUOTA DE LEASING',
					'account_id':parametros.account_cargo_interes_monetario_id.id,
					'price_unit':self.mora,
					'invoice_line_tax_ids':[(6,0,i[2])],
					'invoice_id':t2.id
				}
				self.env['account.invoice.line'].create(vals_line2)

			vals_factura_line2 = {
				'nro_cuota':self.account_leasing_line_id.nro_cuota,
				'libro':t2.journal_id.id,
				'factura':t2.id,
				'nro_comprobante':t2.reference,
				'fecha_emision':t2.date_invoice,
				'fecha_contable':t2.date,
				'leasing_id':self.account_leasing_id.id
			}
			obj_factura_line2 = self.env['factura.line'].create(vals_factura_line2)
			t2.write({'leasing_factura_line_id':obj_factura_line2.id})
			t2.button_reset_taxes()

		vals_asiento = {
			'journal_id':parametros.journal_asiento_compra_id.id,
			'partner_id':self.account_leasing_id.partner_id.id,
			'ref':'LEASING NRO '+str(self.account_leasing_id.nro_contrato)+' - CUOTA NRO '+str(self.account_leasing_line_id.nro_cuota),
			'date':self.account_leasing_line_id.fecha,
			'fecha_contable':self.account_leasing_line_id.fecha,
			'leasing_line_id':self.account_leasing_line_id.id
		}
		m = self.env['account.move'].create(vals_asiento)
		self.account_leasing_line_id.write({'move':True})
		sumatoria=0
		currency_suma=0
		for c,i in enumerate(devengo):
			amount_currency = 0
			if self.account_leasing_id.currency_id.name != 'PEN':
				amount_currency = i[0]
				i[0] = self.tc * i[0]
				i[0] = float(Decimal(str(i[0])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
				sumatoria += i[0]
				if parametros.journal_asiento_compra_id.currency_id and parametros.journal_asiento_compra_id.currency_id.name == 'USD':
					currency_suma += amount_currency
			else:
				sumatoria += i[0]
				if parametros.journal_asiento_compra_id.currency_id and parametros.journal_asiento_compra_id.currency_id.name == 'USD':
					currency_suma += amount_currency
			vals_asiento_line = {
				'name':'PRESTAMO '+str(self.account_leasing_id.partner_id.name)+' NRO '+str(self.account_leasing_id.nro_contrato)+' CUOTA NRO '+str(self.account_leasing_line_id.nro_cuota),
				'account_id':i[1],
				'partner_id':self.account_leasing_id.partner_id.id,
				'type_document_it':parametros.catalog_comprobante_cuotas_id.id,
				'nro_comprobante':self.factura_cuota,
				'currency_id':self.account_leasing_id.currency_id.id,
				'debit':0 if c == 1 else i[0],
				'credit':sumatoria if c == 1 else 0,
				'amount_currency':0-currency_suma if c == 1 else amount_currency,
				'tc':self.tc,
				'move_id':m.id
			}
			if vals_asiento_line['debit'] > 0 or vals_asiento_line['credit'] > 0:
				self.env['account.move.line'].create(vals_asiento_line)
		m.post()
		vals_leasing_asiento_line = {
			'libro':m.journal_id.id,
			'fecha_contable':m.fecha_contable,
			'asiento':m.id,
			'nro_cuota':self.account_leasing_line_id.nro_cuota,
			'leasing_id':self.account_leasing_id.id
		}
		obj_asiento = self.env['leasing.asiento.line'].create(vals_leasing_asiento_line)
		m.write({'leasing_asiento_line_id':obj_asiento.id})
		self.account_leasing_line_id.write({
			'mora':self.mora,
			'factura_cuota':self.factura_cuota,
			'tc_cuota':self.tc_cuota,
			'factura_mora':self.factura_mora,
			'tc_mora':self.tc_mora
			})

		return {
			'res_id':self.account_leasing_id.id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'account.leasing',
			'views':[[self.env.ref('account_leasing_it.account_leasing_form_view').id,'form']],
			'type':'ir.actions.act_window',
		}

class AccountInvoice(models.Model):
	_inherit = 'account.invoice'

	leasing_line_id = fields.Many2one('account.leasing.line')
	line_identifier = fields.Char()
	leasing_factura_line_id = fields.Many2one('factura.line')

	@api.multi
	def unlink(self):
		if self.leasing_factura_line_id:
			if self.line_identifier == '1':
				self.leasing_line_id.write({'invoice_1':False})
			else:
				self.leasing_line_id.write({'invoice_2':False})
			self.leasing_factura_line_id.unlink()
		return super(AccountInvoice,self).unlink()

class AccountMove(models.Model):
	_inherit = 'account.move'

	leasing_line_id = fields.Many2one('account.leasing.line')
	leasing_asiento_line_id = fields.Many2one('leasing.asiento.line')

	@api.model
	def unlink(self):
		if self.leasing_asiento_line_id:
			self.leasing_line_id.write({'move':False})
			self.leasing_asiento_line_id.unlink()
		return super(AccountMove,self).unlink()
