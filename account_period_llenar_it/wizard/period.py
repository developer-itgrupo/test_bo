# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp import models, fields, api


class account_period_llenar_wizard(osv.TransientModel):
	_name='account.period.llenar.wizard'
	
	fiscal_id = fields.Many2one('account.fiscalyear','Año Fiscal',required=True)
	
	@api.multi
	def do_rebuild(self):
		from datetime import datetime, timedelta
		day = 1
		month = 1
		year = int(self.fiscal_id.name)



		busqueda = self.env['account.period'].search([('date_start','=', self.fiscal_id.name+ '-01-01'),('date_stop','=',self.fiscal_id.name+ '-01-01'),('fiscalyear_id','=',self.fiscal_id.id)])
		if len(busqueda)==0:
			datae= {
				'date_start':self.fiscal_id.name+'-01-01',
				'date_stop': self.fiscal_id.name+'-01-01',
				'fiscalyear_id':self.fiscal_id.id,
				'name': '00/' + self.fiscal_id.name ,
				'code': '00/' + self.fiscal_id.name ,
				'state':'draft',
				'special':True,
			}
			self.env['account.period'].create(datae)
			
		for fech in range(12):
			dia_1 = datetime(day=day,month=month,year=year)
			month+= 1
			if month == 13:
				month= 1
				year+= 1

			dia_2 = datetime(day=day,month=month,year=year) - timedelta(days=1)
			busqueda = self.env['account.period'].search([('date_start','=',str(dia_1)[:10]),('date_stop','=',str(dia_2)[:10]),('fiscalyear_id','=',self.fiscal_id.id)])
			if len(busqueda)==0:
				data = {
					'date_start':str(dia_1)[:10],
					'date_stop':str(dia_2)[:10],
					'fiscalyear_id':self.fiscal_id.id,
					'name': str(dia_1.month).rjust(2).replace(' ','0') + '/' + self.fiscal_id.name ,
					'code': str(dia_1.month).rjust(2).replace(' ','0') + '/' + self.fiscal_id.name ,
					'state':'draft',
					'special':False,
				}
				self.env['account.period'].create(data)


		busqueda = self.env['account.period'].search([('date_start','=',self.fiscal_id.name+ '-12-31'),('date_stop','=', self.fiscal_id.name+'-12-31'),('fiscalyear_id','=',self.fiscal_id.id)])
		if len(busqueda)==0:
			datae= {
				'date_start':self.fiscal_id.name+'-12-31',
				'date_stop': self.fiscal_id.name+'-12-31',
				'fiscalyear_id':self.fiscal_id.id,
				'name': '13/' + self.fiscal_id.name ,
				'code': '13/' + self.fiscal_id.name ,
				'state':'draft',
				'special':True,
			}
			self.env['account.period'].create(datae)
