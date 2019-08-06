# -*- coding: utf-8 -*-

from odoo import models, fields, api

class product_category(models.Model):

	_inherit = "product.category"
	
	codigo_categoria = fields.Char(string="Codigo")
	

class product_product(models.Model):
	_inherit = 'product.product'

	campo_name_get = fields.Char('Campo Busqueda')

	@api.model
	def create(self,vals):
		t = super(product_product,self).create(vals)
		t.campo_name_get = t.name_get()[0][1]
		return t

	@api.one
	def write(self,vals):
		t = super(product_product,self).write(vals)
		if 'noprocess' in vals:
			pass
		else:
			self.refresh()
			self.write({'noprocess':1,'campo_name_get':self.name_get()[0][1]})
		return t


	@api.model
	def name_search(self,name,args=None,operator='ilike',limit=100):
		if limit > 1 and limit < 10000:
			pass
		else:
			limit = 200
		args = args or []
		domain = []
		products =  self.search([]+args,limit=limit)
		if name:
			namex = name.split(' ')
			do = []
			for i in namex:
				do.append( ('campo_name_get','ilike',i) )

			products = self.search(do+args,limit=limit)
		if not products:
			domain = [ ('default_code','=',name) ]
			products = self.search(domain+args,limit=limit)
		
		return products.name_get()



	@api.onchange('asset_category_id')
	def onchange_asset_category_id(self):
		if self.asset_category_id.id:
			self.property_account_expense_id = self.asset_category_id.account_asset_id.id
			

class product_template(models.Model):
	_inherit = 'product.template'

	analytic_account_id = fields.Many2one('account.analytic.account','Cuenta Analitica')

	@api.model
	def name_search(self,name,args=None,operator='ilike',limit=100):
		if limit > 1 and limit < 10000:
			pass
		else:
			limit = 200
		args = args or []
		domain = []
		products =  self.search([]+args,limit=limit)
		if name:
			namex = name.split(' ')
			do = []
			for i in namex:
				do.append( ('name','ilike',i) )

			products = self.search(do+args,limit=limit)
		if not products:
			domain = [ ('default_code','=',name) ]
			products = self.search(domain+args,limit=limit)
		
		return products.name_get()


	@api.onchange('asset_category_id')
	def onchange_asset_category_id(self):
		if self.asset_category_id.id:
			self.property_account_expense_id = self.asset_category_id.account_asset_id.id