# -*- encoding: utf-8 -*-
from openerp.osv import osv

from openerp import models, fields, api
from datetime import *
from odoo.exceptions import UserError, ValidationError

class account_account_analytic_wizard(osv.TransientModel):
	_name='account.account.analytic.wizard'
	
	period_ini =fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end =fields.Many2one('account.period','Periodo Final',required=True)

	@api.model
	def get_wizard(self):
		return self.env['automatic.fiscalyear'].get_wizard('Analisis Destinos',self.id,'account.account.analytic.wizard','account_analisis_destino_it.view_account_account_analytic_wizard_form','default_period_ini','default_period_end')

	@api.onchange('period_ini','period_end')
	def _change_periodo_ini(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
		if not year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			return {'domain':{'period_ini':[('fiscalyear_id','=',year.id )],'period_end':[('fiscalyear_id','=',year.id )]}}

	@api.multi
	def do_rebuild(self):

		aaar_obj = self.env['account.account.analytic.rep']

		fechaini_obj = self.period_ini
		fechafin_obj = self.period_end
		
		lstidsaaar = aaar_obj.search([('fecha_ini','>=',fechaini_obj.date_start),('fecha_fin','<=',fechafin_obj.date_stop)])
		
		if (len(lstidsaaar) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')
		
		domain_tmp= [('fecha_ini','>=',fechaini_obj.date_start),('fecha_fin','<=',fechafin_obj.date_stop)]
		
		return {
			'domain' : domain_tmp,
			'type': 'ir.actions.act_window',
			'res_model': 'account.account.analytic.rep',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
		}






class account_account_analytic_asiento_wizard(osv.TransientModel):
	_name='account.account.analytic.asiento.wizard'

	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	

	@api.multi
	def do_rebuild(self):

		fechaD = self.period_ini.date_stop
		fecha_obj = self.period_ini
		lst_journals = self.env['account.journal'].search([('is_journal_unic','=','True')])

		if (len(lst_journals) == 0) :
			raise osv.except_osv('Alerta','No tiene configurado el Diario para el Asiento Unico.')
		move_obj=self.env['account.account.analytic.rep.contable.unico']
		
		mlra_obj = move_obj.search([('period','=',fecha_obj.id)])
		if (len(mlra_obj) == 0):
			raise osv.except_osv('Alerta','No contiene datos o no esta configurado sus cuentas de amarre.')
		
		periodo = fecha_obj
		lineas = []
		for mlra in mlra_obj:
			debit = round(mlra.debe,2)
			credit = round(mlra.haber,2)
			vals = (0,0,{
				'analytic_account_id': False, 
				'tax_code_id': False, 
				'analytic_lines': [], 
				'tax_amount': 0.0, 
				'name': "%s"%('Asiento de Destino Clase 9 para '+periodo.name), 
				'ref': 'Asiento de Destino Clase 9 para '+periodo.name, 
				'debit': debit,
				'credit': credit, 
				'product_id': False, 
				'date_maturity': False, 
				'date': fechaD,
				'product_uom_id': False, 
				'quantity': 0, 
				'partner_id': False, 
				'account_id': int(mlra.cuenta),
				'analytic_line_id': False,
				'nro_comprobante': 'DEST-'+periodo.name,
			})
			lineas.append(vals)
			
		move_id = self.env['account.move'].create({
			'company_id': periodo.company_id.id,
			'journal_id': lst_journals.id,
			'period_id': periodo.id,
			'date': fechaD,
			'ref': 'DEST-'+periodo.name, 
			'line_id':lineas})			
		return True