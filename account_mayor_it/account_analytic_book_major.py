# -*- coding: utf-8 -*-

from openerp import models, fields, api


class account_analytic_book_major(models.Model):
	_name = 'account.analytic.book.major'
	_auto = False

	@api.multi
	def compute_saldo(self):
		print "Comenzo"
		y = None
		SaldoN = 0
		for x in self.sorted(key=lambda r: r.id):
			if y != x.cuenta:
				y = x.cuenta
				SaldoN= 0 
			SaldoN += x.debe
			SaldoN -= x.haber
			x.saldo = SaldoN
			print y,SaldoN,x.voucher

	
	periodo= fields.Char('Periodo', size=50)
	libro= fields.Char('Libro', size=50)
	voucher= fields.Char('Voucher', size=50)
	cuenta= fields.Char('Cuenta', size=200)
	descripcion= fields.Char('Descripción', size=200)
	debe = fields.Float('Debe', digits=(12,2))
	haber = fields.Float('Haber', digits=(12,2))
	divisa= fields.Char('Divisa', size=50)
	tipocambio  = fields.Float('Tipo Cambio', digits=(12,3))
	importedivisa  = fields.Float('Importe Divisa', digits=(12,2))

	conciliacion= fields.Char('Conciliación', size=50)
	fechaemision = fields.Date('Fecha Emisión')
	fechavencimiento = fields.Date('Fecha Vencimiento')
	tipodocumento= fields.Char('Tipo de Documento', size=50)
	numero= fields.Char('Número', size=50)
	ruc= fields.Char('RUC', size=50)
	partner= fields.Char('Partner', size=50)
	glosa = fields.Char('Glosa', size=50)
	analitica = fields.Char('Analítica', size=200)
	ordenamiento = fields.Integer('Ordenamiento')
	cuentaname = fields.Char('Cuenta Name', size=200)
	saldo = fields.Float('Saldo', compute='compute_saldo', digits=(12,2))
	state = fields.Char('Estado',size=50)


class account_analytic_book_major_saldoinicial(models.Model):
	_name = 'account.analytic.book.major.saldoinicial'

	
	periodo= fields.Char('Periodo', size=50)
	libro= fields.Char('Libro', size=50)
	voucher= fields.Char('Voucher', size=50)
	cuenta= fields.Char('Cuenta', size=200)
	descripcion= fields.Char('Descripción', size=200)
	debe = fields.Float('Debe', digits=(12,2))
	haber = fields.Float('Haber', digits=(12,2))
	divisa= fields.Char('Divisa', size=50)
	tipocambio  = fields.Float('Tipo Cambio', digits=(12,3))
	importedivisa  = fields.Float('Importe Divisa', digits=(12,2))

	conciliacion= fields.Char('Conciliación', size=50)
	fechaemision = fields.Date('Fecha Emisión')
	fechavencimiento = fields.Date('Fecha Vencimiento')
	tipodocumento= fields.Char('Tipo de Documento', size=50)
	numero= fields.Char('Número', size=50)
	ruc= fields.Char('RUC', size=50)
	partner= fields.Char('Partner', size=50)
	glosa = fields.Char('Glosa', size=50)
	analitica = fields.Char('Analítica', size=200)
	ordenamiento = fields.Integer('Ordenamiento')

	_defaults={
		'ordenamiento' : 1,
	}