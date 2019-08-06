# -*- coding: utf-8 -*-

from openerp import models, fields, api,exceptions , _
from suds.client import Client
from openerp.osv import osv
import re

class res_partner(models.Model):
	_inherit = 'res.partner'

	ruc_state = fields.Char('RUC Estado')
	ruc_condition = fields.Char(u'RUC Condición')

	@api.model
	def default_get(self,fields):
		res = super(res_partner,self).default_get(fields)
		res['name']        = 'Nombre'
		return res

	@api.one
	def verify_ruc(self):
		client = Client("http://ws.insite.pe/sunat/ruc.php?wsdl",faults=False,cachingpolicy= 1, location= "http://ws.insite.pe/sunat/ruc.php?wsdl")
		result = client.service.consultaRUC(self.nro_documento,"jtejada@itgrupo.net","ZDI-9DJ-YA8-D8C","plain")
		texto = result[1].split('|')
		flag = False
		for i in texto:
			tmp = i.split('=')
			if tmp[0] == 'status_msg' and tmp[1] == 'OK/1':
				flag = True

		print texto
		if flag:
			for j in texto:
				tmp = j.split('=')
				if tmp[0] == 'n1_alias':
					self.name = tmp[1]
				if tmp[0] == 'n1_direccion':
					self.street = tmp[1]
				if tmp[0] == 'n1_ubigeo':
					ubigeo=self.env['res.country.state'].search([('code','=',tmp[1])])
					if ubigeo:
						self.zip = tmp[1]
						pais =self.env['res.country'].search([('code','=','PE')]) 
						ubidepa=tmp[1][0:2]
						ubiprov=tmp[1][0:4]
						ubidist=tmp[1][0:6]

						departamento = self.env['res.country.state'].search([('code','=',ubidepa),('country_id','=',pais.id)])
						provincia  = self.env['res.country.state'].search([('code','=',ubiprov),('country_id','=',pais.id)])
						distrito = self.env['res.country.state'].search([('code','=',ubidist),('country_id','=',pais.id)])

						self.country_id=pais.id
						self.state_id=departamento.id
						self.province_id = provincia.id
						self.district_id = distrito.id
				if tmp[0] == 'n1_estado':
					self.ruc_state = tmp[1]
				if tmp[0] == 'n1_condicion':
					self.ruc_condition = tmp[1]
				
		else:
			raise osv.except_osv( 'Alerta!', "El RUC es invalido.")	
