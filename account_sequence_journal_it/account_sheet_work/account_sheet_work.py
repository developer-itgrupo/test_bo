# -*- coding: utf-8 -*-

from openerp import models, fields, api


class account_sheet_work_simple_visual(models.Model):
	_name = 'account.sheet.work.simple.visual'


	clasificationactual = fields.Char('clasification',size=50)
	levelactual= fields.Char('level', size=50)
	clasification = fields.Char('clasification',size=50)
	level= fields.Char('level', size=50)
	periodo= fields.Char('Periodo', size=50)
	cuenta= fields.Char('Cuenta', size=200)
	descripcion= fields.Char('Descripción', size=200)
	debe = fields.Float('Debe', digits=(12,2))
	haber = fields.Float('Haber', digits=(12,2))
	saldodeudor = fields.Float('Saldo Deudo', digits=(12,2))
	saldoacredor = fields.Float('Saldo Acreedor', digits=(12,2))

	_order = 'cuenta'

class account_sheet_work_detalle_visual(models.Model):
	_name = 'account.sheet.work.detalle.visual'

	clasificationactual = fields.Char('clasification',size=50)
	levelactual= fields.Char('level', size=50)
	clasification = fields.Char('clasification',size=50)
	level= fields.Char('level', size=50)
	periodo= fields.Char('Periodo', size=50)
	cuenta= fields.Char('Cuenta', size=200)
	descripcion= fields.Char('Descripción', size=200)
	debe = fields.Float('Debe', digits=(12,2))
	haber = fields.Float('Haber', digits=(12,2))
	saldodeudor = fields.Float('Saldo Deudo', digits=(12,2))
	saldoacredor = fields.Float('Saldo Acreedor', digits=(12,2))
	activo = fields.Float('Activo', digits=(12,2))
	pasivo = fields.Float('Pasivo', digits=(12,2))
	perdidasnat = fields.Float('Perdidas NAT', digits=(12,2))
	ganancianat = fields.Float('Ganacias NAT', digits=(12,2))
	perdidasfun = fields.Float('Perdidas FUN', digits=(12,2))
	gananciafun = fields.Float('Ganancia FUN', digits=(12,2))


	_order = 'cuenta'

class account_sheet_work_simple(models.Model):
	_name = 'account.sheet.work.simple'
	_auto = False

	cuenta= fields.Char('Cuenta', size=200)
	descripcion= fields.Char('Descripción', size=200)
	debe = fields.Float('Debe', digits=(12,2))
	haber = fields.Float('Haber', digits=(12,2))
	saldodeudor = fields.Float('Saldo Deudo', digits=(12,2))
	saldoacredor = fields.Float('Saldo Acreedor', digits=(12,2))
	rubro = fields.Char('Rubro',compute="get_rubro")

	@api.one
	def get_rubro(self):
		name = ""
		self.env.cr.execute(""" 
				select aati.name from 
				account_account aa
				inner join account_account_type_it aati on aati.id = aa.type_it
				where aa.code = '""" + (self.cuenta if self.cuenta else '')  + """'
			""")
		t = self.env.cr.fetchall()
		for i in t:
			name = i[0] if i[0] else ''
		self.rubro = name

	_order = 'cuenta'

class account_sheet_work_detalle(models.Model):
	_name = 'account.sheet.work.detalle'
	_auto = False


	#clasificationactual = fields.Char('clasification',size=50)
	#levelactual= fields.Char('level', size=50)
	#clasification = fields.Char('clasification',size=50)
	#level= fields.Char('level', size=50)
	#periodo= fields.Char('Periodo', size=50)
	cuenta= fields.Char('Cuenta', size=200)
	#cuentaactual= fields.Char('Cuenta', size=200)
	descripcion= fields.Char('Descripción', size=200)
	debe = fields.Float('Debe', digits=(12,2))
	haber = fields.Float('Haber', digits=(12,2))
	saldodeudor = fields.Float('Saldo Deudo', digits=(12,2))
	saldoacredor = fields.Float('Saldo Acreedor', digits=(12,2))
	activo = fields.Float('Activo', digits=(12,2))
	pasivo = fields.Float('Pasivo', digits=(12,2))
	perdidasnat = fields.Float('Perdidas Nat.', digits=(12,2))
	ganancianat = fields.Float('Ganancia Nat.', digits=(12,2))
	perdidasfun = fields.Float('Perdidas Fun.', digits=(12,2))
	gananciafun = fields.Float('Ganancia Fun.', digits=(12,2))

	aml_ids = fields.Text('Detalle')

	@api.multi
	def edit_linea_it(self):
		t = eval(self.aml_ids.replace('None','0').replace('NULL','0'))
		elem = []
		for i in t:
			if i!= 0:
				elem.append(i)

		return {
			'name': 'Detalle',
			'domain' : [('id','in',elem)],
			'type': 'ir.actions.act_window',
			'res_model': 'account.move.line',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
			'target': '_blank',
		}

	_order = 'cuenta'