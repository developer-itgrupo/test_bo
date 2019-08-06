# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_forth_category(models.Model):
	_name = 'account.forth.category'
	_auto = False
	#statefiltro = fields.Char('StateFiltro',size=50)
	periodo= fields.Char('Periodo', size=50)
	libro= fields.Char('Libro', size=50)
	voucher= fields.Char('Voucher', size=50)
	fechaemision = fields.Date('Fecha Emisión')
	fechapago = fields.Date('Fecha Pago')
	tipodocumento = fields.Char('T.C.', size=50)
	serie = fields.Char('Serie', size=50)
	numero = fields.Char('Numero', size=50)
	tipodoc = fields.Char('T.D.P.', size=50)
	numdoc = fields.Char('Num. Documento', size=50)
	partner = fields.Char('Razon Social', size=50)
	divisa = fields.Char('Divisa', size=50)
	tipodecambio = fields.Float('Tip. Cambio', digits=(12,3))
	monto  = fields.Float('Monto', digits=(12,2))
	retencion  = fields.Float('Retencion', digits=(12,2))
	neto  = fields.Float('Neto Pagado', digits=(12,2))
	state = fields.Selection([('draft','Borrador'),('proforma','Pro-forma'),('proforma2','Pro-forma'),('open','Abierto/a'),('paid','Pagado'),('cancel','Cancelado')],'Estado')
	periodopago = fields.Char('Periodo Pago', size=50)
	
	'''
	def init(self,cr):
		cr.execute("""
			create or replace view account_forth_category as (

				select * from vst_reg_forth_1_1_1


						)""")
	'''
