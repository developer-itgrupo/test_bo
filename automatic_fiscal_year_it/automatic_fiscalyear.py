# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import *
from odoo.exceptions import UserError, ValidationError

class AutomaticFiscalyear(models.Model):
	_name = 'automatic.fiscalyear'

	def get_min_max_period(self,periods,flag=False):
		ac = []
		ac = filter(lambda periodo: not periodo.special,periods)
		if flag:
			apertura = [(i.date_start) for i in ac if not i.special]
			apertura = min(apertura) if len(apertura) > 0 else None
			apertura = filter(lambda period: not period.special and period.date_start == apertura,periods)
			return apertura[0]
		else:
			cierre = [(i.date_stop) for i in ac if not i.special]
			cierre = max(cierre) if len(cierre) > 0 else None
			cierre = filter(lambda period: not period.special and period.date_stop == cierre,periods)
			return cierre[0]

	@api.model
	def get_wizard(self,name,res_id,model,ref,period_ini='dummy',period_fin='dummy'):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
		if not year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			wizard = {
					'name':_(name),
					'res_id':res_id,
					'view_type':'form',
					'view_mode':'form',
					'res_model':model,
					'views':[[self.env.ref(ref).id,'form']],
					'type':'ir.actions.act_window',
					'target':'new'}
			dates,aux = [],[]
			apertura,cierre = None,None
			periodos = self.env['account.period'].search([('fiscalyear_id','=',year.id)])
			apertura_cierre = filter(lambda periodo:periodo.special,periodos)
			if len(apertura_cierre) > 2:
				raise UserError(u'Se han encontrado mas de dos periodos de apertura y cierre en el mismo año revise sus periodos por favor')
			elif len(apertura_cierre) == 2:
				for i in apertura_cierre:
					if i.name.split('/')[0] == '00':
						apertura = i
					if i.name.split('/')[0] == '13':
						month,day = datetime.now().month,datetime.now().day
						if month == datetime.strptime(i.date_stop,"%Y-%m-%d").month and day == datetime.strptime(i.date_stop,"%Y-%m-%d").day:
							cierre = i
						else:
							cierre = filter(lambda periodo: not periodo.special and datetime.strptime(periodo.date_start,"%Y-%m-%d").month == month,periodos)
							if len(cierre) > 0:
								cierre = cierre[0]
							else:
								cierre = self.get_min_max_period(periodos)
				wizard['context'] = {period_ini:apertura.id,period_fin:cierre.id}
				return wizard
			elif len(apertura_cierre) == 1:
				if apertura_cierre[0].name.split('/')[0] == '00':
					apertura = apertura_cierre[0]
					month,day = datetime.now().month, datetime.now().day
					if day == 1 and month == 1:
						wizard['context'] = {period_ini:apertura.id,period_fin:apertura.id}
					else:
						per_cierre = filter(lambda periodo: not periodo.special and datetime.strptime(periodo.date_start,"%Y-%m-%d").month == month,periodos)
						per_cierre = per_cierre[0] if len(per_cierre) > 0 else self.get_min_max_period(periodos)
						wizard['context'] = {period_ini:apertura.id,period_fin:per_cierre.id}
					return wizard
				else:
					month,day = datetime.now().month,datetime.now().day
					if month == datetime.strptime(apertura_cierre[0].date_stop,"%Y-%m-%d").month and day == datetime.strptime(apertura_cierre[0].date_stop,"%Y-%m-%d").day:
						cierre = apertura_cierre[0]
					else:
						cierre = filter(lambda periodo: not periodo.special and datetime.strptime(periodo.date_start,"%Y-%m-%d").month == month,periodos)
						if len(cierre) > 0:
							cierre = cierre[0]
						else:
							cierre = self.get_min_max_period(periodos)
					per_apertura = self.get_min_max_period(periodos,True)
					wizard['context'] = {period_ini:per_apertura.id,period_fin:cierre.id}
					return wizard
			else:
				apertura = self.get_min_max_period(periodos,True)
				month = datetime.now().month
				cierre = filter(lambda periodo: not periodo.special and datetime.strptime(periodo.date_start,"%Y-%m-%d").month == month,periodos)
				cierre = cierre[0] if len(cierre) > 0 else self.get_min_max_period(periodos)
				wizard['context'] = {period_ini:apertura.id,period_fin:cierre.id}
				return wizard