# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_sale_register(models.Model):
	_name = 'account.sale.register'
	_auto = False
	_order = 'periodo,voucher'
	
	libro= fields.Char('Libro', size=50)
	periodo= fields.Char('Periodo', size=50)
	voucher= fields.Char('Voucher', size=50)
	fechaemision = fields.Date('Fecha Emisión')
	fechavencimiento = fields.Date('Fecha Vencimiento')
	tipodocumento = fields.Char('T.D.', size=50)
	serie = fields.Char('Serie', size=50)
	numero = fields.Char('Numero', size=50)
	tipodoc = fields.Char('T.D.P.', size=50)
	numdoc = fields.Char('Num. Documento', size=50)
	partner = fields.Char('Razon Social', size=50)
	valorexp  = fields.Float('Valor Exp.', digits=(12,2))
	baseimp  = fields.Float('Base Imp.', digits=(12,2))
	inafecto  = fields.Float('Inafecto', digits=(12,2))
	exonerado  = fields.Float('Exonerado', digits=(12,2))
	isc  = fields.Float('I.S.C.', digits=(12,2))
	igv  = fields.Float('I.G.V.', digits=(12,2))
	otros  = fields.Float('Otros', digits=(12,2))
	total  = fields.Float('Total', digits=(12,2))
	divisa= fields.Char('Divisa', size=50)
	tipodecambio = fields.Float('T.C.', digits=(12,3))
	tipodocmod = fields.Char('T/D', size=50)
	seriemod = fields.Char('Serie', size=50)
	numeromod = fields.Char('Numero', size=50)
	glosa = fields.Char('Glosa', size=20)
	
	fechadm = fields.Date('Fecha Documento Modificar')
	fechad = fields.Date('Fecha Documento')
	numeromodd = fields.Char('Numero Documento', size=50)

	nogravado = fields.Float('No Gravado',compute="get_nogravado")


	@api.one
	def get_nogravado(self):
		self.nogravado = self.valorexp + self.inafecto + self.exonerado + self.otros


	'''
	def init(self,cr):
		cr.execute("""
			create or replace view account_sale_register as (


	select * from vst_reg_ventas_1_1_1


						)""")
	'''
