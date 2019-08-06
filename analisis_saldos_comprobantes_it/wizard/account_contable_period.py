# -*- coding: utf-8 -*-

from openerp import models, fields, api

class saldo_comprobante(models.Model):

	_name='saldo.comprobante'
	_auto = False

	fecha_emision = fields.Date('Fecha Emisión')
	empresa = fields.Char('Empresa')
	tipo_cuenta = fields.Char('Tipo Cuenta')
	code = fields.Char('Cuenta')
	tipo = fields.Char('Tipo Documento')
	nro_comprobante = fields.Char('Nro. Comprobante')
	debe = fields.Float('Debe',digits=(12,2))
	haber = fields.Float('Haber',digits=(12,2))
	saldo = fields.Float('Saldo',digits=(12,2))
	divisa = fields.Char('Divisa')
	amount_currency = fields.Float('Importe',digits=(12,2))

