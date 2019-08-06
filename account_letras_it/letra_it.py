# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _
from odoo.exceptions import UserError
import datetime

class main_parameter(models.Model):
	_inherit='main.parameter'

	cuenta_letras_fcliente_mn = fields.Many2one('account.account','Cuenta Factura Cliente MN')
	cuenta_letras_fcliente_me = fields.Many2one('account.account','Cuenta Factura Cliente ME')
	cuenta_letras_lcliente_mn = fields.Many2one('account.account','Cuenta Letra Cliente MN')
	cuenta_letras_lcliente_me = fields.Many2one('account.account','Cuenta Letra Cliente ME')
	cuenta_letras_fproveedor_mn = fields.Many2one('account.account','Cuenta Factura Proveedor MN')
	cuenta_letras_fproveedor_me = fields.Many2one('account.account','Cuenta Factura Proveedor ME')
	cuenta_letras_lproveedor_mn = fields.Many2one('account.account','Cuenta Letra Proveedor MN')
	cuenta_letras_lproveedor_me = fields.Many2one('account.account','Cuenta Letra Proveedor ME')

	cuenta_ganancia_redondeo = fields.Many2one('account.account','Cuenta Ganacia por Redondeo')
	cuenta_perdida_redondeo = fields.Many2one('account.account','Cuenta Perdida por Redondeo')


class account_payment_term(models.Model):
	_inherit = 'account.payment.term'

	tipo_aplicacion = fields.Selection([('pagar','Aplicable Cuentas por Pagar'),('cobrar',' Aplicable Cuentas por Cobrar')])

class account_payment_term_line(models.Model):
    _inherit = "account.payment.term.line"

    account_id = fields.Many2one('account.account','Cuenta')


class account_letras_payment_factura(models.Model):
	_name = 'account.letras.payment.factura'

	tipo_doc = fields.Many2one('einvoice.catalog.01','Tipo de Documento')
	nro_comprobante = fields.Char('Nro de Comprobante')
	cuenta = fields.Many2one('account.account','Cuenta Contable')
	divisa = fields.Many2one('res.currency','Divisa')
	currency_id = fields.Many2one('res.currency','Moneda')
	monto_divisa = fields.Float('Monto Divisa',digits=(12,2))
	tipo_cambio = fields.Float('Tipo de Cambio',digits=(12,3),compute="get_tipo_cambio")
	monto = fields.Float('Monto',digits=(12,2),compute="get_monto")
	letra_payment_id = fields.Many2one('account.letras.payment','Pago')
	invoice_id = fields.Many2one('account.invoice','Factura')
	rest = fields.Float('Saldo',digits=(12,2))

	@api.model
	def create(self,vals):
		if 'invoice_id' in vals:
			invoice = self.env['account.invoice'].browse(vals['invoice_id'])
			vals['currency_id'] = invoice.currency_id.id
		t = super(account_letras_payment_factura,self).create(vals)
		return t

	@api.one
	def write(self,vals):
		if 'invoice_id' in vals:
			invoice = self.env['account.invoice'].browse(vals['invoice_id'])
			vals['currency_id'] = invoice.currency_id.id
		t = super(account_letras_payment_factura,self).write(vals)
		return t





	@api.one
	def get_monto(self):
		self.monto = self.monto_divisa * self.tipo_cambio

	@api.one
	def get_tipo_cambio(self):
		self.tipo_cambio = 1
		if self.divisa.id:
			divisa_line = self.env['res.currency.rate'].search([('currency_id','=',self.divisa.id),('name','=',self.letra_payment_id.fecha_canje)])
			if len(divisa_line)>0:
				self.tipo_cambio = 1 / divisa_line[0].rate 

	@api.onchange('invoice_id')
	def onchange_invoice_id(self):
		self.nro_comprobante=self.invoice_id.reference
		self.tipo_doc = self.invoice_id.it_type_document.id
		if self.invoice_id.currency_id.name != 'PEN':
			self.divisa = self.invoice_id.currency_id.id
		else:
			self.divisa = False
			
		self.monto_divisa = 0
		self.cuenta = self.invoice_id.account_id.id
		self.rest =  self.invoice_id.residual
		self.currency_id = self.invoice_id.currency_id.id

		if self.invoice_id.reference:
			self.env.cr.execute("""

			select row_number() OVER () AS id,* from
			(
				select 
				ap.name as periodo,
				am.date as fecha_emision,
				--facturas.date_due as fecha_venci,
				f_final.fin as fecha_venci,
				rp.nro_documento as ruc,
				rp.name as empresa,
				CASE WHEN aat.type= 'payable' THEN 'A pagar'  ELSE 'A cobrar' END as tipo_cuenta,
				aa.code,
				itd.code as tipo,
				TRIM(aml.nro_comprobante) as nro_comprobante,
				T.debe,
				T.haber,				
				CASE WHEN abs(T.saldo) < 0.01 then 0 else T.saldo end as saldo,
				rc.name as divisa,
				T.amount_currency,
				am.name as voucher,
				T.aml_ids
				from (
				select concat(account_move_line.partner_id,'-',account_id,'-',type_document_it,'-',TRIM(nro_comprobante) ) as identifica,min(account_move_line.id),sum(debit)as debe,sum(credit) as haber, sum( CASE WHEN aat.type='receivable' then debit-credit else credit-debit end) as saldo, sum(amount_currency) as amount_currency, array_agg(account_move_line.id) as aml_ids from account_move_line
				inner join account_move ami on ami.id = account_move_line.move_id
				inner JOIN account_period api ON api.date_start <= ami.fecha_contable and api.date_stop >= ami.fecha_contable  and api.special = ami.fecha_special

				left join account_account on account_account.id=account_move_line.account_id
				left join account_account_type aat on aat.id = account_account.user_type_id
				where --account_account.reconcile = true and 
				(aat.type='receivable' or aat.type='payable' ) and ami.state != 'draft'
				and nro_comprobante = '""" +str(self.invoice_id.reference)+ """'
				
				group by identifica) as T
				inner join account_move_line aml on aml.id = T.min
				inner join account_move am on am.id = aml.move_id
				inner JOIN account_period ap ON ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable  and ap.special = am.fecha_special
				left join (
select concat(aml.partner_id,'-',aml.account_id,'-',aml.type_document_it,'-',TRIM(aml.nro_comprobante) )as ide, max(aml.date_maturity) as fin, am.id from
account_move am 
inner join account_move_line aml on aml.move_id = am.id 
where aml.nro_comprobante = '""" +str(self.invoice_id.reference)+ """'
group by am.id,concat(aml.partner_id,'-',aml.account_id,'-',aml.type_document_it,'-',TRIM(aml.nro_comprobante) )
) as f_final on f_final.ide = T.identifica and am.id = f_final.id

				left join res_partner rp on rp.id = aml.partner_id
				left join einvoice_catalog_01 itd on itd.id = aml.type_document_it
				left join res_currency rc on rc.id = aml.currency_id
				left join account_account aa on aa.id = aml.account_id
				left join account_account_type aat on aat.id = aa.user_type_id
				left join (select concat(partner_id,account_id,it_type_document,TRIM(reference) ) as identifica,date,date_due from account_invoice) facturas on facturas.identifica=t.identifica
				order by empresa, code, nro_comprobante
				) T where nro_comprobante = '""" +str(self.invoice_id.reference)+ """'

			 """)

			lineas = self.env.cr.dictfetchall()
			linea = lineas[0]
			if self.invoice_id.currency_id.name != 'PEN':
				self.rest =  linea['amount_currency']
			else:
				self.rest =  linea['saldo']

	# @api.onchange('nro_comprobante','tipo_doc')
	# def onchange_suplier_invoice_number_it(self):
	# 	if self.nro_comprobante:
	# 		self.nro_comprobante = str(self.nro_comprobante).replace(' ','')
			
	# 		if self.nro_comprobante and self.tipo_doc.id:
	# 			self.nro_comprobante = str(self.nro_comprobante).replace(' ','')
	# 			t = self.nro_comprobante.split('-')
	# 			n_serie = 0
	# 			n_documento = 0
	# 			self.env.cr.execute("select coalesce(n_serie,0), coalesce(n_documento,0) from einvoice_catalog_01 where id = "+ str(self.tipo_doc.id))
				
	# 			forelemn = self.env.cr.fetchall()
	# 			for ielem in forelemn:
	# 				n_serie = ielem[0]
	# 				n_documento = ielem[1]
	# 			if len(t) == 2:
	# 				parte1= t[0]
	# 				if len(t[0]) < n_serie:
	# 					for i in range(0,n_serie-len(t[0])):
	# 						parte1 = '0'+parte1
	# 				parte2= t[1]
	# 				if len(t[1]) < n_documento:
	# 					for i in range(0,n_documento-len(t[1])):
	# 						parte2 = '0'+parte2
	# 				self.nro_comprobante = parte1 + '-' + parte2
	# 			elif len(t) == 1:
	# 				parte2= t[0]
	# 				if len(t[0]) < n_documento:
	# 					for i in range(0,n_documento-len(t[0])):
	# 						parte2 = '0'+parte2
	# 				self.nro_comprobante = parte2
	# 			else:
	# 				pass


class account_letras_payment_letra(models.Model):
	_name = 'account.letras.payment.letra'

	payment_line_id = fields.Many2one('account.payment.term.line','Payment Line')
	tipo_vencimiento = fields.Selection(related='payment_line_id.value')
	porcentaje = fields.Float(related='payment_line_id.value_amount')
	nro_dias = fields.Integer(related='payment_line_id.days')
	cuenta = fields.Many2one('account.account','Cuenta',compute="get_cuenta")

	fecha_vencimiento = fields.Date('Fecha Vencimiento')
	monto = fields.Float('Monto',compute="get_monto",digits=(12,2))
	monto_divisa = fields.Float('Monto Divisa',digits=(12,2))
	nro_letra = fields.Char('Nro. de Letra',default='Letra')
	letra_payment_id = fields.Many2one('account.letras.payment','Pago')

	tc = fields.Float('Tipo de Cambio',compute="get_tc",digits=(12,3))

	@api.one
	def get_cuenta(self):
		param = self.env['main.parameter'].search([])[0]

		flag = False

		if self.letra_payment_id.id:
			for i in self.letra_payment_id.factura_ids:
				if i.divisa.id and i.divisa.name == 'USD':
					flag = True

		if self.letra_payment_id.id:
			if self.letra_payment_id.tipo == '1':			
				self.cuenta =  param.cuenta_letras_lcliente_me.id if flag else param.cuenta_letras_lcliente_mn.id
			else:
				self.cuenta =  param.cuenta_letras_lproveedor_me.id if flag else param.cuenta_letras_lproveedor_mn.id
		else:
			self.cuenta = False


	@api.one
	def get_tc(self):
		self.tc = 1
		if self.cuenta.currency_id.id:
			divisa_line = self.env['res.currency.rate'].search([('currency_id','=',self.cuenta.currency_id.id),('name','=',self.letra_payment_id.fecha_canje)])
			if len(divisa_line)>0:
				self.tc = 1 / divisa_line[0].rate 

	@api.one
	def get_monto(self):
		self.monto = self.monto_divisa * self.tc



class account_letras_payment_letra_manual(models.Model):
	_name = 'account.letras.payment.letra.manual'

	cuenta = fields.Many2one('account.account','Cuenta',compute="get_cuenta")
	fecha_vencimiento = fields.Date('Fecha Vencimiento')
	monto = fields.Float('Monto',compute="get_monto",digits=(12,2))
	monto_divisa = fields.Float('Monto Divisa',digits=(12,2))
	nro_letra = fields.Char('Nro. de Letra',default='Letra')
	letra_payment_id = fields.Many2one('account.letras.payment','Pago')

	tc = fields.Float('Tipo de Cambio',compute="get_tc",digits=(12,3))

	@api.one
	def get_cuenta(self):
		param = self.env['main.parameter'].search([])[0]

		flag = False

		if self.letra_payment_id.id:
			for i in self.letra_payment_id.factura_ids:
				if i.divisa.id and i.divisa.name == 'USD':
					flag = True

		if self.letra_payment_id.id:
			if self.letra_payment_id.tipo == '1':			
				self.cuenta =  param.cuenta_letras_lcliente_me.id if flag else param.cuenta_letras_lcliente_mn.id
			else:
				self.cuenta =  param.cuenta_letras_lproveedor_me.id if flag else param.cuenta_letras_lproveedor_mn.id
		else:
			self.cuenta = False

	@api.one
	def get_tc(self):
		self.tc = 1
		if self.cuenta.currency_id.id:
			divisa_line = self.env['res.currency.rate'].search([('currency_id','=',self.cuenta.currency_id.id),('name','=',self.letra_payment_id.fecha_canje)])
			if len(divisa_line)>0:
				self.tc = 1 / divisa_line[0].rate 


	@api.one
	def get_monto(self):
		self.monto = self.monto_divisa * self.tc


class account_letras_payment(models.Model):
	_name = 'account.letras.payment'

	name = fields.Char('Nro. Canje')
	partner_id = fields.Many2one('res.partner','Partner')
	termino_pago_id = fields.Many2one('account.payment.term','Termino de Pago')
	fecha_canje = fields.Date('Fecha Canje')
	glosa = fields.Char('Glosa')
	referencia = fields.Char('Referencia')
	journal_id = fields.Many2one('account.journal','Diario')
	factura_ids = fields.One2many('account.letras.payment.factura','letra_payment_id','Facturas')
	letras_ids = fields.One2many('account.letras.payment.letra','letra_payment_id','Letras')
	letras_manual_ids = fields.One2many('account.letras.payment.letra.manual','letra_payment_id','Letras Manual')
	asiento = fields.Many2one('account.move','Asiento Contable')
	state = fields.Selection([('draft','Borrador'),('done','Finalizado')],'Estado',default='draft')
	usar_termino = fields.Boolean('Usar Termino de Pago',default=False)
	tipo = fields.Selection([('1','Cliente'),('2','Proveedor')],'Tipo',default="1")
	

	total_monto = fields.Float('Total Monto',digits=(12,2),compute="get_total_monto")

	@api.one
	def get_total_monto(self):
		tmp = 0
		for i in self.factura_ids:
			tmp+= i.monto
		self.total_monto = tmp

	@api.multi
	def get_rest_invoice(self):
		now = datetime.datetime.now()
		anio = str(now.year)
		period_1 = '00'+'/'+anio
		period_2 = '12'+'/'+anio

		fiscalyear_id = self.env['account.fiscalyear'].search([('name','=',anio)])[0].id
		
		period_id_1 =  self.env['account.period'].search([('code','=',period_1)])[0].id
		period_id_2 =  self.env['account.period'].search([('code','=',period_2)])[0].id
		cadfact = ''
		for fact in self.factura_ids:
			cadfact= cadfact+fact.nro_comprobante+','
		cadfact = cadfact[:-1]

		vals = {
			'fiscal_id':fiscalyear_id,
			'periodo_ini':period_id_1,
			'periodo_fin':period_id_2,
			'mostrar':  'newwindow',
			'empresa': self.partner_id.id,
			'tipo' : 'A cobrar' if self.tipo == '1' else 'A pagar',
			'comprobantes': cadfact
			}
		reporte = self.env['saldo.comprobante.periodo.wizard'].create(vals)
		c = reporte.do_rebuild()
		return c

		

	@api.multi
	def get_rest_draught(self):
		now = datetime.datetime.now()
		anio = str(now.year)
		period_1 = '00'+'/'+anio
		period_2 = '12'+'/'+anio

		fiscalyear_id = self.env['account.fiscalyear'].search([('name','=',anio)])[0].id
		
		period_id_1 =  self.env['account.period'].search([('code','=',period_1)])[0].id
		period_id_2 =  self.env['account.period'].search([('code','=',period_2)])[0].id
		cadfact = ''
		for fact in self.letras_ids:
			cadfact= cadfact+fact.nro_letra+','
		cadfact = cadfact[:-1]

		vals = {
			'fiscal_id':fiscalyear_id,
			'periodo_ini':period_id_1,
			'periodo_fin':period_id_2,
			'mostrar':  'newwindow',
			'empresa': self.partner_id.id,
			'tipo' : 'A cobrar' if self.tipo == '1' else 'A pagar',
			'comprobantes': cadfact
			}
		reporte = self.env['saldo.comprobante.periodo.wizard'].create(vals)
		c = reporte.do_rebuild()
		return c

	@api.multi
	def get_rest_draught1(self):
		now = datetime.datetime.now()
		anio = str(now.year)
		period_1 = '00'+'/'+anio
		period_2 = '12'+'/'+anio

		fiscalyear_id = self.env['account.fiscalyear'].search([('name','=',anio)])[0].id
		
		period_id_1 =  self.env['account.period'].search([('code','=',period_1)])[0].id
		period_id_2 =  self.env['account.period'].search([('code','=',period_2)])[0].id
		cadfact = ''
		for fact in self.letras_manual_ids:
			cadfact= cadfact+fact.nro_letra+','
		cadfact = cadfact[:-1]

		vals = {
			'fiscal_id':fiscalyear_id,
			'periodo_ini':period_id_1,
			'periodo_fin':period_id_2,
			'mostrar':  'newwindow',
			'empresa': self.partner_id.id,
			'tipo' : 'A cobrar' if self.tipo == '1' else 'A pagar',
			'comprobantes': cadfact
			}
		print vals
		reporte = self.env['saldo.comprobante.periodo.wizard'].create(vals)
		c = reporte.do_rebuild()
		return c


	@api.model
	def create(self,vals):
		id_seq = self.env['ir.sequence'].search([('name','=','Canje de Letra')])
		if len(id_seq)>0:
			id_seq = id_seq[0]
		else:
			id_seq = self.env['ir.sequence'].create({'name':'Canje de Letra','implementation':'standard','active':True,'prefix':'CLT-','padding':4,'number_increment':1,'number_next_actual' :1})
		
		vals['name'] = id_seq.next_by_id()

		t = super(account_letras_payment,self).create(vals)

		total = 0
		for opt in t.factura_ids:
			total += opt.monto

		tt = t.termino_pago_id.with_context(currency_id=self.env['res.currency'].search([('name','=','USD')])[0].id).compute(total, t.fecha_canje)[0]
		tt = sorted(tt)

		cont = 0
		for i in t.termino_pago_id.line_ids:
			if len(tt)>cont:
				data= {
					'payment_line_id':i.id,
					'fecha_vencimiento': tt[cont][0],
					'monto_divisa':tt[cont][1],
					'letra_payment_id':t.id,
				}
				cont += 1
				self.env['account.letras.payment.letra'].create(data)
		return t


	@api.one
	def write(self,vals):
		t = super(account_letras_payment,self).write(vals)
		self.refresh()
		if 'termino_pago_id' in vals:
			for mm in self.letras_ids:
				mm.unlink()
			
			total = 0
			for opt in self.factura_ids:
				total += opt.monto_divisa

			tt = self.termino_pago_id.with_context(currency_id=self.env['res.currency'].search([('name','=','USD')])[0].id).compute(total, self.fecha_canje)[0]
			tt = sorted(tt)
			cont = 0
			for i in self.termino_pago_id.line_ids.sorted(key=lambda r: r.days):
				if len(tt)>cont:
					data= {
						'payment_line_id':i.id,
						'fecha_vencimiento': tt[cont][0],
						'letra_payment_id':self.id,
						'monto_divisa':tt[cont][1],
					}
					cont+=1
					self.env['account.letras.payment.letra'].create(data)
		return t

	@api.one
	def actualizar(self,vals):
		if self.factura_ids:
			currency = self.factura_ids[0].currency_id.id
			for i in self.factura_ids:
				if i.currency_id.id != currency:
					raise UserError('No se puede tener facturas con diferentes tipos de moneda')

		for mm in self.letras_ids:
			mm.unlink()
		
		total = 0
		for opt in self.factura_ids:
			total += opt.monto_divisa

		tt = self.termino_pago_id.with_context(currency_id=self.env['res.currency'].search([('name','=','USD')])[0].id).compute(total, self.fecha_canje)[0]
		tt = sorted(tt)
		cont = 0
		for i in self.termino_pago_id.line_ids.sorted(key=lambda r: r.days):
			if len(tt)>cont:
					
				data= {
					'payment_line_id':i.id,
					'fecha_vencimiento': tt[cont][0],
					'letra_payment_id':self.id,
					'monto_divisa':tt[cont][1],
				}
				cont+=1
				self.env['account.letras.payment.letra'].create(data)


	@api.one
	def crear_asiento(self):
		if not self.asiento.id:
			if self.factura_ids:
				currency = self.factura_ids[0].currency_id.id
				for i in self.factura_ids:
					if i.currency_id.id != currency:
						raise UserError('No se puede tener facturas con diferentes tipos de moneda')
			y_ver = 0
			x_ver = 0
			for oo in self.factura_ids:
				y_ver += oo.monto_divisa

			if self.usar_termino:
				for oo in self.letras_ids:
					x_ver += oo.monto_divisa
			else:
				for oo in self.letras_manual_ids:
					x_ver += oo.monto_divisa

			if abs(float(x_ver) - float(y_ver)) >= 0.01:
				raise UserError( 'Los totales de Factura y Letras no son iguales, por favor Actualizar antes de generar el asiento.' )

			data = {
				'journal_id':self.journal_id.id,
				'date':self.fecha_canje,
				'ref':self.name,
			}

			t = self.env['account.move'].create(data)


			param = self.env['main.parameter'].search([])[0]			
			if self.tipo == '2':

				for i in self.factura_ids:
					di = {
						'move_id':t.id,
						'account_id': i.invoice_id.account_id.id,# param.cuenta_letras_fproveedor_me.id if i.divisa.id else param.cuenta_letras_fproveedor_mn.id,
						'partner_id':self.partner_id.id,
						'type_document_it':i.tipo_doc.id,
						'nro_comprobante':i.nro_comprobante,
						'name':'CANJE DE LETRAS POR FACTURA',
						'amount_currency':i.monto_divisa if i.divisa.id else 0,
						'currency_id':i.divisa.id,
						'debit':i.monto if i.monto >0 else 0,
						'credit':-i.monto if i.monto <0 else 0,
						'date_maturity':False,
						'tc':i.tipo_cambio if i.divisa.id else False,
					}
					ott = self.env['account.move.line'].create(di)
					ids_conciliacion = []
					ids_conciliacion.append(ott.id)

					if i.invoice_id.id:
						for ml in i.invoice_id.move_id.line_ids:
							if ml.account_id.id == ott.account_id.id  and ml.type_document_it.id == ott.type_document_it.id and ml.nro_comprobante == ott.nro_comprobante:
								ids_conciliacion.append(ml.id)
					if len(ids_conciliacion) >1:
						self.env['account.move.line'].browse(ids_conciliacion).reconcile()


				obj_res = self.letras_manual_ids
				if self.usar_termino:
					obj_res = self.letras_ids
					
				for i in obj_res:
					di = {
						'move_id':t.id,
						'account_id':i.cuenta.id,
						'partner_id':self.partner_id.id,
						'type_document_it': self.env['einvoice.catalog.01'].search([('code','=','00')])[0].id,
						'nro_comprobante':i.nro_letra,
						'name':'CANJE DE LETRAS POR FACTURA',
						'amount_currency':-i.monto_divisa if i.cuenta.currency_id.id else 0,
						'currency_id':i.cuenta.currency_id.id,
						'debit':-i.monto if i.monto <0 else 0,
						'credit':i.monto if i.monto >0 else 0,
						'date_maturity':i.fecha_vencimiento,
						'tc':i.tc if i.cuenta.currency_id.id else False,
					}
					self.env['account.move.line'].create(di)

			else:

				for i in self.factura_ids:
					di = {
						'move_id':t.id,
						'account_id':i.invoice_id.account_id.id,#param.cuenta_letras_fcliente_me.id if i.divisa.id else param.cuenta_letras_fcliente_mn.id,
						'partner_id':self.partner_id.id,
						'type_document_it':i.tipo_doc.id,
						'nro_comprobante':i.nro_comprobante,
						'name':'CANJE DE LETRAS POR FACTURA',
						'amount_currency':-i.monto_divisa if i.divisa.id else 0,
						'currency_id':i.divisa.id,
						'debit':-i.monto if i.monto <0 else 0,
						'credit':i.monto if i.monto >0 else 0,
						'date_maturity':False,
						'tc':i.tipo_cambio if i.divisa.id else False,
					}
					ott = self.env['account.move.line'].create(di)
					ids_conciliacion = []
					ids_conciliacion.append(ott.id)

					if i.invoice_id.id:
						for ml in i.invoice_id.move_id.line_ids:
							if ml.account_id.id == ott.account_id.id  and ml.type_document_it.id == ott.type_document_it.id and ml.nro_comprobante == ott.nro_comprobante:
								ids_conciliacion.append(ml.id)
					if len(ids_conciliacion) >1:
						self.env['account.move.line'].browse(ids_conciliacion).reconcile()

				obj_res = self.letras_manual_ids
				if self.usar_termino:
					obj_res = self.letras_ids
					
				for i in obj_res:
					di = {
						'move_id':t.id,
						'account_id':i.cuenta.id,
						'partner_id':self.partner_id.id,
						'type_document_it': self.env['einvoice.catalog.01'].search([('code','=','00')])[0].id,
						'nro_comprobante':i.nro_letra,
						'name':'CANJE DE LETRAS POR FACTURA',
						'amount_currency':i.monto_divisa if i.cuenta.currency_id.id else 0,
						'currency_id':i.cuenta.currency_id.id,
						'debit': i.monto if i.monto >0 else 0,
						'credit':-i.monto if i.monto <0 else 0,
						'date_maturity':i.fecha_vencimiento,
						'tc':i.tc if i.cuenta.currency_id.id else False,
					}
					self.env['account.move.line'].create(di)

			#redondeo
			diferencia = 0
			t.refresh()
			for i in t.line_ids:
				diferencia += round(i.debit,2) - round(i.credit,2)

			if abs(round(diferencia,2)) >= 0.01:
				data = {
					'move_id':t.id,
					'account_id': param.cuenta_ganancia_redondeo.id if diferencia>0 else param.cuenta_perdida_redondeo.id,
					'partner_id':self.partner_id.id,
					'name':'Redondeo',
					'debit': abs(round(diferencia,2)) if diferencia<0 else 0,
					'credit': round(diferencia,2) if diferencia>0 else 0,
				}
				self.env['account.move.line'].create(data)
			t.post()
			self.asiento = t.id
			self.state = 'done'

	@api.one
	def cancelar(self):
		if self.asiento.id:
			if self.asiento.state =='draft':
				pass
			else:
				for mm in self.asiento.line_ids:
					mm.remove_move_reconcile()
				self.asiento.button_cancel()
			self.asiento.unlink()
		self.state = 'draft'