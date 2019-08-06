# -*- coding: utf-8 -*-

from openerp import models, fields, api


class account_payable_contable_vencimiento(models.Model):

	_name='account.payable.contable.vencimiento'

	_order = "empresa, nro_comprobante"
	
	_auto = False

	fecha_emision = fields.Char(string='F. Emision',size=200)
	fecha_ven = fields.Char(string='F. Vencimiento',size=200)
	plazo= fields.Char('Plazo')

	nro_comprobante = fields.Char(string='Número',size=200)
	empresa = fields.Char(string='Empresa',size=200)

	tipo = fields.Char('TD')
	cuenta = fields.Char(string='Cuenta',size=200)
	importe_me = fields.Float('Importe ME')
	moneda = fields.Char('Moneda')
	por_vencer = fields.Float('Vencidas', digits=(12,2))
	hasta_15 = fields.Float('De 1 a 15', digits=(12,2))
	hasta_30 = fields.Float('De 16 a 30', digits=(12,2))
	hasta_60 = fields.Float('De 46 a 60', digits=(12,2))
	hasta_90 = fields.Float('De 61 a 90', digits=(12,2))
	hasta_180 = fields.Float('De 91 a 180', digits=(12,2))
	mas_de_180 = fields.Float('Mas de 180', digits=(12,2))




class account_receivable_contable_vencimiento(models.Model):

	_name='account.receivable.contable.vencimiento'

	_order = "empresa, nro_comprobante"
	
	_auto = False

	fecha_emision = fields.Char(string='F. Emision',size=200)
	fecha_ven = fields.Char(string='F. Vencimiento',size=200)
	plazo= fields.Char('Plazo')

	nro_comprobante = fields.Char(string='Número',size=200)
	empresa = fields.Char(string='Empresa',size=200)

	tipo = fields.Char('TD')
	cuenta = fields.Char(string='Cuenta',size=200)
	importe_me = fields.Float('Importe ME')
	moneda = fields.Char('Moneda')

	por_vencer = fields.Float('Vencidas', digits=(12,2))
	hasta_15 = fields.Float('De 1 a 15', digits=(12,2))
	hasta_30 = fields.Float('De 16 a 30', digits=(12,2))
	hasta_60 = fields.Float('De 46 a 60', digits=(12,2))
	hasta_90 = fields.Float('De 61 a 90', digits=(12,2))
	hasta_180 = fields.Float('De 91 a 180', digits=(12,2))
	mas_de_180 = fields.Float('Mas de 180', digits=(12,2))

