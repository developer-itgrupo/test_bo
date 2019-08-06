# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _
from datetime import datetime, timedelta

class account_payment(models.Model):
	_inherit='account.payment'

	means_payment_id = fields.Many2one('einvoice.means.payment','Medio de Pago')
	change_type = fields.Float('Tipo de Cambio Divisa',digits=(12,3))
	check_currency_rate = fields.Boolean('T.C. Personalizado?')
	it_type_document = fields.Many2one('einvoice.catalog.01','Tipo Documento')
	nro_comprobante = fields.Char('Nro comprobante')
	rendicion_id = fields.Many2one('account.rendicion.it','Rendicion Origen')
	rendicion_destino_id = fields.Many2one('account.rendicion.it','Rendicion Destino')
	c_rendicion = fields.Boolean('C_c',related='journal_id.check_rendicion')
	c_canje_letras = fields.Boolean('C_cl',related='journal_id.check_canje_letras')

	@api.one
	@api.depends('destination_journal_id')
	def get_rendicion_destino(self):
		self.c_rendicion_destino = True if self.destination_journal_id.check_rendicion else False

	c_rendicion_destino = fields.Boolean(compute='get_rendicion_destino')
	tp_plazo_pago = fields.Many2one('account.payment.term','Plazo de Pago')
	fch_vencimiento = fields.Date('Fecha de Vencimiento', readonly = True)
	num_unico_letras = fields.Char('Número Único de Letras')
	ref_op = fields.Char('Ref. Op.')

	nro_caja = fields.Char('Nro. de Op. Caja')

	@api.onchange('nro_comprobante','it_type_document')
	def onchange_suplier_invoice_number_it(self):
		if self.nro_comprobante:
			self.nro_comprobante = str(self.nro_comprobante).replace(' ','')
			
			if self.nro_comprobante and self.it_type_document.id:
				self.nro_comprobante = str(self.nro_comprobante).replace(' ','')
				t = self.nro_comprobante.split('-')
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
					self.nro_comprobante = parte1 + '-' + parte2
				elif len(t) == 1:
					parte2= t[0]
					if len(t[0]) < n_documento:
						for i in range(0,n_documento-len(t[0])):
							parte2 = '0'+parte2
					self.nro_comprobante = parte2
				else:
					pass


	@api.onchange('payment_date','check_currency_rate')
	def onchange_payment_date(self):
		if self.check_currency_rate == False:
			currency = self.env['res.currency'].search([('name','=','USD')])[0]
			rate = self.env['res.currency.rate'].search([('currency_id','=',currency.id),('name','=',self.payment_date)])

			if len(rate)>0:
				self.change_type = rate[0].type_sale
			else:
				self.change_type = 1

	@api.onchange('partner_id','partner_type')
	def onchange_plazo_pago(self):
		if self.partner_id != "":
			plazo_pago = self.env['res.partner'].search([('id','=',self.partner_id.id)])
			if self.partner_type == "supplier":

				if len(plazo_pago)>0 and plazo_pago[0].property_supplier_payment_term_id != "":
					self.tp_plazo_pago = plazo_pago[0].property_supplier_payment_term_id
			else:
				if len(plazo_pago)>0 and plazo_pago[0].property_payment_term_id != "":
					self.tp_plazo_pago = plazo_pago[0].property_payment_term_id

	@api.onchange('payment_date','tp_plazo_pago')
	def onchange_fch_vencimiento(self):
		if not self.tp_plazo_pago is None and not self.payment_date is None:
			if self.tp_plazo_pago.id == 1:
				self.fch_vencimiento = fields.Datetime.from_string(self.payment_date)
			elif self.tp_plazo_pago.id == 2:
				self.fch_vencimiento = fields.Datetime.from_string(self.payment_date) + timedelta(days=15)
			elif self.tp_plazo_pago.id == 3:
				self.fch_vencimiento = fields.Datetime.from_string(self.payment_date) + timedelta(days=30)


	@api.model
	def create(self,vals):
		t = super(account_payment,self).create(vals)
		if t.check_currency_rate == False:
			currency = self.env['res.currency'].search([('name','=','USD')])[0]
			rate = self.env['res.currency.rate'].search([('currency_id','=',currency.id),('name','=',t.payment_date)])

			if len(rate)>0:
				t.change_type = rate[0].type_sale
				t.write({'change_type':rate[0].type_sale})
			else:
				t.change_type = 1
				t.write({'change_type':1})
		return t


	@api.one
	def write(self,vals):
		fechas = None
		check = None
		_state = None
		_c_canje_letras = None
		_payment_type = None

		if 'payment_date' in vals:
			fechas = vals['payment_date']
		else:
			fechas = self.payment_date

		if 'check_currency_rate' in vals:
			check = vals['check_currency_rate']
		else:
			check = self.check_currency_rate

		if 'state' in vals:
			_state = vals['state']
		else:
			_state = self.state

		if 'c_canje_letras' in vals:
			_c_canje_letras = vals['c_canje_letras']
		else:
			_c_canje_letras = self.c_canje_letras

		if 'payment_type' in vals:
			_payment_type = vals['payment_type']
		else:
			_payment_type = self.payment_type


		if check == False:
			currency = self.env['res.currency'].search([('name','=','USD')])[0]
			rate = self.env['res.currency.rate'].search([('currency_id','=',currency.id),('name','=',fechas)])

			if len(rate)>0:
				vals['change_type'] = rate[0].type_sale
			else:
				vals['change_type'] = 1

		if _state in ['posted', 'reconciled'] and _c_canje_letras == True and _payment_type == 'inbound':
			letra = self.env['letras.it'].search([('id_Pago','=',self.id)])
			if len(letra) > 0:
				self.env['letras.it'].write(letra, self.obtener_valores_letras_upd())
			else:
				self.env['letras.it'].create(self.obtener_valores_letras_ins())

		t = super(account_payment,self).write(vals)
		return t

	def obtener_valores_letras_upd(self):
		return {
			'id_Cliente': self.partner_id.id,
			'id_Diario': self.journal_id.id,
			'id_Cuenta': self.journal_id.default_debit_account_id
		}

	def obtener_valores_letras_ins(self):
		return {
			'name': self.ref_op,
			'fch_Emision': self.payment_date,
			'id_Cliente': self.partner_id.id,
			'tp_Plazo_Pago': self.tp_plazo_pago.id,
			'id_Diario': self.journal_id.id,
			'id_Cuenta': self.journal_id.default_debit_account_id.id,
			'id_Vendedor': self.partner_id.user_id.id,
			'fch_Vencimiento': self.fch_vencimiento,
			'monto': self.amount,
			'currency_id': self.currency_id.id,
			'id_Pago': self.id
		}
