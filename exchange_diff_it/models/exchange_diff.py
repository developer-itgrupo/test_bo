# -*- coding: utf-8 -*-
import datetime
from openerp.osv import osv
from openerp import models, fields, api

from odoo.exceptions import UserError, ValidationError
from odoo import _


class make_exchange_diff(models.Model):
	_name = "make.exchange.diff"

	journal_id = fields.Many2one('account.journal', 'Diario')
	has_extorno = fields.Boolean('Tiene Extorno',default=True)
	
	@api.multi
	def make_calculate_differences(self):
		line_obj = self.env['exchange.diff.line']
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		# for install_act in picking_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
			# if install_act.state == 'draft':
			# 	raise osv.except_osv('Alerta', 'No es posible procesar notas en borrador')
		
		#print 'Fecha Fin', data['date_end']
						
		ids2=line_obj.browse(self.env.context['active_ids']).with_context({'journal_id':self.journal_id.id,'has_extorno':self.has_extorno,'active_ids':self.env.context['active_ids']}).make_calculate_differences()
		ids2= self.env.context['active_ids']
		if ids2==[]:
			raise osv.except_osv('Alerta','No se calculo la diferencias, verifique los elementos seleccionados')
		result={}

		model, action_id = self.env['ir.model.data'].get_object_reference('exchange_diff_it','view_exchange_diff_line_action')
		
		[action] = self.env[model].browse(action_id).read()
		
		return action

class exchange_diff_line(models.Model):
	_name='exchange.diff.line'

	account_id = fields.Many2one('account.account', string='Cuenta')
	account_code = fields.Char(related='account_id.code', string='Cuenta', store=True)
	invoice = fields.Char(string='Factura', size=64)
	partner_id = fields.Many2one('res.partner', string='Partner')
	type_document_id = fields.Many2one('it.type.document', string='Partner')
	currency_id = fields.Many2one('res.currency', string='Divisa')
	debit = fields.Float(string='Debe', digits=(12,2))
	credit = fields.Float(string='Haber', digits=(12,2))
	saldo = fields.Float(string='Saldo M.N.', digits=(12,2))
	amount_currency = fields.Float(string='Monto Act', digits=(12,2))
	exchange = fields.Float(string='Tipo Cambio Cierre', digits=(12,3))
	amount = fields.Float(string='Monto Act', digits=(12,2))
	diff = fields.Float(string='Diferencia', digits=(12,2))
	period_id = fields.Many2one('account.period', string='Periodo')
	current_type = fields.Char(string='Tipo', size=64)
	exchange_account_id = fields.Many2one('account.account', string='Cuenta Ajuste')
	exchange_account_code = fields.Char(related='exchange_account_id.code', string='Cuenta Ajuste', store=True)
    #line_id = fields.Many2one('exchange.diff', string='Header')





	def make_process_records(self):
		fiscalyear_id = self.env.context['fiscalyear_id']
		period_id = self.env.context['period_id']
		tipo = (self.env.context['type']).encode("utf-8")
		
		res = []


		config_obj_id = self.env['exchange.diff.config'].search([])
		if len(config_obj_id) == 0:
			raise ValidationError(_('Alerta','Debe configurar las diferencias de cambio en el menu Contabilidad/Miscelaneous'))	
		config_obj =  config_obj_id[0]
		if tipo == 'payable':
			periodo = self.env['account.period'].browse(period_id)
			periods_ids = self.env['account.period'].search([('date_start', '<', periodo.date_stop),('fiscalyear_id','=',fiscalyear_id)])

			account__type_id = self.env['account.account.type'].search([('type','=',tipo)])
			
			account_ids = self.env['account.account'].search([('user_type_id','in',account__type_id.ids),('currency_id', '!=', False)])
			#account_ids = self.env['account.account'].search([('user_type_id','=',account__type_id)])
			

			#account_ids = self.env['account.account'].search([('type','=',tipo),('active','=',True),('currency_id', '!=', False)])
			#dates_start_periods = sorted(map(datetime,periods_ids.date_start))
			#dates_start_periods for dates_start_periods, periods_ids in periods_ids.date_start()
			dates_start_periods = [datetime.datetime.strptime(s.date_start,'%Y-%m-%d').date() for s in periods_ids]
			dates_start = sorted(dates_start_periods)[0]
			dates_start_string = dates_start.strftime('%Y-%m-%d')

			dates_stop_periods = [datetime.datetime.strptime(s.date_stop,'%Y-%m-%d').date() for s in periods_ids]
			dates_stop = sorted(dates_stop_periods)[len(dates_stop_periods)-1]
			dates_stop_string = dates_stop.strftime('%Y-%m-%d')
			
			account_ids = sorted(map(int,account_ids))
			moves_ids = self.env['account.move.line'].search([('account_id', 'in', account_ids),('move_id.state','!=','draft'),('move_id.fecha_contable','>=',dates_start_string),('move_id.fecha_contable','<=',dates_stop_string)])
			
			if config_obj.earn_account_id.id == False:
				raise ValidationError('Debe configurar una cuenta para las ganancias')
			if config_obj.lose_account_id.id == False:
				raise ValidationError('Debe configurar una cuenta para las perdidas')
			if len(moves_ids) > 0:
				fact = {}
				for line in moves_ids:
					rate = 0.00
					for dato in config_obj.lines_id:
						if dato.period_id.id == periodo.id:
							rate = dato.venta
							break
					partner = str(line.partner_id.id) if line.partner_id.id != False else 'NONE_PARTNER'
					voucher = line.nro_comprobante if line.nro_comprobante != False else 'NONE_VOUCHER'
					doc_type = str(line.type_document_it.id) if line.type_document_it.id != False else 'NONE_TYPE'
					accindex = str(line.account_id.id) if line.account_id.id != False else 'NONE_TYPE'
					index = voucher + '|' + partner + '|' + doc_type + '|' + accindex

					if index in fact:
						if line.credit > 0:
							fact[index]['invoice'] = line.nro_comprobante	
						fact[index]['debit'] += line.debit
						fact[index]['credit'] += line.credit
						fact[index]['saldo'] = fact[index]['credit'] - fact[index]['debit']
						fact[index]['amount_currency'] += line.amount_currency
						fact[index]['amount'] = round(fact[index]['amount_currency'] * fact[index]['exchange'],2)
						fact[index]['diff'] = fact[index]['amount'] - fact[index]['saldo']
						fact[index]['exchange_account_id'] = config_obj.earn_account_id.id if fact[index]['diff'] >= 0 else config_obj.lose_account_id.id,
					else:
						fact.update({index : {
							'account_id': line.account_id.id,
							'invoice': line.nro_comprobante,
							'partner_id': line.partner_id.id,
							'type_document_id': line.type_document_it.id,
							'currency_id': line.currency_id.id,
							'debit': line.debit,
							'credit': line.credit,
							'saldo': line.credit - line.debit,
							'amount_currency': line.amount_currency,
							'exchange': rate,
							'amount': round((line.amount_currency) * rate,2),
							'diff': ((line.amount_currency) * rate) - (line.credit - line.debit),
							'period_id': periodo.id,
							'current_type': tipo,
							'exchange_account_id': config_obj.earn_account_id.id if (((line.amount_currency) * rate) - (line.credit - line.debit)) >= 0 else config_obj.lose_account_id.id,
						}})
				
				for key, value in fact.items():
					value['amount'] = -1 * round((value['amount_currency'] * value['exchange']),2)
					value['diff'] = value['amount'] - value['saldo']
					if round(value['diff'],2) != 0:
						value['exchange_account_id'] = config_obj.earn_account_id.id if value['amount'] < value['saldo'] else config_obj.lose_account_id.id
					else:
						value['exchange_account_id'] = False
					#ex_line = self.pool.get('exchange.diff.line').create(cr, uid, value, context)
					if not value['amount'] == 0: 
						ex_line = self.env['exchange.diff.line'].create(value)
						res.append(ex_line)

		if tipo == 'receivable':

			periodo = self.env['account.period'].browse(period_id)
			periods_ids = self.env['account.period'].search([('date_start', '<', periodo.date_stop),('fiscalyear_id','=',fiscalyear_id)])

			account__type_id = self.env['account.account.type'].search([('type','=',tipo)])
			
			account_ids = self.env['account.account'].search([('user_type_id','in',account__type_id.ids),('currency_id', '!=', False)])
			#account_ids = self.env['account.account'].search([('user_type_id','=',account__type_id)])

			dates_start_periods = [datetime.datetime.strptime(s.date_start,'%Y-%m-%d').date() for s in periods_ids]
			dates_start = sorted(dates_start_periods)[0]
			dates_start_string = dates_start.strftime('%Y-%m-%d')

			dates_stop_periods = [datetime.datetime.strptime(s.date_stop,'%Y-%m-%d').date() for s in periods_ids]
			dates_stop = sorted(dates_stop_periods)[len(dates_stop_periods)-1]
			dates_stop_string = dates_stop.strftime('%Y-%m-%d')
			
			account_ids = sorted(map(int,account_ids))
			moves_ids = self.env['account.move.line'].search([('account_id', 'in', account_ids),('move_id.state','!=','draft'),('move_id.fecha_contable','>=',dates_start_string),('move_id.fecha_contable','<=',dates_stop_string)])
			
			if config_obj.earn_account_id.id == False:
				raise osv.except_osv('Alerta','Debe configurar una cuenta para las ganancias')
			if config_obj.lose_account_id.id == False:
				raise osv.except_osv('Alerta','Debe configurar una cuenta para las perdidas')
			
			#raise osv.except_osv('Alerta',moves_ids)
			if len(moves_ids) > 0:
				fact = {}
				for line in moves_ids:

					rate = 0.00
					for dato in config_obj.lines_id:
						if dato.period_id.id == periodo.id:
							rate = dato.compra
							break
					
					partner = str(line.partner_id.id) if line.partner_id.id != False else 'NONE_PARTNER'
					
					voucher = line.nro_comprobante if line.nro_comprobante != False else 'NONE_VOUCHER'
					
					doc_type = str(line.type_document_it.id) if line.type_document_it.id != False else 'NONE_TYPE'
					
					accindex = str(line.account_id.id) if line.account_id.id != False else 'NONE_TYPE'
					
					index = voucher + '|' + partner + '|' + doc_type + '|' + accindex
					
					if index in fact:
						if line.credit > 0:
							fact[index]['invoice'] = line.nro_comprobante	
						fact[index]['debit'] += line.debit
						fact[index]['credit'] += line.credit
						fact[index]['saldo'] = fact[index]['debit'] - fact[index]['credit']
						fact[index]['amount_currency'] += line.amount_currency
						fact[index]['amount'] = round(fact[index]['amount_currency'] * fact[index]['exchange'],2)
						fact[index]['diff'] = fact[index]['amount'] - fact[index]['saldo']
						fact[index]['exchange_account_id'] = config_obj.earn_account_id.id if fact[index]['diff'] >= 0 else config_obj.lose_account_id.id,
					else:
						fact.update({index : {
							'account_id': line.account_id.id,
							'invoice': line.nro_comprobante,
							'partner_id': line.partner_id.id,
							'type_document_id': line.type_document_it.id,
							'currency_id': line.currency_id.id,
							'debit': line.debit,
							'credit': line.credit,
							'saldo': line.debit - line.credit,
							'amount_currency': line.amount_currency,
							'exchange': rate,
							'amount': round((line.amount_currency) * rate,2),
							'diff': ((line.amount_currency) * rate) - (line.debit - line.credit),
							'period_id': periodo.id,
							'current_type': tipo,
							'exchange_account_id': config_obj.earn_account_id.id if (((line.amount_currency) * rate) - (line.debit - line.credit)) >= 0 else config_obj.lose_account_id.id,
							#'line_id': obj.id,
						}})
					
				for key, value in fact.items():
					#value['amount_currency'] = abs(value['amount_currency'])
					value['amount'] = value['amount_currency'] * value['exchange']
					value['diff'] = value['amount'] - value['saldo']
					if round(value['diff'],2) != 0:
						value['exchange_account_id'] = config_obj.lose_account_id.id if value['amount'] < value['saldo'] else config_obj.earn_account_id.id,
					else:
						value['exchange_account_id'] = False
					if not value['amount'] == 0: 
						ex_line = self.env['exchange.diff.line'].create(value)
						res.append(ex_line)
		return res


	@api.multi
	def make_calculate_differences(self):
		#raise osv.except_osv('Alerta','Listo para implemetar el asiento de cambio')
		journal_id = self.env.context['journal_id']
		has_extorno = self.env.context['has_extorno']
		#Configuracion
		config_obj_id = self.env['exchange.diff.config'].search([])
		if len(config_obj_id) == 0:
			raise osv.except_osv('Alerta','Debe configurar las diferencias de cambio en el menu Contabilidad/Miscelaneous')
		config_obj = config_obj_id[0]

		if config_obj.earn_account_id.id == False:
			raise osv.except_osv('Alerta','Debe configurar una cuenta para las ganancias')
		if config_obj.lose_account_id.id == False:
			raise osv.except_osv('Alerta','Debe configurar una cuenta para las perdidas')
		periodo = None
		periodo_next = None
		total_earn = 0.00	
		total_lose = 0.00	

		cc_earn = []
		cc_earn_ext = []
		cc_lose = []
		cc_lose_ext = []

		for item in self:
			if periodo is None:
				periodo = item.period_id
				periodo_next = self.env['account.period'].search( [('date_start', '>', periodo.date_stop)] ).sorted(key=lambda r: r.date_start)[0]
				if len(periodo_next) == 0:
					raise osv.except_osv('Alerta','No existe el periodo siguiente a ' + periodo.code)
				
			if item.exchange_account_id.id != False:
				if item.exchange_account_id.id == config_obj.lose_account_id.id:
					refund_cc = (0,0,{
							'tax_amount': 0.0, 
							'name': 'Diferencia de Cambio Mensual', 
							'ref': False, 
							'currency_id': item.currency_id.id,
							'debit': 0.00,
							'credit': abs(item.diff), 
							'date_maturity': False, 
							'date': periodo.date_stop,
							'amount_currency':0.00, 
							'account_id': item.account_id.id,
							'partner_id': item.partner_id.id,
							'type_document_it': item.type_document_id.id,
							'nro_comprobante': item.invoice if item.current_type in ['payable', 'receivable'] else 'DIF. CAM. ' + periodo.code,
							})
					if has_extorno:
						refund_cc_2 = (0,0,{
								'tax_amount': 0.0, 
								'name': 'Extorno Diferencia de Cambio Mensual', 
								'ref': False, 
								'currency_id': item.currency_id.id,
								'debit': abs(item.diff),
								'credit': 0.00,
								'date_maturity': False, 
								'date': periodo_next.date_start,
								'amount_currency':0.00, 
								'account_id': item.account_id.id,
								'partner_id': item.partner_id.id,
								'type_document_it': item.type_document_id.id,
								'nro_comprobante': item.invoice if item.current_type in ['payable', 'receivable'] else 'DIF. CAM. ' + periodo_next.code,
								})
						cc_lose_ext.append(refund_cc_2)
					cc_lose.append(refund_cc)
					total_lose += abs(item.diff)
				if item.exchange_account_id.id == config_obj.earn_account_id.id:
					#parcho al empleado
					refund_cc = (0,0,{
							'tax_amount': 0.0, 
							'name': 'Diferencia de Cambio Mensual', 
							'ref': False, 
							'currency_id': item.currency_id.id,
							'debit': abs(item.diff),
							'credit': 0.00, 
							'date_maturity': False, 
							'date': periodo.date_stop,
							'amount_currency':0.00, 
							'account_id': item.account_id.id,
							'partner_id': item.partner_id.id,
							'type_document_it': item.type_document_id.id,
							'nro_comprobante': item.invoice if item.current_type in ['payable', 'receivable'] else 'DIF. CAM. ' + periodo.code,
							})
					if has_extorno:	
						refund_cc_2 = (0,0,{
								'tax_amount': 0.0, 
								'name': 'Diferencia de Cambio Mensual', 
								'ref': False, 
								'currency_id': item.currency_id.id,
								'debit': 0.00,
								'credit': abs(item.diff), 
								'date_maturity': False, 
								'date': periodo_next.date_start,
								'amount_currency':0.00, 
								'account_id': item.account_id.id,
								'partner_id': item.partner_id.id,
								'type_document_it': item.type_document_id.id,
								'nro_comprobante': item.invoice if item.current_type in ['payable', 'receivable'] else 'DIF. CAM. ' + periodo_next.code,
								})
						cc_earn_ext.append(refund_cc_2)
					cc_earn.append(refund_cc)
					total_earn += abs(item.diff) 

		if len(cc_lose) > 0:
			lose_cc = (0,0,{
					'tax_amount': 0.0, 
					'name': 'Diferencia de Cambio Mensual', 
					'ref': False, 
					'currency_id': False,
					'debit': total_lose,
					'credit': 0.00, 
					'date_maturity': False, 
					'date': periodo.date_stop,
					'amount_currency':0.00, 
					'account_id': config_obj.lose_account_id.id,
					'partner_id': False,
					'type_document_it': False,
					'nro_comprobante': 'DIF. CAM. ' + periodo.code,
					})
			if has_extorno:	
				lose_cc_2 = (0,0,{
						'tax_amount': 0.0, 
						'name': 'Diferencia de Cambio Mensual', 
						'ref': False, 
						'currency_id': False,
						'debit': 0.00,
						'credit': total_lose, 
						'date_maturity': False, 
						'date': periodo_next.date_start,
						'amount_currency':0.00, 
						'account_id': config_obj.lose_account_id.id,
						'partner_id': False,
						'type_document_it': False,
						'nro_comprobante': 'DIF. CAM. ' + periodo_next.code,
						})
				cc_lose_ext.append(lose_cc_2)		
			cc_lose.append(lose_cc)		

		if len(cc_earn) > 0:
			earn_cc = (0,0,{
					'tax_amount': 0.0, 
					'name': 'Diferencia de Cambio Mensual', 
					'ref': False, 
					'currency_id': False,
					'debit': 0.00,
					'credit': total_earn, 
					'date_maturity': False, 
					'date': periodo.date_stop,
					'amount_currency':0.00, 
					'account_id': config_obj.earn_account_id.id,
					'partner_id': False,
					'type_document_it': False,
					'nro_comprobante': 'DIF. CAM. ' + periodo.code,
					})
			if has_extorno:	
				earn_cc_2 = (0,0,{
						'tax_amount': 0.0, 
						'name': 'Diferencia de Cambio Mensual', 
						'ref': False, 
						'currency_id': False,
						'debit': total_earn,
						'credit': 0.00, 
						'date_maturity': False, 
						'date': periodo_next.date_start,
						'amount_currency':0.00, 
						'account_id': config_obj.earn_account_id.id,
						'partner_id': False,
						'type_document_it': False,
						'nro_comprobante': 'DIF. CAM. ' + periodo_next.code,
						})
				cc_earn_ext.append(earn_cc_2)
			cc_earn.append(earn_cc)

		#lst = self.pool.get('account.period').search(cr,uid,[('date_start','<=',fixer.done_date),('date_stop','>=',fixer.done_date)])
		#period_id=lst[0]

		user = self.env['res.users'].browse(self.env.uid)
		journal = self.env['account.journal'].browse(journal_id)
		# raise osv.except_osv('Alerta', cc)					
		obj_sequence = self.env['ir.sequence']
		id_seq = journal.sequence_id.id

		#Creo el asiento de Ganancias
		if len(cc_earn) > 0:
			name=obj_sequence.browse(id_seq).next_by_id()					
			move = {
					'name':name,
					'ref': 'AJUSTE DIF. CAM. ' + periodo.code,
					'line_ids': cc_earn,
					'date': periodo.date_stop,
					'journal_id': journal.id,
					'company_id': user.company_id.id,
				}
			move_obj = self.env['account.move']
			move_id1 = move_obj.create(move)
			move_id_act=move_id1
			move_id1.post()
			#ids_move.append(move_id_act)
			if has_extorno:
				name=obj_sequence.browse(id_seq).next_by_id()
				move = {
						'name':name,
						'ref': 'EXTORNO DIF. CAM. ' + periodo_next.code,
						'line_ids': cc_earn_ext,
						'date': periodo.date_start,
						'journal_id': journal.id,
						'company_id': user.company_id.id,
					}
				move_obj = self.env['account.move']
				move_id1 = move_obj.create( move )
				move_id_act=move_id1
				move_id1.post()

		#Creo el asiento de Perdidas
		if len(cc_lose) > 0:
			name2=obj_sequence.browse(id_seq).next_by_id()
			move2 = {
					'name':name2,
					'ref': 'DIF. CAM. ' + periodo.code,
					'line_ids': cc_lose,
					'date': periodo.date_stop,
					'journal_id': journal.id,
					'company_id': user.company_id.id,
				}
			move_obj2 = self.env['account.move']
			move_id12 = move_obj2.create( move2 )
			move_id_act2=move_id12
			move_id12.post()	
			#XD
			if has_extorno:
				name2=obj_sequence.browse(id_seq).next_by_id()
				move2 = {
						'name':name2,
						'ref': 'EXTORNO DIF. CAM. ' + periodo.code,
						'line_ids': cc_lose_ext,
						'date': periodo_next.date_start,
						'journal_id': journal.id,
						'company_id': user.company_id.id,
					}
				move_obj2 = self.env['account.move']
				move_id12 = move_obj2.create(  move2 )
				move_id_act2=move_id12
				move_id12.post()
		return self.env.context['active_ids']


