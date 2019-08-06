# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_purchase_register_nodeducible(models.Model):
	_name = 'account.purchase.register.nodeducible'
	_auto = False

	periodo= fields.Char('Periodo', size=50)
	libro= fields.Char('Libro', size=50)
	voucher= fields.Char('Voucher', size=50)
	fechaemision = fields.Date('Fecha Emisión')
	fechavencimiento = fields.Date('Fecha Vencimiento')
	tipodocumento = fields.Char('T.D.', size=50)
	serie = fields.Char('Serie', size=50)
	numero = fields.Char('Numero', size=50)
	anio = fields.Char('Año', size=50)
	
	tdp = fields.Char('T.D.P.', size=50)
	ruc = fields.Char('RUC/DNI.', size=50)
	razonsocial = fields.Char('Razon Social', size=50)
	
	bioge = fields.Float('BIOGE', digits=(12,2))
	biogeng = fields.Float('BIOGENG', digits=(12,2))
	biong = fields.Float('BIONG', digits=(12,2))
	cng = fields.Float('CNG', digits=(12,2))
	isc = fields.Float('ISC', digits=(12,2))
	igva = fields.Float('IGVA', digits=(12,2))
	igvb = fields.Float('IGVB', digits=(12,2))
	igvc = fields.Float('IGVC', digits=(12,2))
	otros  = fields.Float('Otros', digits=(12,2))
	total  = fields.Float('Total', digits=(12,2))
	
	comprobante = fields.Char('CSND',size=50)
	moneda = fields.Char('Moneda', size=50)
	tc = fields.Float('T.C.', digits=(12,3))
	fechad = fields.Date('Fecha_Doc')
	numerod = fields.Char('Numero_Doc', size=50)
	fechadm = fields.Date('F_Doc_M')
	td = fields.Char('T.D._Doc', size=50)
	seried = fields.Char('Serie', size=50)
	numerodd = fields.Char('Numero', size=50)
	