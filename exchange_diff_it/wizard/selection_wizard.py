# -*- encoding: utf-8 -*-
import time

from odoo import api, fields, models, _
from datetime import *
from odoo.exceptions import UserError, ValidationError


class selection_wizard(models.TransientModel):
	_name='selection.wizard'
	
	TYPE_SELECTION = [
		('payable', 'A Pagar'),
		('receivable', 'A Cobrar'),
	]

	def get_fiscalyear(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		id_year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1).id
		if not id_year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			return id_year

	fiscalyear_id = fields.Many2one('account.fiscalyear', string='Anio Fiscal',default=lambda self: self.get_fiscalyear(),readonly=True)

	def get_period(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
		if not year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			periodos = self.env['account.period'].search([('fiscalyear_id','=',year.id)])
			periodos = filter(lambda period: not period.special and datetime.strptime(period.date_start,"%Y-%m-%d").month == datetime.now().month,periodos)
			periodos = periodos[0].id if len(periodos) > 0 else 0
			return periodos
	
	period_id = fields.Many2one('account.period', string='Periodo',default=lambda self:self.get_period())
	type = fields.Selection(TYPE_SELECTION, string='Tipo', help="Tipo")
		
	
	@api.multi
	def print_report(self):

		line_obj = self.env['exchange.diff.line']
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		data = self.read()
		context = dict(self._context)
		#context = dict(self._context)
		context.update({'fiscalyear_id': data[0]['fiscalyear_id'][0], 'period_id': data[0]['period_id'][0], 'type': data[0]['type']})
		self.env.cr.execute('TRUNCATE exchange_diff_line;')
		ids2=line_obj.with_context(context).make_process_records()
		if ids2==[]:
			raise ValidationError('No encontraron registros')
		result={}
		#raise osv.except_osv('Alerta',data)
		view_ref = False
		if data[0]['type'] in ['payable', 'receivable']:
			#ir_model_obj.get_object_reference('account', action_name)
			#view_ref = self.env['ir.model.data'].get_object_reference('exchange_diff_it', 'view_exchange_diff_line_action')
			#view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'exchange_diff_it', 'view_exchange_diff_line_action')
			

			#view_id = view_ref and view_ref[1] or False
			#result = act_obj.read([view_id])

			ir_model_obj = self.env['ir.model.data']
			model, action_id = ir_model_obj.get_object_reference('exchange_diff_it', 'view_exchange_diff_line_action')
			[action] = self.env[model].browse(action_id).read()
			#import pdb; pdb.set_trace()
			return action
		else:
			view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'exchange_diff_it', 'view_exchange_diff_line_active_action')
			view_id = view_ref and view_ref[1] or False
			result = act_obj.read([view_id])
			return result[0]
		return True
		
	 	
		
	 	
	# 	if ids2==[]:
	# 		raise osv.except_osv('Alerta','No encontraron registros')
	# 	result={}
	# 	#raise osv.except_osv('Alerta',data)
	# 	view_ref = False
	# 	if data['type'] in ['payable', 'receivable']:
	# 		print 'IN 1'
	# 		view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'exchange_diff_it', 'view_exchange_diff_line_action')
	# 		view_id = view_ref and view_ref[1] or False
	# 		print 'view_id', view_id
	# 		result = act_obj.read(cr, uid, [view_id], context=context)
	# 		print 'result', result
	# 		return result[0]
	# 	else:
	# 		print 'IN 2'
	# 		view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'exchange_diff_it', 'view_exchange_diff_line_active_action')
	# 		view_id = view_ref and view_ref[1] or False
	# 		print 'view_id', view_id
	# 		result = act_obj.read(cr, uid, [view_id], context=context)
	# 		print 'result', result
	# 		return result[0]
