# -*- coding: utf-8 -*-

from openerp import models, fields, api
import base64
from openerp.osv import osv

class anticipo_proveedor(models.Model):
	_name = 'anticipo.proveedor'


	name = fields.Char('Nombre',size=200)
	state = fields.Selection([('draft','Borrador'), ('done','Entregado'), ('cancel','Cancelado')], 'Estado', readonly=True, copy=False, default='draft')
	
	tipo = fields.Selection([('cliente','Cliente'), ('proveedor','Proveedor')], 'Tipo', required="1", default='cliente')
	fecha = fields.Date('Fecha')
	empresa = fields.Many2one('res.partner', string='Empresa')

	metodo_pago = fields.Many2one('account.journal','Metodo Pago', domain="[('type','=',['cash','bank'])]")
	medio_pago = fields.Many2one('einvoice.means.payment','Medio de Pago')

	comprobante_caja = fields.Char('Comprobante Caja',size=200)
	comprobante_anticipo = fields.Char('Comprobante Anticipo', size=200)
	memoria = fields.Char(required="1", string='Memoria',size=300)
	flujo_efectivo = fields.Many2one('account.config.efective','Flujo de Efectivo')
	monto = fields.Float('Monto', digits=(12,2))
	ruc = fields.Char('RUC', related='empresa.nro_documento')

	cuenta_anticipo= fields.Many2one('account.account','Cuenta de Anticipo')
	cuenta_caja= fields.Many2one('account.account','Cuenta de Caja')
	fecha_vencimiento = fields.Date('Fecha Vencimiento')

	period_id = fields.Many2one('account.period','Periodo')
	move_id = fields.Many2one('account.move','Asiento')

	## campo auxiliar para filtrar los partners de forma dinámica en funcion al tipo de usuario(cliente o proveedor)
	#es necesario que por defecto 'tipo' y 'aux_type' se inicialicen por igual('customer' en este caso)
	aux_type = fields.Char(default='customer', string='auxiliar')

	@api.onchange('tipo')
	def onchange_type_partner(self):
		print('tipo: ', self.tipo)
		if self.tipo == 'cliente':
			self.aux_type = 'customer'
			return
		if self.tipo == 'proveedor':
			self.aux_type = 'supplier'
			return
		else:
			self.aux_type = 'active'


	@api.onchange('comprobante_caja')
	def onchange_comprobante_caja(self):
		self.comprobante_anticipo = self.comprobante_caja

	@api.onchange('fecha')
	def onchange_fecha(self):
		self.fecha_vencimiento = self.fecha

	@api.onchange('tipo','metodo_pago')
	def onchange_tipo_metodo_pago(self):
		parameter_id = self.env['main.parameter'].search([])[0]
		if self.tipo and self.metodo_pago.id:
			self.cuenta_caja = self.metodo_pago.default_debit_account_id.id
			if self.metodo_pago.currency_id.id:
				if self.tipo == 'cliente':
					self.cuenta_anticipo = parameter_id.account_anticipo_clientes_me.id
				else:
					self.cuenta_anticipo = parameter_id.account_anticipo_proveedor_me.id
			else:
				if self.tipo == 'cliente':
					self.cuenta_anticipo = parameter_id.account_anticipo_clientes_mn.id
				else:
					self.cuenta_anticipo = parameter_id.account_anticipo_proveedor_mn.id


	@api.one
	def write(self,vals):
		fechita = None

		if 'fecha' in vals:
			fechita = vals['fecha']
		else:
			fechita = self.fecha

		periodo = self.env['account.period'].search([('code','=', str( fechita[5:7])+'/'+ str( fechita[:4])  )])
		if not periodo:
			raise osv.except_osv('Alerta!','No existe el periodo para esta fecha.')
		vals['period_id'] = periodo.id
		return super(anticipo_proveedor,self).write(vals)

	@api.model
	def create(self,vals):
		if 'fecha' in vals:
			periodo = self.env['account.period'].search([('code','=', str(vals['fecha'][5:7])+'/'+ str(vals['fecha'][:4])  )])
			if not periodo:
				raise osv.except_osv('Alerta!','No existe el periodo para esta fecha.')
			vals['period_id'] = periodo.id

		t = super(anticipo_proveedor,self).create(vals)
		if self.env['main.parameter'].search([])[0].sequence_anticipo_proveedor.id:
			secuencia_name = self.env['main.parameter'].search([])[0].sequence_anticipo_proveedor.next_by_id( )
			t.name = secuencia_name
		else:
			raise osv.except_osv('Alerta!', 'Falta consigurar la secuencia para el Anticipo Proveedor')
		return t


	@api.multi
	def entregar_button(self):
		l1 = l2 = {}
		tipo_doc = self.env['einvoice.catalog.01'].search([('code','=','00')])
		if len(tipo_doc)==0:
			raise osv.except_osv('Alerta!','No existe tipo de documento "00"')
		if self.metodo_pago.currency_id.id:
			if not len(self.env['res.currency.rate'].search([('name','=',self.fecha),('currency_id','=',self.metodo_pago.currency_id.id)])) >0:
				raise osv.except_osv('Alerta!','No existe tipo de cambio para la fecha colocada')
			tipo_cambio = self.env['res.currency.rate'].search([('name','=',self.fecha),('currency_id','=',self.metodo_pago.currency_id.id)])[0].type_sale

			
			l1 = {
				'name': self.memoria,
				'debit': float( "%0.2f"%(self.monto * tipo_cambio)),
				'credit': 0,
				'nro_comprobante': self.comprobante_anticipo,
				'account_id': self.cuenta_anticipo.id,
				'partner_id': self.empresa.id,
				'date': self.fecha,
				'date_maturity': self.fecha_vencimiento,
				'currency_id': self.metodo_pago.currency_id.id,
				'amount_currency': float( "%0.2f"%self.monto),
				'tc': tipo_cambio,
				'type_document_it': tipo_doc[0].id,
			}

			l2 = {
				'name': self.memoria,
				'debit': 0,
				'credit': float( "%0.2f"%(self.monto * tipo_cambio)),
				'nro_comprobante': self.comprobante_caja,
				'account_id': self.cuenta_caja.id,
				'partner_id': self.empresa.id,
				'date': self.fecha,
				'date_maturity': self.fecha_vencimiento,
				'currency_id': self.metodo_pago.currency_id.id,
				'amount_currency': float( "%0.2f"%(-self.monto)),
				'tc': tipo_cambio,
				'fefectivo_id':self.flujo_efectivo.id,
				'means_payment_id': self.medio_pago.id,
			}
		else:
			l1 = {
				'name': self.memoria,
				'debit': float( "%0.2f"%(self.monto )),
				'credit': 0,
				'nro_comprobante': self.comprobante_anticipo,
				'account_id': self.cuenta_anticipo.id,
				'partner_id': self.empresa.id,
				'date': self.fecha,
				'date_maturity': self.fecha_vencimiento,
				'type_document_it': tipo_doc[0].id,
			}

			l2 = {
				'name': self.memoria,
				'debit': 0,
				'credit': float( "%0.2f"%(self.monto )),
				'nro_comprobante': self.comprobante_caja,
				'account_id': self.cuenta_caja.id,
				'partner_id': self.empresa.id,
				'date': self.fecha,
				'date_maturity': self.fecha_vencimiento,
				'fefectivo_id':self.flujo_efectivo.id,
				'means_payment_id': self.medio_pago.id,
			}

		periodo = self.env['account.period'].search([('code','=', str(self.fecha[5:7])+'/'+ str(self.fecha[:4])  )])
		if not periodo:
			raise osv.except_osv('Alerta!','No existe el periodo para esta fecha.')

		move = self.env['account.move'].create({
			'ref': 'Anticipo a Proveedor',
			'line_ids': [(0, 0, l2), (0, 0, l1)],
			'journal_id': self.metodo_pago.id,
			'date': self.fecha,
			#'state': 'posted'
		})

		move.post() ## contabilizamos el move

		self.move_id = move
		self.state='done'



	@api.multi
	def cancelar_button(self):
		if self.move_id.id:
			raise osv.except_osv('Alerta!','Debe eliminar primero el asiento contable de este anticipo.')
		else:
			self.state='cancel'
			if self.move_id.state=='posted':
				self.move_id.button_cancel()

			self.move_id.unlink()


	@api.multi
	def borrador_button(self):
		if self.move_id.id:
			raise osv.except_osv('Alerta!','Debe eliminar primero el asiento contable de este anticipo.')
		else:
			self.state='draft'



class main_parameter(models.Model):
	_inherit = 'main.parameter'

	sequence_anticipo_proveedor = fields.Many2one('ir.sequence','Secuencia de Anticipo Proveedor')

