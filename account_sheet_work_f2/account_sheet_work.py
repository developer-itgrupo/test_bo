# -*- coding: utf-8 -*-

from openerp import models, fields, api


class account_sheet_work_f2_visual(models.Model):
	_name = 'account.sheet.work.f2.visual'
	_auto = False


	cuenta= fields.Char('Cuenta', size=200)
	descripcion= fields.Char('Descripción', size=200)

	debeinicial = fields.Float('SI Debe', digits=(12,2))
	haberinicial = fields.Float('SI Haber', digits=(12,2))
	
	debe = fields.Float('MP Debe', digits=(12,2))
	haber = fields.Float('MP Haber', digits=(12,2))

	debesa = fields.Float('SA Debe', digits=(12,2))
	habersa = fields.Float('SA Haber', digits=(12,2))

	saldodeudor = fields.Float('Deudo', digits=(12,2))
	saldoacredor = fields.Float('Acreedor', digits=(12,2))
	activo = fields.Float('Activo', digits=(12,2))
	pasivo = fields.Float('Pasivo', digits=(12,2))
	perdidasnat = fields.Float('Perdidas NAT', digits=(12,2))
	ganancianat = fields.Float('Ganacias NAT', digits=(12,2))
	perdidasfun = fields.Float('Perdidas FUN', digits=(12,2))
	gananciafun = fields.Float('Ganancia FUN', digits=(12,2))

	
	_order = 'cuenta'
