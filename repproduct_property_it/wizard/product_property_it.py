# -*- coding: utf-8 -*-

from openerp import models, fields, api

class product_property_it(models.Model):

	_name='product.property.it'
	_auto = False

	product_id = fields.Integer(string='Producto ID', size=30)
	codigo = fields.Char(string='Código',size=100)
	descripcion = fields.Many2one('product.product',string='Descripción',size=100)
	categoria = fields.Char(string='Categoria',size=100)
	tipo = fields.Char(string='Tipo',size=100)
	cuentaingreso = fields.Char(string='Cuenta Ingreso',size=100)
	cuentagasto = fields.Char(string='Cuenta Gasto',size=100)
	cuentaentrada = fields.Char(string='Cuenta Entrada',size=100)
	cuentasalida = fields.Char(string='Cuenta Salida',size=100)
	cuentavaluacion = fields.Char(string='Cuenta Valuación',size=100)
	
	@api.model_cr
	def init(self):

		self.env.cr.execute("""
			create or replace view product_property_it as (


select * from (
select row_number() OVER() as id,* from
(

select distinct * from (
select 
product_product.id as product_id,
product_product.default_code as codigo,
product_product.id as descripcion,
product_category.name as categoria,
CASE WHEN product_template.type = 'product' THEN 'Almacenable' WHEN product_template.type = 'consu' THEN 'Consumible' ELSE 'Servicio' END as tipo,
CASE WHEN aa1.code is Null THEN aa7.code ELSE aa1.code END as cuentaingreso,
CASE WHEN aa2.code is Null THEN aa8.code ELSE aa2.code END as cuentagasto,
aa3.code as cuentaentrada,
aa4.code as cuentasalida,
aa5.code as cuentavaluacion
from
product_product 

left outer join product_template on product_template.id = product_product.product_tmpl_id
left outer join product_category on product_category.id = product_template.categ_id


left outer join ir_property ip1 on (ip1.res_id = 'product.template,' || COALESCE(product_template.id,-1) or ip1.res_id is Null) and ip1.name = 'property_account_income_id'
left outer join account_account aa1 on aa1.id = COALESCE( substring(ip1.value_reference from 17)::int8 , -1)
left outer join ir_property ip2 on (ip2.res_id = 'product.template,' || COALESCE(product_template.id,-1) or ip2.res_id is Null) and ip2.name = 'property_account_expense_id'
left outer join account_account aa2 on aa2.id = COALESCE( substring(ip2.value_reference from 17)::int8, -1)
left outer join ir_property ip3 on (ip3.res_id = 'product.category,' || COALESCE(product_category.id,-1) or ip3.res_id is Null) and ip3.name = 'property_stock_account_input_categ_id' 
left outer join account_account aa3 on aa3.id = COALESCE( substring(ip3.value_reference from 17)::int8, -1)
left outer join ir_property ip4 on (ip4.res_id = 'product.category,' || COALESCE(product_category.id,-1) or ip4.res_id is Null) and ip4.name = 'property_stock_account_output_categ_id'
left outer join account_account aa4 on aa4.id = COALESCE( substring(ip4.value_reference from 17)::int8, -1)
left outer join ir_property ip5 on (ip5.res_id = 'product.category,' || COALESCE(product_category.id,-1) or ip5.res_id is Null) and ip5.name = 'property_stock_valuation_account_id'
left outer join account_account aa5 on aa5.id = COALESCE( substring(ip5.value_reference from 17)::int8, -1)
left outer join ir_property ip7 on (ip7.res_id = 'product.category,' || COALESCE(product_category.id,-1) or ip7.res_id is Null) and ip7.name = 'property_account_income_categ_id'
left outer join account_account aa7 on aa7.id = COALESCE( substring(ip7.value_reference from 17)::int8, -1)
left outer join ir_property ip8 on (ip8.res_id = 'product.category,' || COALESCE(product_category.id,-1) or ip8.res_id is Null) and ip8.name = 'property_account_expense_categ_id'
left outer join account_account aa8 on aa8.id = COALESCE( substring(ip8.value_reference from 17)::int8, -1) ) AS T
order by product_id
) AS W  ) AS TT where id in (select min(id) from (
select row_number() OVER() as id,* from
(

select distinct * from (
select 
product_product.id as product_id,
product_product.default_code as codigo,
product_product.id as descripcion,
product_category.name as categoria,
CASE WHEN product_template.type = 'product' THEN 'Almacenable' WHEN product_template.type = 'consu' THEN 'Consumible' ELSE 'Servicio' END as tipo,
CASE WHEN aa1.code is Null THEN aa7.code ELSE aa1.code END as cuentaingreso,
CASE WHEN aa2.code is Null THEN aa8.code ELSE aa2.code END as cuentagasto,
aa3.code as cuentaentrada,
aa4.code as cuentasalida,
aa5.code as cuentavaluacion
from
product_product 

left outer join product_template on product_template.id = product_product.product_tmpl_id
left outer join product_category on product_category.id = product_template.categ_id


left outer join ir_property ip1 on (ip1.res_id = 'product.template,' || COALESCE(product_template.id,-1) or ip1.res_id is Null) and ip1.name = 'property_account_income_id'
left outer join account_account aa1 on aa1.id = COALESCE( substring(ip1.value_reference from 17)::int8 , -1)
left outer join ir_property ip2 on (ip2.res_id = 'product.template,' || COALESCE(product_template.id,-1) or ip2.res_id is Null) and ip2.name = 'property_account_expense_id'
left outer join account_account aa2 on aa2.id = COALESCE( substring(ip2.value_reference from 17)::int8, -1)
left outer join ir_property ip3 on (ip3.res_id = 'product.category,' || COALESCE(product_category.id,-1) or ip3.res_id is Null) and ip3.name = 'property_stock_account_input_categ_id' 
left outer join account_account aa3 on aa3.id = COALESCE( substring(ip3.value_reference from 17)::int8, -1)
left outer join ir_property ip4 on (ip4.res_id = 'product.category,' || COALESCE(product_category.id,-1) or ip4.res_id is Null) and ip4.name = 'property_stock_account_output_categ_id'
left outer join account_account aa4 on aa4.id = COALESCE( substring(ip4.value_reference from 17)::int8, -1)
left outer join ir_property ip5 on (ip5.res_id = 'product.category,' || COALESCE(product_category.id,-1) or ip5.res_id is Null) and ip5.name = 'property_stock_valuation_account_id'
left outer join account_account aa5 on aa5.id = COALESCE( substring(ip5.value_reference from 17)::int8, -1)
left outer join ir_property ip7 on (ip7.res_id = 'product.category,' || COALESCE(product_category.id,-1) or ip7.res_id is Null) and ip7.name = 'property_account_income_categ_id'
left outer join account_account aa7 on aa7.id = COALESCE( substring(ip7.value_reference from 17)::int8, -1)
left outer join ir_property ip8 on (ip8.res_id = 'product.category,' || COALESCE(product_category.id,-1) or ip8.res_id is Null) and ip8.name = 'property_account_expense_categ_id'
left outer join account_account aa8 on aa8.id = COALESCE( substring(ip8.value_reference from 17)::int8, -1) ) AS T
order by product_id
) AS W 
) AS LAST
GROUP BY product_id, codigo, descripcion, categoria , tipo
order by min(id)

)


						)""")

