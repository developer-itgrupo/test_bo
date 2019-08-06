# -*- coding: utf-8 -*-
from openerp import _, api, fields, models
from odoo.osv import expression

class account_config_efective(models.Model):

	_name='account.config.efective'
	_rec_name='code'

	concept = fields.Char(string='Concepto', size=50)
	code = fields.Char(string='Código',size=20)
	group = fields.Selection((
									
									('E1','Ingresos de operación'),
									('E2','Egresos de operación'),
									('E3','Ingresos de Inversión'),
									('E4','Egresos de Inversión'),
									('E5','Ingresos de Financiamiento'),
									('E6','Egresos de Financiamiento'),
									('E7','Saldo Inicial'),
									('E8','Diferencia de cambio'),
									
							  ),'Grupo')
	order = fields.Integer(string='Orden')

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|', ('code', '=ilike', name + '%'), ('concept', operator, name)]
			if operator in expression.NEGATIVE_TERM_OPERATORS:
				domain = ['&', '!'] + domain[1:]
		accounts = self.search(domain + args, limit=limit)
		return accounts.name_get()

class einvoice_means_payment(models.Model):
	_name = 'einvoice.means.payment'
	_description = 'Codigo de Medio de Pago'
	#_rec_name='code'

	code = fields.Char(string='Codigo', index=True, required=True)
	name = fields.Char(string='Descripcion', size=128, index=True, required=True)

	@api.multi
	def name_get(self):
		result = []
		for elem in self:
			if 'get_code' in self.env.context:
				result.append( (elem.id,elem.code) )
			else:
				result.append( (elem.id,elem.name) )
		return result


	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
			if operator in expression.NEGATIVE_TERM_OPERATORS:
				domain = ['&', '!'] + domain[1:]
		accounts = self.search(domain + args, limit=limit)
		return accounts.name_get()

class einvoice_catalog_01(models.Model):
	_name = "einvoice.catalog.01"
	_description = 'Codigo de Tipo de documento'

	code = fields.Char(string='Codigo', size=4, index=True, required=True)
	name = fields.Char(string='Descripcion', size=128, index=True, required=True)
	n_serie = fields.Integer('Digitos Serie',default= 0)
	n_documento = fields.Integer('Digitos Numero',default= 0)
	
	@api.multi
	@api.depends('code', 'name')
	def name_get(self):
		result = []
		for table in self:
			l_name = table.name
			if 'get_code' in self.env.context: 
				l_name = table.code
			result.append((table.id, l_name ))
		return result

		
	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
			if operator in expression.NEGATIVE_TERM_OPERATORS:
				domain = ['&', '!'] + domain[1:]
		accounts = self.search(domain + args, limit=limit)
		return accounts.name_get()




class einvoice_catalog_06(models.Model):
	_name = "einvoice.catalog.06"
	_description = 'Tipo de documento de Identidad'

	code = fields.Char(string='Codigo', size=4, index=True, required=True)
	name = fields.Char(string='Descripcion', size=128, index=True, required=True)
	default = fields.Char(string='Valor por defecto', size=128)
	
	@api.multi
	@api.depends('code', 'name')
	def name_get(self):
		result = []
		for table in self:
			l_name = table.code and table.code + ' - ' or ''
			l_name +=  table.name
			result.append((table.id, l_name ))
		return result
		
class einvoice_catalog_07(models.Model):
	_name = "einvoice.catalog.07"
	_description = 'Codigos de Tipo de Afectacion del IGV'

	code = fields.Char(string='Codigo', size=4, index=True, required=True)
	name = fields.Char(string='Descripcion', size=128, index=True, required=True)
	no_onerosa = fields.Boolean(string='No onerosa')
	type = fields.Selection([('gravado','Gravado'),('exonerado','Exonerado'),('inafecto','Inafecto')],string='Tipo')
	
	@api.multi
	@api.depends('code', 'name')
	def name_get(self):
		result = []
		for table in self:
			l_name = table.code and table.code + ' - ' or ''
			l_name +=  table.name
			result.append((table.id, l_name ))
		return result

class einvoice_catalog_08(models.Model):
	_name = "einvoice.catalog.08"
	_description = 'Codigos de Tipo de Afectacion del IGV'

	code = fields.Char(string='Codigo', size=4, index=True, required=True)
	name = fields.Char(string='Descripcion', size=128, index=True, required=True)
	
	@api.multi
	@api.depends('code', 'name')
	def name_get(self):
		result = []
		for table in self:
			l_name = table.code and table.code + ' - ' or ''
			l_name +=  table.name
			result.append((table.id, l_name ))
		return result

class einvoice_catalog_09(models.Model):
	_name = "einvoice.catalog.09"
	_description = 'Codigos de Tipo de Nota de Credito Electronica'

	code = fields.Char(string='Codigo', size=4, index=True, required=True)
	name = fields.Char(string='Descripcion', size=128, index=True, required=True)
	
	@api.multi
	@api.depends('code', 'name')
	def name_get(self):
		result = []
		for table in self:
			l_name = table.code and table.code + ' - ' or ''
			l_name +=  table.name
			result.append((table.id, l_name ))
		return result

class einvoice_catalog_10(models.Model):
	_name = "einvoice.catalog.10"
	_description = 'Codigos de Tipo de Nota de Debito Electronica'

	code = fields.Char(string='Codigo', size=4, index=True, required=True)
	name = fields.Char(string='Descripcion', size=128, index=True, required=True)
	
	@api.multi
	@api.depends('code', 'name')
	def name_get(self):
		result = []
		for table in self:
			l_name = table.code and table.code + ' - ' or ''
			l_name +=  table.name
			result.append((table.id, l_name ))
		return result

class einvoice_catalog_16(models.Model):
	_name = "einvoice.catalog.16"
	_description = 'Codigos - Tipo de Precio de Venta Unitario'

	code = fields.Char(string='Codigo', size=4, index=True, required=True)
	name = fields.Char(string='Descripcion', size=128, index=True, required=True)
	
	@api.multi
	@api.depends('code', 'name')
	def name_get(self):
		result = []
		for table in self:
			l_name = table.code and table.code + ' - ' or ''
			l_name +=  table.name
			result.append((table.id, l_name ))
		return result
