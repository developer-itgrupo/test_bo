# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

class exchange_diff_config(models.Model):
	_name = 'exchange.diff.config'
	
	def init(self):
		#uid = self.env["res.users"].search([])[0]
		cr = self._cr
		cr.execute('select id from res_users')
		uid = cr.dictfetchall()
		print 'uid', uid
		print 'uid0', uid[0]['id']
		cr.execute('select id from exchange_diff_config')
		ids = cr.fetchall()
		print 'ids', ids
		if len(ids) == 0:
			cr.execute("""INSERT INTO exchange_diff_config (create_uid, name) VALUES (""" + str(uid[0]['id']) + """, 'Configuracion Diferencias de Cambio');""")		

	name = fields.Char('Nombre', size=255, default='Configuracion Diferencias de Cambio')
	earn_account_id = fields.Many2one('account.account', string='Cuenta Ganancia')
	lose_account_id = fields.Many2one('account.account', string='Cuenta Perdida')
	lines_id = fields.One2many('exchange.diff.config.line', 'line_id', 'Lineas')

	
class exchange_diff_config_line(models.Model):
	_name='exchange.diff.config.line'
	
	period_id = fields.Many2one('account.period', string='Periodo')
	compra = fields.Float('Compra', digits=(12,3))
	venta = fields.Float('Venta',digits=(12,3))
	line_id = fields.Many2one('exchange.diff.config', 'Header')