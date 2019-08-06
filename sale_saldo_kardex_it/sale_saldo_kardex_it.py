# -*- coding: utf-8 -*-
# partner.py

from openerp.osv import osv
from openerp import models, fields, api  , exceptions , _

class sale_saldo_kardex_it(models.Model):
	_inherit = 'sale.order'	

	@api.multi
	def get_saldo(self):		
		productos = []
		#Productos del sale_order
		for fila in self.order_line:
			var = fila.product_id.id
			if var not in productos:							
				productos.append(var)	
		#Productos del option		
		#Año Fiscal
		year = self.date_order
		year = year[0:4]

		fiscal_year = self.env['account.fiscalyear'].search([('name','=', year)])
		if not fiscal_year:
			raise exceptions.Warning(_(u"No existe el Año Fiscal"))

		saldos = self.env['detalle.simple.fisico.total.d.wizard'].create({'fiscalyear_id':fiscal_year.id})
		saldos.do_rebuild()		

		return {
			'type'     : 'ir.actions.act_window',
			'res_model': 'detalle.simple.fisico.total.d',
			# 'res_id'   : self.id,			
			'view_type': 'form',
			'view_mode': 'tree',			
			'target'   : 'new',
			#'flags'    : {'form': {'action_buttons': True}},
			'domain'  : [('producto','in',productos)],
		}










