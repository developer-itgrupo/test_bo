# -*- coding: utf-8 -*-
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import Warning
import time
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
from openerp.osv import osv
import base64
from odoo import models, fields, api
from datetime import datetime, timedelta
import codecs
values = {}

import datetime
from odoo import tools


class ProductPricelist(models.Model):
	_inherit = 'product.pricelist'
	prod_category = fields.Many2one('product.category','Categoria')
	mode_selector = fields.Selection([('variant','Producto'),('category','Categoria')],string='Agregar por:', default='variant')


	@api.multi
	def get_lista_items(self):
		action = self.env.ref('custom_functionaity_rates_it.action_sale_tarifa').read()[0]

		items = self.mapped('item_ids')
		if len(items) > 1:
			action['domain'] = [('id', 'in', items.ids)]
		elif items:
			action['views'] = [(self.env.ref('product.product_pricelist_item_form_view').id, 'form')]
			action['res_id'] = items.id
		return action

	@api.multi
	def do_oexcel(self):
		compania = ""
		today = ""
		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		workbook = Workbook(direccion +'reporte_garantia.xlsx')
		worksheet = workbook.add_worksheet("Kardex")
		bold = workbook.add_format({'bold': True})
		bold.set_font_size(8)
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_text_wrap()
		boldbord.set_font_size(8)
		boldbord.set_bg_color('#DCE6F1')

		especial1 = workbook.add_format({'bold': True})
		especial1.set_align('center')
		especial1.set_align('vcenter')
		especial1.set_text_wrap()
		especial1.set_font_size(15)

		especial4 = workbook.add_format({'bold': True})
		especial4.set_align('center')
		especial4.set_align('vcenter')
		especial4.set_text_wrap()
		especial4.set_font_size(15)

		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		numberseis = workbook.add_format({'num_format':'0.000000'})
		numberseis.set_font_size(8)
		numberocho = workbook.add_format({'num_format':'0.00000000'})
		numberocho.set_font_size(8)
		bord = workbook.add_format()
		bord.set_border(style=1)
		bord.set_font_size(8)
		bord2 = workbook.add_format({'align': 'right', 'border': 1})
		bord2.set_font_size(8)
		numberdos.set_border(style=1)
		numberdos.set_font_size(8)
		numbertres.set_font_size(8)
		numbertres.set_border(style=1)
		numberseis.set_border(style=1)
		numberocho.set_border(style=1)
		numberdosbold = workbook.add_format({'num_format':'0.00','border':1})
		numberdosbold.set_font_size(8)
		numberseisbold = workbook.add_format({'num_format':'0.000000','border':1})
		numberseisbold.set_font_size(8)
		formatMoneyWithBorder = workbook.add_format(
			{'valign': 'vcenter', 'align': 'right', 'border': 1, 'num_format': '"S/." #,##0.00' })
		formatMoneyWithBorder.set_font_size(8)
		formatCompraWithBorder = workbook.add_format(
			{'valign': 'vcenter', 'align': 'right', 'border': 1, 'num_format': '0.0000' })
		formatCompraWithBorder.set_font_size(8)
		x= 10
		y= 10
		tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tam_letra = 1.2
		import datetime
		today = datetime.datetime.today().strftime('%Y-%m-%d')
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		worksheet.merge_range(0,1,0,6, "FORMATO : REPORTE DE TARIFAS", especial1)


		worksheet.write(3,5,'FECHA DE EMISION:',boldbord)
		worksheet.write(3,6,today)
		#Categoria
		worksheet.merge_range(8,1,9,1, u"NOMBRE",boldbord)
		worksheet.merge_range(8,2,9,2, u"CANTIDAD MIN.",boldbord)
		#default_code_producto
		worksheet.merge_range(8,3,9,3, u"ULTIMA COMPRA",boldbord)
		worksheet.merge_range(8,4,9,4, u"COSTO PROMEDIO",boldbord)
		worksheet.merge_range(8,5,9,5, u"FECHA DE INICIO",boldbord)
		worksheet.merge_range(8,6,9,6, u"FECHA FINAL",boldbord)
		worksheet.merge_range(8,7,9,7, u"PRECIO",boldbord)

		#COSTO
		#costo*stock
		listas = self.env['product.pricelist.item'].search([('pricelist_id','=', self.id)])
		print(list(listas))
		for line in listas:
			worksheet.write(x,1,line.name if line.name else '' ,bord )
			worksheet.write(x,2,line.min_quantity if line.min_quantity else 0 ,bord )
			worksheet.write(x,3,line.last_cost if line.last_cost else 0 ,bord )
			worksheet.write(x,4,line.standart_price if line.standart_price else 0 ,bord2 )
			worksheet.write(x,5,line.date_start if line.date_start else '' ,bord )
			worksheet.write(x,6,line.date_end if line.date_end else '' ,bord )
			worksheet.write(x,7,line.price if line.price else 0 ,bord )
			x=x+1
		total_saldo = 0
		total_saldo_acumulado = 0
		i=0
		y=0
		p=0
		

		tam_col = [11,50,20,14,14,14,14,40,11,11,11,11]


		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])
		worksheet.set_column('H:H', tam_col[7])
		worksheet.set_column('I:I', tam_col[8])
		worksheet.set_column('J:J', tam_col[9])
		worksheet.set_column('K:K', tam_col[10])
		worksheet.set_column('L:L', tam_col[11])

		workbook.close()

		f = open(direccion + 'reporte_garantia.xlsx', 'rb')


		sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
		vals = {
			'output_name': 'reporte_garantia.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),
		}

		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		sfs_id = self.env['export.file.save'].create(vals)
		result = {}
		#import pdb; pdb.set_trace()
		#view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
		#view_id = view_ref and view_ref[1] or False
		#result = act_obj.read( [view_id] )
		print sfs_id

		#import os
		#os.system('c:\\eSpeak2\\command_line\\espeak.exe -ves-f1 -s 170 -p 100 "Se Realizo La exportación exitosamente Y A EDWARD NO LE GUSTA XDXDXDXDDDDDDDDDDDD" ')
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}


	@api.multi
	def export_excel(self):
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		self.env.cr.execute("""
				copy (select * from public.get_rep_tarifa(('"""+str(self.id)+"""'))) to
				'"""+direccion+u"""reporte_elementos_tarifa.csv' WITH DELIMITER ',' CSV HEADER
				"""
			)

		f = open(direccion + 'reporte_elementos_tarifa.csv', 'rb')


		sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
		vals = {
			'output_name': 'reporte_elementos_tarifa.csv',
			'output_file': base64.encodestring(''.join(f.readlines())),
		}

		sfs_id = self.env['export.file.save'].create(vals)

		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}



#PARA AGREGAR ITEMS A LA TARIFA
	@api.multi
	def add_items(self):


		products = None
		print('sel', self.mode_selector)
		if not self.mode_selector:
			raise exceptions.Warning('No ha seleccionado un tipo de Criterio. \n'+'Debe elegir Producto o Categoria')
		if self.mode_selector == 'category':
			cat = self.prod_category[0].id
		if self.mode_selector == 'variant':
			cat = 0



		self.env.cr.execute("""
				select* from get_lista(1,('"""+str(self.id)+"""'),('"""+str(cat)+"""'))
				"""
			)

		verified_products= self.env.cr.fetchall()



		for product in verified_products:
			vals = {
				'pricelist_id': self.id,
				'applied_on': '0_product_variant',
				'compute_price': 'fixed',
				#'standart_price': product[0].standard_price,
				'product_id': product
			}

			self.env['product.pricelist.item'].create(vals)

#PARA REMOVER LOS ITEMS DEPENDIENDO DE LA CATEGORIA O TODOS LOS ITEMS
	@api.multi
	def remove_items(self):

		print('works remove')
		if not self.mode_selector:
			raise exceptions.Warning('No ha seleccionado un tipo de Criterio. \n'+'Debe elegir Producto o Categoria')
		if self.mode_selector == 'variant':
			cat = 0
		if self.mode_selector == 'category':
			cat = self.prod_category[0].id
		self.env.cr.execute("""
				select* from get_lista(2,('"""+str(self.id)+"""'),('"""+str(cat)+"""'))
				"""
			)
		verified_products= self.env.cr.fetchall()

#PARA MOSTRAR LOS COSTOS EN LA TARIFA
	@api.multi
	def show_cost_for_items(self):

		self.env.cr.execute("""
				select * from vst_ultimos_precios_compra
				"""
			)
		query = list(self.env.cr.dictfetchall())
		for que in query:
			result = self.env['product.pricelist.item'].search([('product_id','=', que["product_id"]),('pricelist_id','=', self.id)])
			cadena = str(que['price_unit'])
			cadena1 = que['simbolo']
			cadena2= cadena1 + ' ' + cadena  
			result.write({'last_cost' : cadena2})



	@api.multi
	def show_costo_prom(self):
		self.env.cr.execute("""
				select  cast(substr (res_id, 17) AS INTEGER) as product_id, value_float as costo_promedio
				FROM ir_property
				WHERE name='standard_price'
				"""
			)
		query_costo = list(self.env.cr.dictfetchall())
		for que_costo in query_costo:
			que_costo
		for que_costo in query_costo:
			result = self.env['product.pricelist.item'].search([('product_id','=', que_costo["product_id"]),('pricelist_id','=', self.id)])
			result.write({'standart_price' : que_costo["costo_promedio"]})



class ProductPricelistItem(models.Model):
	_inherit = 'product.pricelist.item'
	# standard price del producto de del product_list_item
	standart_price = fields.Char(u'Precio Estandar')
	# last_cost del producto de del product_list_item
	last_cost = fields.Char('Ultimo costo')
