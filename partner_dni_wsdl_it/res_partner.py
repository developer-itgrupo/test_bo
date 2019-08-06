# -*- coding: utf-8 -*-

from openerp import models, fields, api,exceptions , _
from suds.client import Client
from openerp.osv import osv
import re

class res_partner(models.Model):
	_inherit = 'res.partner'

	@api.model
	def default_get(self,fields):
		res = super(res_partner,self).default_get(fields)
		res['name']        = 'Nombre'
		res['nombre']  = 'Nombre'
		res['apellido_p'] = 'Apellido Paterno'
		res['apellido_m'] = 'Apellido Materno'
		return res

	@api.onchange('company_type')
	def _set_street_default(self):
		if self.company_type == 'company':
			if len(self.type_document_partner_it) > 0:
				if self.type_document_partner_it[0].code == '6':
					self.street = 'Calle'
		else:
			self.street = ''
	@api.onchange('type_document_partner_it')
	def _verify_document(self):
		if len(self.type_document_partner_it) > 0:
			if self.type_document_partner_it[0].code == '6' and self.company_type == 'company':
				self.street = 'Calle'
			else:
				self.street = ''
		else:
			self.street = ''

	@api.multi
	def verify_dni(self):
		if self.nro_documento == False:
			raise osv.except_osv('Alerta!',"Debe seleccionar un DNI")
		client = Client("http://reniec.insite.pe/soap?wsdl",faults=False,cachingpolicy= 1, location= "http://reniec.insite.pe/index.php/soap?wsdl")
		print("DNI",str(self.nro_documento))
		try: 
			result = client.service.consultar(str(self.nro_documento),"jtejada@itgrupo.net","ZDI-9DJ-YA8-D8C","plain")
		except Exception as e:
			raise osv.except_osv('Alerta!','No se encontro el DNI')
		print('result',result)
		texto = result[1].split('|')
		flag = False
		nombres = ''
		a_paterno = ''
		a_materno = ''
		for c in texto:
			tmp = c.split('=')
			if tmp[0] == 'status_id' and tmp[1] == '102':
				raise osv.except_osv('Alerta!','El DNI debe tener al menos 8 digitos de longitud')
			if tmp[0] == 'status_id' and tmp[1] == '103':
				raise osv.except_osv('Alerta!','El DNI debe ser un valor numerico')
			if tmp[0] == 'reniec_nombres' and tmp[1] != '':
				nombres = tmp[1]
				self.nombre = tmp[1]
			if tmp[0] == 'reniec_paterno' and tmp[1] != '':
				a_paterno = tmp[1]
				self.apellido_p = tmp[1]
			if tmp[0] == 'reniec_materno' and tmp[1] != '':
				a_materno = tmp[1]
				self.apellido_m = tmp[1]
		self.name = (nombres + " " + a_paterno + " " + a_materno).strip()
