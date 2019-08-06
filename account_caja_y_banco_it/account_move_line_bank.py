# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_move_line_bank(models.Model):
	_name = 'account.move.line.bank'
	_auto = False

	periodo= fields.Char('Periodo', size=50)
	libro= fields.Char('Libro', size=50)
	voucher= fields.Char('Voucher', size=50)
	cuentacode= fields.Char('Cuenta', size=200)
	cuentaname= fields.Char('Descripcion', size=200)
	debe = fields.Float('Debe', digits=(12,2))
	haber = fields.Float('Haber', digits=(12,2))
	divisa= fields.Char('Divisa', size=50)
	tipodecambio  = fields.Float('Tipo Cambio', digits=(12,3))
	importedivisa  = fields.Float('Importe Divisa', digits=(12,2))
	codigo= fields.Char('Código', size=50)
	partner= fields.Char('Partner', size=50)
	tipodocumento= fields.Char('Tipo de Documento', size=50)
	numero= fields.Char('Número', size=50)
	fechaemision = fields.Date('Fecha Emisión')
	fechavencimiento = fields.Date('Fecha Vencimiento')
	glosa = fields.Char('Glosa', size=50)
	ctaanalitica= fields.Char('Cta. Analítica', size=50)
	refconcil= fields.Char('Referencia Conciliación', size=50)
	statefiltro = fields.Char('StateFiltro',size=50)
	mediopago = fields.Char('Medio Pago', size=50)
	entfinan = fields.Char('Entidad Financiera')
	nrocta = fields.Char('Nro. Cuenta', size=50)
	moneda = fields.Char('Moneda', size=10)
	saldo = fields.Float('Saldo', compute='compute_saldo', digits=(12,2))

	
	@api.multi
	def compute_saldo(self):
		y = None
		SaldoN = 0
		for x in self.sorted(key=lambda r: r.id):
			if y != x.cuentacode:
				y = x.cuentacode
				SaldoN= 0 
			SaldoN += x.debe
			SaldoN -= x.haber
			x.saldo = SaldoN
			