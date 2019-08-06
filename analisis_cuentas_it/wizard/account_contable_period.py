# -*- coding: utf-8 -*-

from openerp import models, fields, api

class analisis_cuenta(models.Model):

	_name='analisis.cuenta'
	_auto = False

	group_balance = fields.Char('Grupo Balance')
	group_function = fields.Char('Grupo Funcion')
	group_nature = fields.Char('Grupo Natural')

	periodo_inicial = fields.Many2one('account.period',string='Periodo inicial')
	periodo_final = fields.Many2one('account.period',string='Periodo Final')
	
	rubro = fields.Text(string='Rubro')
	cuenta = fields.Text(string='Cuenta')
	debe = fields.Float(string='Debe', digits=(12,2))
	haber = fields.Float(string='Haber', digits=(12,2))
	saldo = fields.Float(string='Saldo', digits=(12,2))
	aml_ids = fields.Text('Detalle')
	#diario = fields.Text(string='Diario')
	#voucher = fields.Text(string='Voucher')
	

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
