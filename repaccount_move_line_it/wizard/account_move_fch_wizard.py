# -*- encoding: utf-8 -*-
from odoo.osv import osv

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError, ValidationError


class account_move(models.Model):
	_name='account.move'
	_inherit='account.move'
	automatic_destiny = fields.Boolean('Destino Automatico')



class account_move_line_rep_asiento_wizard(models.TransientModel):
	_name='account.move.line.rep.asiento.wizard'

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

	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True,default=lambda self:self.get_period())
	journal_id = fields.Many2one('account.journal','Libro',required=True, domain="[('type', '=', 'general')]")
	fecha = fields.Date('Fecha Asiento',required=True)
	
	@api.onchange('period_ini')
	def onchange_fiscalyear(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
		if not year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			return {'domain':{'period_ini':[('fiscalyear_id','=',year.id )]}}

	@api.multi
	def do_Clase9(self):

		fechaD = self.fecha
		periodo = self.period_ini
		lst_journals = self.journal_id
		if fechaD < periodo.date_start or fechaD > periodo.date_stop:
		 	raise ValidationError('Fecha fuera del rango del periodo seleccionado')

		asiento_delete = self.env['account.move'].search([('automatic_destiny','=',True),('fecha_contable','>=',periodo.date_start),('fecha_contable','<=',periodo.date_stop) ])
		if asiento_delete or len(asiento_delete)>0:

			for move in asiento_delete:
				move.button_cancel()
				for lineas in move.line_ids:
					lineas.unlink()
				move.unlink()
		
		consulta = """select * from (
		select cuenta,period,sum(debe) as debe,0 as haber from account_analytic_destino
		where debe != 0
		group by cuenta,period

		union all

		select cuenta,period,0 as debe,sum(haber) as haber from account_analytic_destino
		where haber != 0
		group by cuenta,period) x
		where period="""+str(periodo.id)+"""
		order by period,debe,cuenta"""

		self.env.cr.execute(consulta)
		obj =self.env.cr.fetchall()
		lineas = []
		for elemnt in obj:
			vals = (0,0,{
				'name': "%s"%('DEST-'+periodo.name), 
				'ref': 'DEST-'+periodo.name, 
				'debit': elemnt[2],
				'credit': elemnt[3], 
				'date': fechaD,
				'account_id': elemnt[0],
				'nro_comprobante': 'DEST-'+periodo.name,
				'glosa': 'DEST-',
			})
			lineas.append(vals)
		
		
		compani_id = self.env['res.company'].search([])[0].id
			
		move_id = self.env['account.move'].create({
			'company_id': compani_id,
			'journal_id': lst_journals.id,
			'period_id': periodo.id,
			'date': fechaD,
			'automatic_destiny':True,
			'ref': 'DEST-'+periodo.name, 
			'line_ids':lineas})
		if move_id.state == "draft":
			move_id.post()
		return True




	@api.multi
	def do_rebuild(self):
		t_c9 = self.do_Clase9()
		rep = ""
		if t_c9 == -1:
			rep += "\nDestino: No contiene datos o no esta configurado sus cuentas de amarre.\n"
		else:
			rep += "\nDestino: Se genero exitosamente.\n"
		 
		return {
			'name':'Exitoso',
			'type':'ir.actions.act_window',
			'view_type':'form',
			'view_mode':'form',
			'res_model':'sh.message.wizard',
			'target':'new',
			'context':{'message':"Se ha generado el asiento contable del destino en el diario asientos automaticos para el periodo '"+self.period_ini.code+"'."}
		}