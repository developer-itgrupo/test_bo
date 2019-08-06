# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import base64
from openerp.osv import osv
from datetime import *
from decimal import *

class account_rendicion_it(models.Model):
	_inherit = 'account.rendicion.it'

	#name = fields.Char('Nombre',default='/')
	fecha = fields.Date('Fecha de Entrega')
	empleado = fields.Many2one('res.partner','Empleado')
	monto = fields.Float('Monto Entregado')
	caja_entrega = fields.Many2one('account.journal','Caja de Entrega',domain=[('type','in',('cash','bank'))])
	medio_pago = fields.Many2one('einvoice.means.payment','Medio de Pago')
	nro_comprobante = fields.Char('Nro. Comprobante',size=12)
	memoria = fields.Char('Memoria')
	referencia = fields.Char('Referencia')
	fecha_rendicion = fields.Date('Fecha Rendición')
	monto_entregado = fields.Float('Monto Entregado',compute="get_monto_entregado")
	monto_rendido = fields.Float('Monto Rendido',compute="get_monto_rendido")
	saldo = fields.Float('Saldo',compute="get_saldo")
	state = fields.Selection([('draft','Borrador'),('entregado','Entregado'),('rendido','Rendido'),('cancel','Cancelado')],'Estado',default='draft')
	asiento1 = fields.Many2one('account.move','Asiento Entrega')
	asiento2 = fields.Many2one('account.move','Asiento Rendición')
	tc_personalizado = fields.Float('T.C. Personalizado',digits=(12,3))	
	tc_oficial = fields.Float('T.C. Oficial',digits=(12,3), compute="get_tc_oficial")

	es_caja = fields.Boolean(related='caja_entrega.is_small_cash')
	
	small_cash = fields.Many2one('small.cash.another','Caja Chica')

	def get_tc(self,line):
		importe_usd = 0
		if self.caja_entrega.currency_id.name == 'USD':
			if line.tc:
				importe_usd = float(Decimal(str(line.debit/line.tc)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
			else:
				hoy = datetime.strptime(datetime.now(),"%Y-%m-%d")
				tc = self.env['res.currency.rate'].search([('name','=',hoy)])
				tc_cuota = 0
				if not tc:
					tc_cuota = 1
				else:
					tc_cuota = 1/tc.rate
				importe_usd = float(Decimal(str(line.debit/tc_cuota)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))	
		else:
			importe_usd = 0
		return importe_usd

	@api.multi
	def excel(self):		
		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		workbook = Workbook( direccion + 'tempo_rendicion.xlsx')
		worksheet = workbook.add_worksheet("Rendicion")
		bold = workbook.add_format({'bold': True})
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_text_wrap()
		boldbord.set_font_size(9)
		boldbord.set_bg_color('#DCE6F1')
		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		bord = workbook.add_format()
		bord.set_border(style=1)
		numberdos.set_border(style=1)
		numbertres.set_border(style=1)			
		x= 5				
		tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tam_letra = 1
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		worksheet.write(0,0, "RENDICION:"  + self.name, bold)
		
		worksheet.write(1,0, 'Responsable:', normal)
		
		worksheet.write(1,1, self.empleado.name, normal)

		worksheet.write(1,5, 'Caja que Entrega:', normal)
		
		worksheet.write(1,6, self.caja_entrega.name, normal)

		worksheet.write(2,5, u'Fecha Rendición:', normal)
		
		worksheet.write(2,6, self.fecha, normal)
		


		worksheet.write(4,0, "Fecha",boldbord)
		worksheet.write(4,1, "Nro. Comprobante",boldbord)
		worksheet.write(4,2, "RUC/DNI",boldbord)
		worksheet.write(4,3, "Partner",boldbord)
		worksheet.write(4,4, "Importe Dolares",boldbord)
		worksheet.write(4,5, u"Entrega",boldbord)
		worksheet.write(4,6, u"Rendición",boldbord)
		worksheet.write(4,7, "Saldo",boldbord)
		worksheet.write(4,8, "Glosa",boldbord)


		param = self.env['main.parameter'].search([])[0]
		saldo = 0
		report_data = []
		account = param.deliver_account_me.id if self.caja_entrega.currency_id.name == 'USD' else param.deliver_account_mn.id
		if self.asiento2.line_ids[1].debit > 0:
			if self.asiento2.id:
				line = False

				for w in self.asiento2.line_ids:
					if w.debit != 0:
						line = w
				row = {}
				row['fecha'] = line.move_id.date if line.move_id.date else ''
				row['nro'] = line.nro_comprobante if line.nro_comprobante  else ''
				row['ruc'] = line.partner_id.nro_documento if line.partner_id.nro_documento else ''
				row['partner'] = line.partner_id.name if line.partner_id.name else ''
				row['usd'] = self.get_tc(line)
				row['debit'] = line.debit
				row['credit'] = line.credit
				row['glosa'] = line.name if line.name else ''
				row['id'] = 'entrega'
				report_data.append(row)

		lines = self.env['account.move.line'].search([('rendicion_id','=',self.id),('account_id','=',account)])
		if lines:
			for line in lines:
				if line.debit > 0:
					row = {}
					row['fecha'] = line.move_id.date if line.move_id.date else ''
					row['nro'] = line.nro_comprobante if line.nro_comprobante  else ''
					row['ruc'] = line.partner_id.nro_documento if line.partner_id.nro_documento else ''
					row['partner'] = line.partner_id.name if line.partner_id.name else ''
					row['usd'] = self.get_tc(line)
					row['debit'] = line.debit
					row['credit'] = line.credit
					row['glosa'] = line.name if line.name else ''
					row['id'] = 'entrega' 
					report_data.append(row)

		moves = self.env['account.move'].search([('rendicion_id','=',self.id),('state','!=','draft')])
		for move in moves:
			for line in move.line_ids:
				if line.account_id.id != account:
					if line.debit > 0:
						row = {}
						row['fecha'] = line.move_id.date if line.move_id.date else ''
						row['nro'] = line.nro_comprobante if line.nro_comprobante  else ''
						row['ruc'] = line.partner_id.nro_documento if line.partner_id.nro_documento else ''
						row['partner'] = line.partner_id.name if line.partner_id.name else ''
						row['usd'] = self.get_tc(line)
						row['debit'] = line.credit
						row['credit'] = line.debit
						row['glosa'] = line.name if line.name else ''
						row['id'] = 'rendicion'
						report_data.append(row)

		report_data = sorted(report_data,key = lambda i:i['fecha'])
		
		for i in report_data:
			if i['id'] == 'entrega':
				saldo += i['debit'] - i['credit']
			else:
				saldo += i['debit'] - i['credit']
			worksheet.write(x,0,i['fecha'],bord )
			worksheet.write(x,1,i['nro'],bord )
			worksheet.write(x,2,i['ruc'],bord)
			worksheet.write(x,3,i['partner'],bord)
			worksheet.write(x,4,i['usd'],numberdos)
			worksheet.write(x,5,i['debit'],numberdos)
			worksheet.write(x,6,i['credit'],numberdos)
			worksheet.write(x,7,saldo ,numberdos)
			worksheet.write(x,8,i['glosa'],bord)
			x = x +1

		tam_col = [16.5,7.29,12,7,36,32,11,11,11,9,11,11,14,8,16,16,36,16,16,9]

		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])
		worksheet.set_column('H:H', tam_col[7])
		worksheet.set_column('I:I', tam_col[8])
		worksheet.set_column('J:J', tam_col[9])
		worksheet.set_column('K:K', tam_col[10])
		worksheet.set_column('L:L', tam_col[11])
		worksheet.set_column('M:M', tam_col[12])
		worksheet.set_column('N:N', tam_col[13])
		worksheet.set_column('O:O', tam_col[14])
		worksheet.set_column('P:P', tam_col[15])
		worksheet.set_column('Q:Q', tam_col[16])
		worksheet.set_column('R:R', tam_col[17])
		worksheet.set_column('S:S', tam_col[18])
		worksheet.set_column('T:T', tam_col[19])

		workbook.close()
		
		f = open(direccion + 'tempo_rendicion.xlsx', 'rb')
		
		
		vals = {
			'output_name': 'Rendicion.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		sfs_id = self.env['export.file.save'].create(vals)
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}


	@api.one
	def cancelar(self):
		if self.asiento1.id:			
			if self.asiento1.state!= 'draft':
				self.asiento1.button_cancel()
			self.asiento1.unlink()

		if self.asiento2.id:			
			if self.asiento2.state!= 'draft':
				self.asiento2.button_cancel()
			self.asiento2.unlink()

		self.state = 'cancel'

	@api.one
	def borrador(self):
		self.state = 'draft'

	@api.onchange('fecha')
	def onchange_fecha(self):
		tmp = 0

		if self.fecha:
			self.env.cr.execute(""" select type_sale from res_currency_rate rcr 
				inner join res_currency rc on rc.id = rcr.currency_id
				where rcr.name = '""" +self.fecha+ """' and rc.name = 'USD'
			  """)
			for i in self.env.cr.fetchall():
				tmp = i[0]

		self.tc_oficial = tmp


	@api.one
	def get_tc_oficial(self):
		tmp = 0

		if self.fecha:
			self.env.cr.execute(""" select type_sale from res_currency_rate rcr 
				inner join res_currency rc on rc.id = rcr.currency_id
				where rcr.name = '""" +self.fecha+ """' and rc.name = 'USD'
			  """)
			for i in self.env.cr.fetchall():
				tmp = i[0]

		self.tc_oficial = tmp


	@api.onchange('fecha_rendicion')
	def onchange_fecha_rendicion(self):
		tmp = 0

		if self.fecha_rendicion:
			self.env.cr.execute(""" select type_sale from res_currency_rate rcr 
				inner join res_currency rc on rc.id = rcr.currency_id
				where rcr.name = '""" +self.fecha_rendicion+ """' and rc.name = 'USD'
			  """)
			for i in self.env.cr.fetchall():
				tmp = i[0]

		self.tc_oficial2 = tmp



	@api.one
	def get_saldo(self):
		self.saldo =( ( (self.monto_entregado * self.tc_personalizado) if self.tc_personalizado else (self.monto_entregado * self.tc_oficial) ) if self.caja_entrega.currency_id.name == 'USD' else self.monto_entregado ) - self.monto_rendido

	@api.one
	def get_monto_rendido(self):
		param = self.env['main.parameter'].search([])[0]
		moves = self.env['account.move'].search([('rendicion_id','=',self.id),('state','!=','draft')])
		account = param.deliver_account_me.id if self.caja_entrega.currency_id.name == 'USD' else param.deliver_account_mn.id
		tot = 0
		for move in moves:
			for line in move.line_ids:
				if line.account_id.id == account:
					tot += line.credit
		self.monto_rendido = tot

	@api.one
	def get_monto_entregado(self):
		param = self.env['main.parameter'].search([])[0]
		tot = 0
		if not param.deliver_account_me:
			raise osv.except_osv('Error!', u'Debe Configurarse las cuentas de Rendicion en Parametros.')

		if not param.deliver_account_mn:
			raise osv.except_osv('Error!', u'Debe Configurarse las cuentas de Rendicion en Parametros.')
		lineas = self.env['account.move.line'].search([('rendicion_id','=',self.id)])
		for i in lineas:
			if i.account_id.id == (param.deliver_account_me.id if self.caja_entrega.currency_id.name == 'USD' else param.deliver_account_mn.id) and i.debit > 0:
				tot += i.debit

		tc = self.tc_oficial
		if self.tc_personalizado:
			tc = self.tc_personalizado

		self.monto_entregado = (tot+self.monto) * tc if self.caja_entrega.currency_id.name == 'USD' else (tot+self.monto) 


	@api.one
	def entrega(self):

		id_seq = self.env['ir.sequence'].search([('name','=','Seq. Rendicion')])
		if len(id_seq)>0:
			id_seq = id_seq[0]
		else:
			id_seq = self.env['ir.sequence'].create({'name':'Seq. Rendicion','implementation':'standard','active':True,'prefix':'REND-','padding':4,'number_increment':1,'number_next_actual' :1})
		if self.name == '/':
			self.write({'name': id_seq.next_by_id()})


		tc = self.tc_oficial
		if self.tc_personalizado:
			tc = self.tc_personalizado

		param_conf = self.env['res.company'].search([])[0]

		linea1 = (0,0,{
			'account_id':self.caja_entrega.default_debit_account_id.id,
			'partner_id':self.empleado.id,
			'nro_comprobante':self.name,
			'name':self.memoria,
			'currency_id':self.caja_entrega.currency_id.id if self.caja_entrega.currency_id.name == 'USD' else 0,
			'amount_currency':-self.monto if self.caja_entrega.currency_id.name == 'USD' else 0,
			'debit':0,
			'credit':self.monto * tc if self.caja_entrega.currency_id.name == 'USD' else self.monto,
			'date_maturity':self.fecha,
			'tc':tc,
		})


		linea2 = (0,0,{
			'account_id':param_conf.transfer_account_id.id,
			'partner_id':self.empleado.id,
			'nro_comprobante':self.name,
			'name':self.memoria,
			'currency_id':self.caja_entrega.currency_id.id if self.caja_entrega.currency_id else 0,
			'amount_currency':0,
			'debit':self.monto * tc if self.caja_entrega.currency_id.name == 'USD' else self.monto,
			'credit':0,
			'date_maturity':self.fecha,
			'tc':tc,
		})

		lineas=[linea1,linea2]

		data = {
			'journal_id':self.caja_entrega.id,
			'date':self.fecha,
			'ref':self.name,
			'means_payment_it':self.medio_pago.id,
			'line_ids':lineas,
		}
		a1 = self.env['account.move'].create(data)

		self.asiento1 = a1.id


		if self.caja_entrega.is_small_cash:
			self.asiento1.small_cash_id = self.small_cash.id
		if a1.state == 'draft':
			a1.post()

		self.rendido()
		self.state = 'entregado'


	@api.one
	def rendir_state(self):
		self.state = 'rendido'


	@api.one
	def rendido(self):
		tc = self.tc_oficial
		if self.tc_personalizado:
			tc = self.tc_personalizado
		param = self.env['main.parameter'].search([])[0]

		param_conf = self.env['res.company'].search([])[0]

		if not param.deliver_account_me:
			raise osv.except_osv('Error!', u'Debe Configurarse las cuentas de Rendicion en Parametros.')

		if not param.deliver_account_mn:
			raise osv.except_osv('Error!', u'Debe Configurarse las cuentas de Rendicion en Parametros.')

		
		if not param.loan_journal_mn:
			raise osv.except_osv('Error!', u'Debe Configurarse las cuentas de Rendicion en Parametros.')

		
		if not param.loan_journal_me:
			raise osv.except_osv('Error!', u'Debe Configurarse las cuentas de Rendicion en Parametros.')

		if not (param.loan_journal_me if self.caja_entrega.currency_id.name == 'USD' else param.loan_journal_mn).default_debit_account_id.id:
			raise osv.except_osv('Error!', u'Debe Configurarse las cuentas por defecto de los Diarios Rendicion.')			

		linea1 = (0,0,{
			'account_id': (param.loan_journal_me if self.caja_entrega.currency_id.name == 'USD' else param.loan_journal_mn).default_debit_account_id.id,
			'partner_id':self.empleado.id,
			'nro_comprobante':self.name,
			'name':self.memoria,
			'currency_id':self.caja_entrega.currency_id.id if self.caja_entrega.currency_id.name == 'USD' else 0,
			'amount_currency':self.monto if self.caja_entrega.currency_id.name == 'USD' else 0,
			'rendicion_id':self.id,
			'debit':self.monto * tc if self.caja_entrega.currency_id.name == 'USD' else self.monto,
			'credit':0,
			'date_maturity':self.fecha,
			'tc':tc,
		})


		linea2 = (0,0,{
			'account_id':param_conf.transfer_account_id.id,
			'partner_id':self.empleado.id,
			'nro_comprobante':self.name,
			'name':self.memoria,
			'currency_id':self.caja_entrega.currency_id.id if self.caja_entrega.currency_id else 0,
			'amount_currency':0,
			'rendicion_id':self.id,
			'debit':0,
			'credit':self.monto * tc if self.caja_entrega.currency_id.name == 'USD' else self.monto,
			'date_maturity':self.fecha,
			'tc':tc,
		})

		lineas=[linea1,linea2]

		data = {
			'journal_id':param.loan_journal_me.id if self.caja_entrega.currency_id.name == 'USD' else param.loan_journal_mn.id,
			'date':self.fecha,
			'ref':self.name,
			'means_payment_it':self.medio_pago.id,
			'line_ids':lineas,
		}
		a1 = self.env['account.move'].create(data)

		self.asiento2 = a1.id

		if a1.state == 'draft':
			a1.post()
