# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_move_line_book(models.Model):
	_name = 'account.move.line.book'
	_auto = False

	statefiltro = fields.Char('StateFiltro',size=50)
	periodo= fields.Char('Periodo', size=50)
	libro= fields.Char('Libro', size=50)
	voucher= fields.Char('Voucher', size=50)
	cuenta= fields.Char('Cuenta', size=200)
	descripcion = fields.Char('Descripción',size=200)
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
	aml_id = fields.Many2one('account.move.line', 'aml id')
	aj_id = fields.Many2one('account.journal', 'journal id')
	ap_id = fields.Many2one('account.period','period id')
	am_id = fields.Many2one('account.move','move id')
	aa_id = fields.Many2one('account.account', 'account id')
	rc_id = fields.Many2one('res.currency', 'currency id')
	rp_id = fields.Many2one('res.partner' , 'partner id')
	itd_id = fields.Many2one('einvoice.catalog.01', 'typo document id')
	aaa_id = fields.Many2one('account.analytic.account','analytic id')
	state = fields.Char('Estado',size=50)





class account_move_line_book_report(models.Model):
	_name = 'account.move.line.book.report'
	_auto = False

	statefiltro = fields.Char('StateFiltro',size=50)
	periodo= fields.Char('Periodo', size=50)
	libro= fields.Char('Libro', size=50)
	voucher= fields.Char('Voucher', size=50)
	cuenta= fields.Char('Cuenta', size=200)
	descripcion = fields.Char('Descripción',size=200)
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
	state = fields.Char('Estado',size=50)

