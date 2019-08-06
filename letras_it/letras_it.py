# -*- coding: utf-8 -*-
from openerp.osv import osv
import base64
from odoo import models, fields, api
from datetime import datetime, timedelta

class letras_it(models.Model):
	_name = 'letras.it'
	
	name = fields.Char(string='Nro Letra', related='id_Pago.ref_op')
	fch_Emision = fields.Date(string='Fecha de Emisión', related='id_Pago.payment_date')
	id_Cliente = fields.Many2one('res.partner', ondelete='set null', string='Cliente', related='id_Pago.partner_id')
	tp_Plazo_Pago = fields.Many2one('account.payment.term', ondelete='set null', string='Plazo de Pago', related='id_Pago.tp_plazo_pago')
	id_Vendedor = fields.Many2one('res.users', string='Vendedor')
	fch_Vencimiento = fields.Date(string='Fecha de Vencimiento', readonly = True)
	id_Pago = fields.Many2one('account.payment', ondelete='cascade', string='Pago', required = False)
	state = fields.Selection([
		('cartera', "En Cartera"),
		('cobranza', "En Cobranza"),
		('descontada', "Descontada"),
	], default='cartera')
	id_Diario = fields.Many2one('account.journal', string='Diario', related='id_Pago.journal_id', required=True, domain=[('type', 'in', ('bank', 'cash'))])
	id_Cuenta = fields.Many2one('account.account', string='Cuenta de Letra', related='id_Pago.journal_id.default_debit_account_id', readonly = True, domain=[('deprecated', '=', False)])
	fch_Cobranza = fields.Date(string='Pase a Cobranza')
	fch_Descuento = fields.Date(string='Pase a Descuento')
	monto = fields.Monetary(string='Monto', required=True, related='id_Pago.amount')
	currency_id = fields.Many2one('res.currency', string='Moneda', required=True, default=lambda self: self.env.user.company_id.currency_id, related='id_Pago.currency_id')

	@api.multi
	def action_cartera(self):
		self.state = 'cartera'

	@api.multi
	def action_cobranza(self):
		self.state = 'cobranza'

	@api.multi
	def action_descontada(self):
		self.state = 'descontada'

	@api.onchange('fch_Vencimiento','tp_Plazo_Pago')
	def onchange_fch_vencimiento(self):
		if not self.tp_Plazo_Pago is None and not self.fch_Emision is None and self.fch_Emision != False:
			if self.tp_Plazo_Pago.id == 1:
				self.fch_Vencimiento = fields.Datetime.from_string(self.fch_Emision)
			elif self.tp_Plazo_Pago.id == 2:
				self.fch_Vencimiento = fields.Datetime.from_string(self.fch_Emision) + timedelta(days=15)
			elif self.tp_Plazo_Pago.id == 3:
				self.fch_Vencimiento = fields.Datetime.from_string(self.fch_Emision) + timedelta(days=30)

	@api.one
	def write(self,vals):
		_state = None

		if 'state' in vals:
			_state = vals['state']
		else:
			_state = self.state

		if _state == 'cartera':
			vals['fch_Cobranza'] = False
			vals['fch_Descuento'] = False
			self.env['account.move'].search([('ref','=',self.name)]).unlink()

		if _state == 'cobranza':
			if not 'fch_Cobranza' in vals and (self.fch_Cobranza is None or self.fch_Cobranza == False):
				vals['fch_Cobranza'] = fields.date.today()
			asiento_cobranza = self.env['account.move'].search([('ref','=',self.name)])
			if len(asiento_cobranza) > 0:
				asiento = self.env['account.move'].write(asiento_cobranza, self.obtener_valores_asiento(self, "cobranza"))
			else:
				asiento = self.env['account.move'].create(self.obtener_valores_asiento("cobranza"))
				self.env['account.move.line'].create(self.obtener_valores_asiento_line("credito", "cobranza", asiento.id))
				self.env['account.move.line'].create(self.obtener_valores_asiento_line("debito", "cobranza", asiento.id))

		if _state == 'descontada':
			if not 'fch_Descuento' in vals and (self.fch_Descuento is None or self.fch_Descuento == False):
				vals['fch_Descuento'] = fields.date.today()
			asiento_descontada = self.env['account.move'].search([('ref','=',self.name)])
			if len(asiento_descontada) > 1:
				asiento = self.env['account.move'].write(asiento_descontada, self.obtener_valores_asiento(self, "descontada"))
			else:
				asiento = self.env['account.move'].create(self.obtener_valores_asiento(self, "descontada"))
				self.env['account.move.line'].create(self.obtener_valores_asiento_line("credito", "descontada", asiento.id))
				self.env['account.move.line'].create(self.obtener_valores_asiento_line("debito", "descontada", asiento.id))

		t = super(letras_it,self).write(vals)
		return t

	def obtener_valores_asiento(self, tipo_fecha):
		fecha_c = None
		if tipo_fecha == "cobranza":
			if  self.fch_Cobranza is None or self.fch_Cobranza == False:
				print "Cobranza now\n"
				fecha_c = fields.date.today()
			else:
				print "Cobranza valor\n"
				fecha_c = self.fch_Cobranza
		else:
			if  self.fch_Descuento is None or self.fch_Descuento == False:
				print "Descontada now\n"
				fecha_c = fields.date.today()
			else:
				print "Descontada valor\n"
				fecha_c = self.fch_Descuento
		print fecha_c
		return {
			'journal_id': self.id_Diario.id,
			'date': fecha_c,
			'ref': self.name
		}

	def obtener_valores_asiento_line(self, tipo_mov, tipo_state, id_asiento):
		debito = 0
		credito = 0
		_account_id = None
		if tipo_mov == "debito":
			if  self.monto is None or self.monto == False:
				debito = 0
			else:
				debito = self.monto
			parametros = self.env['main.parameter'].search([('id','=','1')])
			if len(parametros) > 0:
				if tipo_state == "cobranza":
					_account_id = parametros.account_cobranza_letras_mn.id
				else:
					_account_id = parametros.account_descuento_letras_mn.id
		else:
			if  self.monto is None or self.monto == False:
				credito = 0
			else:
				credito = self.monto
			_account_id = self.id_Cuenta.id
		return {
			'account_id': _account_id,
			'partner_id': self.id_Cliente.id,
			'type_document_it': 1,
			'nro_comprobante': self.name,
			'name': "TRASLADO DE LETRA A COBRANNZA",
			'debit': debito,
			'credit': credito,
			'date_maturity': self.fch_Vencimiento,
			'tc': 0,
			'move_id': id_asiento
		}
# class letras_it(models.Model):
#     _name = 'letras_it.letras_it'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100