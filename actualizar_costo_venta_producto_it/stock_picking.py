# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
import base64
import sys
from odoo.exceptions import UserError
import pprint
from odoo.exceptions import ValidationError

class product_product(models.Model):
	_inherit = 'product.product'

	@api.multi
	def actualizar_costo_promedio(self):
		if True:
			s_prod = [-1,-1,-1]
			s_loca = [-1,-1,-1]
			productos='(0,'
			almacenes='(0,'
			
			lst_products  = self.env['product.product'].search([])

			for producto in lst_products:
				productos=productos+str(producto.id)+','
				s_prod.append(producto.id)
			productos=productos[:-1]+')'

			lst_locations  = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])

			for location in lst_locations:
				almacenes=almacenes+str(location.id)+','
				s_loca.append(location.id)
			almacenes=almacenes[:-1]+')'

			param = self.env['main.parameter'].search([])
			date_ini= str(param.fiscalyear) + '-01-01'
			date_fin= str(param.fiscalyear) + '-12-31'



			self.env.cr.execute("""
			insert into ir_property(value_float, name, res_id, type,fields_id)
			select 0 as value_float, 'standard_price' as name, 'product.product,' || product_id as res_id, 'float' as type,(select id from ir_model_fields where model = 'product.product' and name = 'standard_price' and ttype = 'float' ) as fields_id  from (
			select 
				CASE WHEN coalesce(sum(ingreso),0) != 0 THEN round(coalesce(sum(coalesce(debit)),0) / coalesce(sum(coalesce(ingreso,0)),0),2) else 0 end as pu,product_id
				from vst_kardex_fisico_valorado_simplificado	
				left join stock_location a1 on a1.id = 	vst_kardex_fisico_valorado_simplificado.id_origen
				left join stock_location a2 on a2.id = 	vst_kardex_fisico_valorado_simplificado.id_destino	
		
				where vst_kardex_fisico_valorado_simplificado.product_id in """ +productos+ """ and vst_kardex_fisico_valorado_simplificado.location_id in """ +almacenes+ """	and (coalesce(a1.usage,'none') != 'internal' or coalesce(a2.usage,'none') != 'internal')
				group by product_id order by product_id ) T
		left join (
			SELECT id, value_float, name, res_id
			FROM ir_property
			WHERE name='standard_price' order by id ) R on R.res_id = ('product.product,' || T.product_id )
																				where R.id is null
																				""")



			self.env.cr.execute(""" 
				update ir_property set value_float = T.valor from (
				select 
				CASE WHEN coalesce(sum(ingreso),0) != 0 THEN round(coalesce(sum(coalesce(debit)),0) / coalesce(sum(coalesce(ingreso,0)),0),2) else 0 end as valor,product_id
				from vst_kardex_fisico_valorado_simplificado
				left join stock_location a1 on a1.id = 	vst_kardex_fisico_valorado_simplificado.id_origen
				left join stock_location a2 on a2.id = 	vst_kardex_fisico_valorado_simplificado.id_destino	
			
				where vst_kardex_fisico_valorado_simplificado.product_id in """ +productos+ """ and vst_kardex_fisico_valorado_simplificado.location_id in """ +almacenes+ """	and (coalesce(a1.usage,'none') != 'internal' or coalesce(a2.usage,'none') != 'internal')
				group by product_id order by product_id ) T where ( 'product.product,' || T.product_id ) = ir_property.res_id

			""")

				

class stock_picking(models.Model):
	_inherit = 'stock.picking'
 
	@api.multi
	def do_transfer(self):

		t = super(stock_picking,self).do_transfer()

		if self.location_dest_id.usage != 'internal':
			return t
		print("entro123")
		purchase_order = self.env['purchase.order'].search([('name','=',self.origin)],limit=1)
		currency_obj = self.env['res.currency'].search([('name','=',purchase_order.currency_id.name)])
		if len(currency_obj)>0:
			currency_obj = currency_obj[0]
		else:
			currency_obj = self.env['res.currency'].search([('name','=','PEN')])
			currency_obj = currency_obj[0]

		fecha = self.fecha_kardex
		tipo_cambio = self.env['res.currency.rate'].search([('name','=',fecha),('currency_id','=',currency_obj.id)])

		if len(tipo_cambio)>0:
			tipo_cambio = tipo_cambio[0]
		else:
			if currency_obj.name != 'PEN':
				raise UserError( 'Error!\nNo existe el tipo de cambio para la fecha: '+ str(fecha) )        
		
		s_prod = []
		s_loca = []
		

		for elem_pro in self.move_lines:
			s_prod.append(elem_pro.product_id.id)

		productos='(0,'
		almacenes='(0,'
		
		for producto in s_prod:
			productos=productos+str(producto)+','
		productos=productos[:-1]+')'

		lst_locations  = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])

		for location in lst_locations:
			almacenes=almacenes+str(location.id)+','
			s_loca.append(location.id)
		almacenes=almacenes[:-1]+')'

		import datetime
		fecha_final = self.fecha_kardex
		if not fecha_final:
			fecha_final = str (datetime.datetime.now() )[:10]
		date_ini=fecha_final.split('-')[0] + '-01-01'
		date_fin=fecha_final.split('-')[0] + '-12-31'
		


		self.env.cr.execute("""
		insert into ir_property(value_float, name, res_id, type,fields_id)
		select 0 as value_float, 'standard_price' as name, 'product.product,' || product_id as res_id, 'float' as type,(select id from ir_model_fields where model = 'product.product' and name = 'standard_price' and ttype = 'float' ) as fields_id  from (
		select 
			CASE WHEN coalesce(sum(ingreso),0) != 0 THEN round(coalesce(sum(coalesce(debit)),0) / coalesce(sum(coalesce(ingreso,0)),0),2) else 0 end as pu,product_id
			from vst_kardex_fisico_valorado_simplificado	
				left join stock_location a1 on a1.id = 	vst_kardex_fisico_valorado_simplificado.id_origen
				left join stock_location a2 on a2.id = 	vst_kardex_fisico_valorado_simplificado.id_destino	
		
				where vst_kardex_fisico_valorado_simplificado.product_id in """ +productos+ """ and vst_kardex_fisico_valorado_simplificado.location_id in """ +almacenes+ """	and (coalesce(a1.usage,'none') != 'internal' or coalesce(a2.usage,'none') != 'internal')
			group by product_id order by product_id ) T
	left join (
		SELECT id, value_float, name, res_id
		FROM ir_property
		WHERE name='standard_price' order by id ) R on R.res_id = ('product.product,' || T.product_id )
																			where R.id is null
																			""")



		self.env.cr.execute(""" 
			update ir_property set value_float = T.valor from (
			select 
			CASE WHEN coalesce(sum(ingreso),0) != 0 THEN round(coalesce(sum(coalesce(debit)),0) / coalesce(sum(coalesce(ingreso,0)),0),2) else 0 end as valor,product_id
			from vst_kardex_fisico_valorado_simplificado
				left join stock_location a1 on a1.id = 	vst_kardex_fisico_valorado_simplificado.id_origen
				left join stock_location a2 on a2.id = 	vst_kardex_fisico_valorado_simplificado.id_destino	
			
				where vst_kardex_fisico_valorado_simplificado.product_id in """ +productos+ """ and vst_kardex_fisico_valorado_simplificado.location_id in """ +almacenes+ """	and (coalesce(a1.usage,'none') != 'internal' or coalesce(a2.usage,'none') != 'internal')
			group by product_id order by product_id ) T where ( 'product.product,' || T.product_id ) = ir_property.res_id

		""")



		return t


	#DESCOMENTASR ESTA FUNCION DONDE SE AGREGAN FUNCIONALIDADES AL REOPEN PARA PODER UTILIZAR EL MODULO DE REOPEN
	# @api.multi
	# def action_revert_done(self):
	# 	t = super(stock_picking,self).action_revert_done()

	# 	if self.location_dest_id.usage != 'internal':
	# 		return t

	# 	purchase_order = self.env['purchase.order'].search([('name','=',self.origin)],limit=1)
	# 	currency_obj = self.env['res.currency'].search([('name','=',purchase_order.currency_id.name)])
	# 	if len(currency_obj)>0:
	# 		currency_obj = currency_obj[0]
	# 	else:
	# 		currency_obj = self.env['res.currency'].search([('name','=','PEN')])
	# 		currency_obj = currency_obj[0]

	# 	fecha = self.fecha_kardex
	# 	tipo_cambio = self.env['res.currency.rate'].search([('name','=',fecha),('currency_id','=',currency_obj.id)])

	# 	if len(tipo_cambio)>0:
	# 		tipo_cambio = tipo_cambio[0]
	# 	else:
	# 		if currency_obj.name != 'PEN':
	# 			raise UserError( 'Error!\nNo existe el tipo de cambio para la fecha: '+ str(fecha) )           
		
	# 	s_prod = [-1,-1,-1]
	# 	s_loca = [-1,-1,-1]
		

	# 	for elem_pro in self.move_lines:
	# 		s_prod.append(elem_pro.product_id.id)

	# 	productos='(0,'
	# 	almacenes='(0,'
		
	# 	for producto in s_prod:
	# 		productos=productos+str(producto)+','
	# 	productos=productos[:-1]+')'

	# 	lst_locations  = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])

	# 	for location in lst_locations:
	# 		almacenes=almacenes+str(location.id)+','
	# 		s_loca.append(location.id)
	# 	almacenes=almacenes[:-1]+')'

	# 	import datetime
	# 	fecha_final = self.fecha_kardex
	# 	if not fecha_final:
	# 		fecha_final = str (datetime.datetime.now() )[:10]
	# 	date_ini=fecha_final.split('-')[0] + '-01-01'
	# 	date_fin=fecha_final.split('-')[0] + '-12-31'



	# 	self.env.cr.execute("""
	# 	insert into ir_property(value_float, name, res_id, type,fields_id)
	# 	select 0 as value_float, 'standard_price' as name, 'product.product,' || product_id as res_id, 'float' as type,(select id from ir_model_fields where model = 'product.product' and name = 'standard_price' and ttype = 'float' ) as fields_id  from (
	# 	select 
	# 		CASE WHEN coalesce(sum(ingreso),0) != 0 THEN round(coalesce(sum(coalesce(debit)),0) / coalesce(sum(coalesce(ingreso,0)),0),2) else 0 end as pu,product_id
	# 		from vst_kardex_fisico_valorado_simplificado			
	# 		where product_id in """ +productos+ """ and location_id in """ +almacenes+ """	
	# 		group by product_id order by product_id ) T
	# left join (
	# 	SELECT id, value_float, name, res_id
	# 	FROM ir_property
	# 	WHERE name='standard_price' order by id ) R on R.res_id = ('product.product,' || T.product_id )
	# 																		where R.id is null
	# 																		""")



	# 	self.env.cr.execute(""" 
	# 		update ir_property set value_float = T.valor from (
	# 		select 
	# 		CASE WHEN coalesce(sum(ingreso),0) != 0 THEN round(coalesce(sum(coalesce(debit)),0) / coalesce(sum(coalesce(ingreso,0)),0),2) else 0 end as valor,product_id
	# 		from vst_kardex_fisico_valorado_simplificado
	# 		where product_id in """ +productos+ """ and location_id in """ +almacenes+ """
	# 		group by product_id order by product_id ) T where ( 'product.product,' || T.product_id ) = ir_property.res_id

	# 	""")

	# 	return t
		
class gastos_vinculados_it(models.Model):
	_inherit = 'gastos.vinculados.it'
	
	@api.one
	def procesar(self):
		t = super(gastos_vinculados_it,self).procesar()

		currency_obj = self.env['res.currency'].search([('name','=',self.currency_id.name)])
		if len(currency_obj)>0:
			currency_obj = currency_obj[0]
		else:
			raise UserError( 'Error!\nNo existe la moneda' )

		fecha = self.date_invoice if self.tomar_valor == 'factura' else self.date_purchase
		tipo_cambio = self.env['res.currency.rate'].search([('name','=',fecha),('currency_id','=',currency_obj.id)])

		if len(tipo_cambio)>0:
			tipo_cambio = tipo_cambio[0]
		else:
			if currency_obj.name != 'PEN':
				raise UserError( 'Error!\nNo existe el tipo de cambio para la fecha: '+ str(fecha) )         
		
		s_prod = [-1,-1,-1]
		s_loca = [-1,-1,-1]
		

		for elem_pro in self.detalle_ids:
			s_prod.append(elem_pro.stock_move_id.product_id.id)

		productos='(0,'
		almacenes='(0,'
		
		for producto in s_prod:
			productos=productos+str(producto)+','
		productos=productos[:-1]+')'

		lst_locations  = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])

		for location in lst_locations:
			almacenes=almacenes+str(location.id)+','
			s_loca.append(location.id)
		almacenes=almacenes[:-1]+')'

		import datetime
		fecha_final = self.date_invoice if self.tomar_valor == 'factura' else self.date_purchase
		if not fecha_final:
			fecha_final = str (datetime.datetime.now() )[:10]
		date_ini=fecha_final.split('-')[0] + '-01-01'
		date_fin=fecha_final.split('-')[0] + '-12-31'




		self.env.cr.execute("""
		insert into ir_property(value_float, name, res_id, type,fields_id)
		select 0 as value_float, 'standard_price' as name, 'product.product,' || product_id as res_id, 'float' as type,(select id from ir_model_fields where model = 'product.product' and name = 'standard_price' and ttype = 'float' ) as fields_id  from (
		select 
			CASE WHEN coalesce(sum(ingreso),0) != 0 THEN round(coalesce(sum(coalesce(debit)),0) / coalesce(sum(coalesce(ingreso,0)),0),2) else 0 end as pu,product_id
			from vst_kardex_fisico_valorado_simplificado			
				left join stock_location a1 on a1.id = 	vst_kardex_fisico_valorado_simplificado.id_origen
				left join stock_location a2 on a2.id = 	vst_kardex_fisico_valorado_simplificado.id_destino	
		
				where vst_kardex_fisico_valorado_simplificado.product_id in """ +productos+ """ and vst_kardex_fisico_valorado_simplificado.location_id in """ +almacenes+ """	and (coalesce(a1.usage,'none') != 'internal' or coalesce(a2.usage,'none') != 'internal')
			group by product_id order by product_id ) T
	left join (
		SELECT id, value_float, name, res_id
		FROM ir_property
		WHERE name='standard_price' order by id ) R on R.res_id = ('product.product,' || T.product_id )
																			where R.id is null
																			""")



		self.env.cr.execute(""" 
			update ir_property set value_float = T.valor from (
			select 
			CASE WHEN coalesce(sum(ingreso),0) != 0 THEN round(coalesce(sum(coalesce(debit)),0) / coalesce(sum(coalesce(ingreso,0)),0),2) else 0 end as valor,product_id
			from vst_kardex_fisico_valorado_simplificado
				left join stock_location a1 on a1.id = 	vst_kardex_fisico_valorado_simplificado.id_origen
				left join stock_location a2 on a2.id = 	vst_kardex_fisico_valorado_simplificado.id_destino	
				
				where vst_kardex_fisico_valorado_simplificado.product_id in """ +productos+ """ and vst_kardex_fisico_valorado_simplificado.location_id in """ +almacenes+ """	and (coalesce(a1.usage,'none') != 'internal' or coalesce(a2.usage,'none') != 'internal')
			group by product_id order by product_id ) T where ( 'product.product,' || T.product_id ) = ir_property.res_id

		""")

		return t


	
	@api.one
	def borrador(self):
		t = super(gastos_vinculados_it,self).borrador()


		currency_obj = self.env['res.currency'].search([('name','=',self.currency_id.name)])
		if len(currency_obj)>0:
			currency_obj = currency_obj[0]
		else:
			raise UserError( 'Error!\nNo existe la moneda' )

		fecha = self.date_invoice if self.tomar_valor == 'factura' else self.date_purchase
		tipo_cambio = self.env['res.currency.rate'].search([('name','=',fecha),('currency_id','=',currency_obj.id)])

		if len(tipo_cambio)>0:
			tipo_cambio = tipo_cambio[0]
		else:
			if currency_obj.name != 'PEN':
				raise UserError( 'Error!\nNo existe el tipo de cambio para la fecha: '+ str(fecha) )       
		
		s_prod = [-1,-1,-1]
		s_loca = [-1,-1,-1]
		

		for elem_pro in self.detalle_ids:
			s_prod.append(elem_pro.stock_move_id.product_id.id)

		productos='(0,'
		almacenes='(0,'
		
		for producto in s_prod:
			productos=productos+str(producto)+','
		productos=productos[:-1]+')'

		lst_locations  = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])

		for location in lst_locations:
			almacenes=almacenes+str(location.id)+','
			s_loca.append(location.id)
		almacenes=almacenes[:-1]+')'

		import datetime
		fecha_final = self.date_invoice if self.tomar_valor == 'factura' else self.date_purchase
		if not fecha_final:
			fecha_final = str (datetime.datetime.now() )[:10]
		date_ini=fecha_final.split('-')[0] + '-01-01'
		date_fin=fecha_final.split('-')[0] + '-12-31'



		self.env.cr.execute("""
		insert into ir_property(value_float, name, res_id, type,fields_id)
		select 0 as value_float, 'standard_price' as name, 'product.product,' || product_id as res_id, 'float' as type,(select id from ir_model_fields where model = 'product.product' and name = 'standard_price' and ttype = 'float' ) as fields_id  from (
		select 
			CASE WHEN coalesce(sum(ingreso),0) != 0 THEN round(coalesce(sum(coalesce(debit)),0) / coalesce(sum(coalesce(ingreso,0)),0),2) else 0 end as pu,product_id
			from vst_kardex_fisico_valorado_simplificado			
				left join stock_location a1 on a1.id = 	vst_kardex_fisico_valorado_simplificado.id_origen
				left join stock_location a2 on a2.id = 	vst_kardex_fisico_valorado_simplificado.id_destino	
				where vst_kardex_fisico_valorado_simplificado.product_id in """ +productos+ """ and vst_kardex_fisico_valorado_simplificado.location_id in """ +almacenes+ """	and (coalesce(a1.usage,'none') != 'internal' or coalesce(a2.usage,'none') != 'internal')
			group by product_id order by product_id ) T
	left join (
		SELECT id, value_float, name, res_id
		FROM ir_property
		WHERE name='standard_price' order by id ) R on R.res_id = ('product.product,' || T.product_id )
																			where R.id is null
																			""")



		self.env.cr.execute(""" 
			update ir_property set value_float = T.valor from (
			select 
			CASE WHEN coalesce(sum(ingreso),0) != 0 THEN round(coalesce(sum(coalesce(debit)),0) / coalesce(sum(coalesce(ingreso,0)),0),2) else 0 end as valor,product_id
			from vst_kardex_fisico_valorado_simplificado
				left join stock_location a1 on a1.id = 	vst_kardex_fisico_valorado_simplificado.id_origen
				left join stock_location a2 on a2.id = 	vst_kardex_fisico_valorado_simplificado.id_destino	
				where vst_kardex_fisico_valorado_simplificado.product_id in """ +productos+ """ and vst_kardex_fisico_valorado_simplificado.location_id in """ +almacenes+ """	and (coalesce(a1.usage,'none') != 'internal' or coalesce(a2.usage,'none') != 'internal')
			group by vst_kardex_fisico_valorado_simplificado.product_id order by vst_kardex_fisico_valorado_simplificado.product_id ) T where ( 'product.product,' || T.product_id ) = ir_property.res_id

		""")

		return t