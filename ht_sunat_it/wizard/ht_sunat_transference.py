# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

class ht_sunat_transference(models.Model):
	_name='ht.sunat.transference'
	
	account = fields.Char('Cuenta',size=200)
	debit = fields.Float('Debe',digits=(12,2))
	credit = fields.Float('Haber',digits=(12,2))



class ht_sunat_transference_wizard(osv.TransientModel):
	_name='ht.sunat.transference.wizard'

	cuenta = None
	resto= None

	@api.onchange('debit','credit')
	def verificar_cuenta(self):
		global resto
		global cuenta
		if self.env.context.get('active_ids',False):
			resto = self.env.context.get('active_ids',False)
			j = self.env['ht.sunat'].search([('id','=',resto[0])])
			resto= resto[1:]
			self.account = j.cuenta
			cuenta= j.cuenta
		else:
			self.finalizado = True


	account = fields.Char('Cuenta',readonly=True)
	debit = fields.Float('Debe',digits=(12,2))
	credit = fields.Float('Haber',digits=(12,2))
	mensaje= fields.Char('Mensaje',size=400)
	check = fields.Boolean('Check')
	finalizado = fields.Boolean('finalizo')



	@api.multi
	def do_rebuild(self):
		global resto
		global cuenta

		data = {
		'account' : cuenta,
		'debit' :self.debit,
		'credit' :self.credit,
		}
		t = self.env['ht.sunat.transference'].search( [('account','=',cuenta)] )
		if len(t)>0:
			t[0].debit = self.debit
			t[0].credit = self.credit
		else:
			self.env['ht.sunat.transference'].create(data)
		print data
		return {
			'context': {'active_ids':resto, 'default_check':True,'default_mensaje': 'Registrado exitosamente la cuenta "'+ str(cuenta) + '" con Debe: ' + str(data['debit'])+ ' y Haber: ' + str(data['credit'])},
			'type': 'ir.actions.act_window',
			'res_model': 'ht.sunat.transference.wizard',
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
		}
