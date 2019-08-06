# -*- coding: utf-8 -*-

from openerp import models, fields, api

class saldo_comprobante_empresa(models.Model):

	_name='saldo.comprobante.empresa'
	_auto = False

	periodo = fields.Char('Periodo')
	empresa = fields.Char('Empresa')
	ruc = fields.Char('RUC')
	tipo_cuenta = fields.Char('Tipo Cuenta')
	code = fields.Char('Cuenta')
	descripcion = fields.Char('Descripción')
	debe = fields.Float('Debe',digits=(12,2))
	haber = fields.Float('Haber',digits=(12,2))
	saldo = fields.Float('Saldo',digits=(12,2))

