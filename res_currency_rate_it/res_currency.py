# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class res_currency_rate(models.Model):
	_inherit = 'res.currency.rate'

	period_name = fields.Char("Periodo", size=50 )

	@api.multi
	def write(self,vals):
		if not vals:
			vals = {}

		date_tmp = "Indefinido"
		if 'name' in vals:
			date_tmp = str(vals['name'])[:7].replace("-","/")

		if self.name:
			date_tmp = str(self.name)[:7].replace("-","/")
		vals['period_name'] = date_tmp
		t = super(res_currency_rate,self).write(vals)
		
		return t

	@api.model
	def create(self,vals):
		if not vals:
			vals={}
		t = super(res_currency_rate,self).create(vals)
		if t.name:
			t.period_name = str(t.name)[:7].replace("-","/")
		else:
			t.period_name = "Indefinido"
		
		return t






class res_currency_wizard_optional(models.Model):
	_name="res.currency.wizard.optional"

	check_type = fields.Selection([('auto', 'Automático'),
                                   ('manual', 'Manual')], 'Modalidad')
	fecha_ini = fields.Date("Fecha Inicio")
	fecha_fin = fields.Date("Fecha Final")
	fecha_unica= fields.Date("Fecha")
	type_compra = fields.Float("Valor de Compra", digits=(12,3))
	type_venta = fields.Float("Valor de Venta",digits=(12,3))

	@api.onchange('fecha_ini')
	def _onchange_type_account(self):
		import datetime
		if self.fecha_ini:
			if self.fecha_ini > str(datetime.datetime.now()):
				self.fecha_ini =""
		if self.fecha_ini:
			self.fecha_fin = self.fecha_ini



	@api.onchange('fecha_fin')
	def _onchange_type_fin_account(self):
		import datetime
		if self.fecha_fin:
			if self.fecha_fin > str(datetime.datetime.now()):
				self.fecha_fin =""

	@api.multi
	def do_rebuild(self):
		if self.check_type == 'auto':
			self.do_auto()
		else:
			self.do_manual()

		return {
			'domain' : [('currency_id.name','=', 'USD')],
			'type': 'ir.actions.act_window',
			'res_model': 'res.currency.rate',
			'view_mode': 'tree',
			'view_type': 'form',
		}


	@api.multi
	def do_manual(self):
		currency_extra = self.env['res.currency'].search([('name','=','USD')])[0]

		tmp_fn = self.env['res.currency.rate'].search([('currency_id','=',currency_extra.id),('name','=',str(self.fecha_unica))])
		
		if len(tmp_fn)>0:
			tmp_fn.type_purchase =  float(self.type_compra)
			tmp_fn.type_sale = float(self.type_venta)
			tmp_fn.rate = 1 /float(self.type_venta)
		else:

			import datetime
			date_sunat_obj = datetime.datetime.strptime(str(self.fecha_unica),'%Y-%m-%d')

			data = {
			#'date_sunat':self.fecha_unica,
			'name':self.fecha_unica,
			'type_purchase' :  float(self.type_compra),
			'type_sale' : float(self.type_venta),
			'rate' : 1 /float(self.type_venta),
			'tipo' : 'Manual',
			}
			print data
			new_rate= self.env['res.currency.rate'].create(data)
			print new_rate
			currency_extra.write({'rate_ids':[(4,new_rate.id)]})
			
	@api.multi
	def do_auto(self):

		import urllib, urllib2
		import datetime
		import pprint
		fecha_inicial = datetime.datetime.strptime(self.fecha_ini, '%Y-%m-%d')
		fecha_final = datetime.datetime.strptime(self.fecha_fin, '%Y-%m-%d')

		mesini = fecha_inicial.month -1
		aoini = fecha_inicial.year
		if mesini == 0:
			mesini = 12
			aoini += -1
		mes_ini = datetime.datetime(year=aoini,month = mesini,day=1)
		mes_fin = datetime.datetime(year=fecha_final.year,month = fecha_final.month,day=1)
		rango_mes = []

		while mes_ini!=mes_fin:
			rango_mes.append( [str(mes_ini.month),str(mes_ini.year)] )
			mes_ini = datetime.datetime(year=mes_ini.year +int((mes_ini.month+1)/13),month = (mes_ini.month%12)+1,day=1)

		rango_mes.append([str(mes_ini.month),str(mes_ini.year)])
			
		saldos = []
		dato_sal = [0,0,0]
		cont = 0
		diaanterior = None
		for meses in rango_mes:
			mes = meses[0]
			anho = meses[1]
			datos = urllib.urlencode({'mes':mes, 'anho':anho})
			url = "http://www.sunat.gob.pe/cl-at-ittipcam/tcS01Alias?"
			try:
				res = urllib2.urlopen(url + datos)
			except:
				raise UserError('No se puede conectar a la página de Sunat!')
			from BeautifulSoup import BeautifulSoup
			soup = BeautifulSoup(res.read())
			table = soup.findAll('table')[1]

			for i in table.findAll("tr")[1:]:
				for j in i.findAll("td"):
					dato_sal[cont]=j.text
					if cont == 2:
						dia_actual = datetime.datetime(year=int(anho),month=int(mes),day=int(dato_sal[0]))
						while (diaanterior and diaanterior + datetime.timedelta(days=1) != dia_actual):
							diaanterior = diaanterior + datetime.timedelta(days=1)
							saldos.append( [diaanterior,diaanterior.day,saldos[-1][2],saldos[-1][3] ] )
							
						saldos.append([dia_actual,dato_sal[0],dato_sal[1],dato_sal[2]])
						diaanterior = dia_actual
					cont = (cont+1)%3

		dic_sal = {}
		for i in saldos:
			dic_sal[i[0]] = [i[2],i[3]]


		fecha_inicial = mes_ini
		final = []
		while fecha_inicial<=fecha_final:
			if fecha_inicial in dic_sal:
				final.append([fecha_inicial,dic_sal[fecha_inicial][0],dic_sal[fecha_inicial][1] ])
			else:
				dic_sal[fecha_inicial] = dic_sal[fecha_inicial - datetime.timedelta(days=1)]
				final.append([fecha_inicial,dic_sal[fecha_inicial][0],dic_sal[fecha_inicial][1] ])
			fecha_inicial = fecha_inicial + datetime.timedelta(days= 1)
		

		currency_extra = self.env['res.currency'].search([('name','=','USD')])[0]
		for fn in final:
			tmp_fn = self.env['res.currency.rate'].search([('currency_id','=',currency_extra.id),('name','=',str(fn[0]))])
			if len(tmp_fn)>0:
				tmp_fn.type_purchase =  float(fn[1])
				tmp_fn.type_sale = float(fn[2])
				tmp_fn.rate = 1 /float(fn[2])
			else:
				data = {
				#'date_sunat':fn[0],
				'name':fn[0] ,
				'type_purchase' :  float(fn[1]),
				'type_sale' : float(fn[2]),
				'rate' : 1 /float(fn[2]),
				'period_name': str(fn[0])[:7].replace("-","/"),
				'tipo': 'Automatico',
				}
				new_rate= self.env['res.currency.rate'].create(data)
				currency_extra.write({'rate_ids':[(4,new_rate.id)]})
