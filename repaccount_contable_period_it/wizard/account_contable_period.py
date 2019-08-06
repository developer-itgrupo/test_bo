# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_contable_period(models.Model):

	_name='account.contable.period'
	_auto = False

	@api.multi
	def compute_saldo(self):
		ide_t = None
		SaldoN = 0
		for x in self.sorted(key=lambda r: str(r.ide) + str(r.id) ):
			if ide_t != x.ide:
				ide_t = x.ide
				SaldoN= 0 
			SaldoN += x.debe
			SaldoN -= x.haber
			x.saldo = SaldoN


	
	periodo = fields.Char(string='Periodo',size=30)
	libro = fields.Char(string='Libro',size=30)
	voucher = fields.Char('Voucher',size=30)
	fecha = fields.Date('Fecha')

	fecha_vencimiento = fields.Date('Fecha de Vencimiento')

	type_document = fields.Char('Tipo de Documento',size=50)
	ruc = fields.Char('RUC',size=20)
	partner = fields.Char(string='Partner',size=100)
	comprobante = fields.Char(string='Comprobante',size=100)
	cuenta = fields.Char(string='Cuenta',size=100)
	debe = fields.Float('Debe',digits=(12,2))
	haber = fields.Float('Haber',digits=(12,2))	
	saldo = fields.Float('Saldo', compute='compute_saldo', digits=(12,2))
	saldo_filter = fields.Float('Saldo',  digits=(12,2))
	ide = fields.Char('IDE')
	tipofiltro = fields.Char('filtro')

	_order = 'partner,cuenta,type_document,comprobante,fecha,id'
