# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
import base64
from decimal import *

class AccountGeneration(models.TransientModel):
	_name = 'account.generation'

	fecha = fields.Date('Fecha',default=datetime.now())
	journal_pago_id = fields.Many2one('account.journal','Diario de Pago')
	mora = fields.Float('Monto Mora')
	tc = fields.Float('TC',digits=(12,3))
	nro_comprobante = fields.Char('Nro. de Comprobante')
	account_prestamo_id = fields.Many2one('account.prestamo')
	account_prestamo_line_id = fields.Many2one('account.prestamo.line')

	@api.multi
	def get_wizard(self,fecha,tc,nro,prestamo,line):
		return {
			'name':_('Generacion de Asiento'),
			'res_id':self.id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'account.generation',
			'views':[[self.env.ref('account_prestamo_it.account_generation_wizard_view').id,'form']],
			'type':'ir.actions.act_window',
			'target':'new',
			'context':{
				'default_fecha':fecha,
				'default_tc':tc,
				'default_nro_comprobante':nro,
				'default_account_prestamo_id':prestamo,
				'default_account_prestamo_line_id':line
			}
		}

	@api.multi
	def generar_asiento(self):
		parametros = self.env['main.parameter'].search([])[0]
		error = ''
		cantidades = []
		devengo = []
		error += "Falta Cuenta Amortizacion Capital configurada.\n" if not parametros.account_amortizacion_capital_id else ''
		error += "Falta Cuenta Interes configurada.\n" if not parametros.account_interes_id else ''
		error += "Falta Cuenta de ITF configurada.\n" if not parametros.account_itf_id else ''
		error += "Falta Cuenta Mora configurada.\n" if not parametros.account_mora_id else ''
		error += "Falta Diario Asiento Devengo configurado.\n" if not parametros.journal_asiento_devengo_id else ''
		error += "Falta Tipo Comprobante de Pago configurado.\n" if not parametros.catalog_comprobante_pago_id else ''
		error += "Falta Cuenta Cargo Devengo configurada.\n" if not parametros.account_cargo_devengo_id else ''
		error += "Falta Cuenta Abono Devengo configurada.\n" if not parametros.account_abono_devengo_id	else ''

		if error != '':
			raise UserError('Faltan las siguientes configuraciones en Contabilidad/Configuracion/Parametros/Prestamos:\n\n'+error)
		else:
			cantidades.append([self.account_prestamo_line_id.amortizacion_capital,parametros.account_amortizacion_capital_id.id])
			cantidades.append([self.account_prestamo_line_id.interes,parametros.account_interes_id.id])
			cantidades.append([self.account_prestamo_line_id.itf,parametros.account_itf_id.id])
			cantidades.append([self.mora,parametros.account_mora_id.id])
			if not self.journal_pago_id.default_credit_account_id:
				raise UserError("El diario seleccionado no tiene una cuenta de pago por defecto")
			cantidades.append([0,self.journal_pago_id.default_credit_account_id.id])
			devengo.append([self.account_prestamo_line_id.interes,parametros.account_cargo_devengo_id.id])
			devengo.append([0,parametros.account_abono_devengo_id.id])

		vals = {
			'journal_id':self.journal_pago_id.id,
			'partner_id':self.account_prestamo_id.partner_id.id,
			'ref':'PRESTAMO NRO '+str(self.account_prestamo_id.nro_prestamo)+' - CUOTA NRO '+str(self.account_prestamo_line_id.nro_cuota),
			'date':self.account_prestamo_line_id.fecha_vencimiento,
			'fecha_contable':self.account_prestamo_line_id.fecha_vencimiento,
			'prestamo_line_id':self.account_prestamo_line_id.id,
			'prestamo_identifier':'1'
		}
		vals2 = {
			'journal_id':parametros.journal_asiento_devengo_id.id,
			'partner_id':self.account_prestamo_id.partner_id.id,
			'ref':'PRESTAMO NRO '+str(self.account_prestamo_id.nro_prestamo)+' - CUOTA NRO '+str(self.account_prestamo_line_id.nro_cuota),
			'date':self.account_prestamo_line_id.fecha_vencimiento,
			'fecha_contable':self.account_prestamo_line_id.fecha_vencimiento,
			'prestamo_line_id':self.account_prestamo_line_id.id,
			'prestamo_identifier':'2'
		}
		t = self.env['account.move'].create(vals)
		self.account_prestamo_line_id.write({'move_1':True})
		t2 = self.env['account.move'].create(vals2)
		self.account_prestamo_line_id.write({'move_2':True})
		sumatoria = 0
		currency_suma = 0
		print("c",cantidades)
		for c,i in enumerate(cantidades):
			amount_currency = 0
			if self.account_prestamo_id.currency_id.name != 'PEN':
				amount_currency = i[0]
				i[0] = self.tc * i[0]
				i[0] = float(Decimal(str(i[0])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
				sumatoria += i[0]
				if self.journal_pago_id.currency_id and self.journal_pago_id.currency_id.name == 'USD':
					currency_suma += amount_currency
			else:
				sumatoria += i[0]
				if self.journal_pago_id.currency_id and self.journal_pago_id.currency_id.name == 'USD':
					currency_suma += amount_currency
			vals_line = {
				'name':'PRESTAMO '+str(self.account_prestamo_id.partner_id.name)+' NRO '+str(self.account_prestamo_id.nro_prestamo)+' CUOTA NRO '+str(self.account_prestamo_line_id.nro_cuota),
				'account_id':i[1],
				'partner_id':self.account_prestamo_id.partner_id.id,
				'type_document_it':parametros.catalog_comprobante_pago_id.id,
				'nro_comprobante':self.nro_comprobante,
				'currency_id':self.account_prestamo_id.currency_id.id,
				'debit':0 if c == 4 else i[0],
				'credit':sumatoria if c == 4 else 0,
				'amount_currency':0-currency_suma if c == 4 else amount_currency,
				'tc':self.tc,
				'move_id':t.id
			}
			if vals_line['debit'] > 0 or vals_line['credit'] > 0:
				self.env['account.move.line'].create(vals_line)
		sumatoria = 0
		currency_suma = 0
		for c,i in enumerate(devengo):
			amount_currency = 0
			if self.account_prestamo_id.currency_id.name != 'PEN' and c == 0:
				amount_currency = i[0]
				i[0] = self.tc * i[0]
				i[0] = float(Decimal(str(i[0])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
				sumatoria += i[0]
				if self.journal_pago_id.currency_id and self.journal_pago_id.currency_id.name == 'USD':
					currency_suma += amount_currency
			else:
				sumatoria += i[0]
				if self.journal_pago_id.currency_id and self.journal_pago_id.currency_id.name == 'USD':
					currency_suma += amount_currency
			vals_line2 = {
				'name':'DEVENGAMIENTO '+str(self.account_prestamo_id.partner_id.name)+' NRO '+str(self.account_prestamo_id.nro_prestamo)+' CUOTA NRO '+str(self.account_prestamo_line_id.nro_cuota),
				'account_id':i[1],
				'partner_id':self.account_prestamo_id.partner_id.id,
				'type_document_it':parametros.catalog_comprobante_pago_id.id,
				'nro_comprobante':self.nro_comprobante,
				'currency_id':self.account_prestamo_id.currency_id.id,
				'debit':0 if c == 1 else i[0],
				'credit':sumatoria if c == 1 else 0,
				'amount_currency':0-currency_suma if c == 1 else amount_currency,
				'tc':self.tc,
				'move_id':t2.id
			}
			if vals_line2['debit'] > 0 or vals_line2['credit'] > 0: 
				self.env['account.move.line'].create(vals_line2)

		t.post()
		t2.post()
		vals_asiento_line = {
			'libro':t.journal_id.id,
			'fecha_contable':t.fecha_contable,
			'asiento':t.id,
			'nro_cuota':self.account_prestamo_line_id.nro_cuota,
			'prestamo_id':self.account_prestamo_id.id
		}
		vals_asiento_line2 = {
			'libro':t2.journal_id.id,
			'fecha_contable':t2.fecha_contable,
			'asiento':t2.id,
			'nro_cuota':self.account_prestamo_line_id.nro_cuota,
			'prestamo_id':self.account_prestamo_id.id
		}
		obj_asiento = self.env['asiento.line'].create(vals_asiento_line)
		obj_asiento2 = self.env['asiento.line'].create(vals_asiento_line2)

		t.write({'prestamo_asiento_line_id':obj_asiento.id})
		t2.write({'prestamo_asiento_line_id':obj_asiento2.id})

		return {
            'res_id':self.account_prestamo_id.id,
            'view_type':'form',
            'view_mode':'form',
            'res_model':'account.prestamo',
            'views':[[self.env.ref('account_prestamo_it.account_prestamo_form_view').id,'form']],
            'type':'ir.actions.act_window',
        }

class AccountMove(models.Model):
	_inherit = 'account.move'

	prestamo_line_id = fields.Many2one('account.prestamo.line')
	prestamo_identifier = fields.Char()
	prestamo_asiento_line_id = fields.Many2one('asiento.line')

	@api.model
	def unlink(self):
		if self.prestamo_asiento_line_id:
			if self.prestamo_identifier == '1':
				self.prestamo_line_id.write({'move_1':False})
			else:
				self.prestamo_line_id.write({'move_2':False})
			self.prestamo_asiento_line_id.unlink()
		return super(AccountMove,self).unlink()