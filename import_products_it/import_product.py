# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api
from datetime import datetime
from datetime import timedelta
from tempfile import TemporaryFile
import csv
import base64

class import_product(models.Model):
	_name = 'import.product'
	_rec_name = 'import_date'

	state = fields.Selection([('draft','Borrador'),('process_exception','Excepciones'),('ready','Listo para importar'),('done','Hecho')],"Estado", default="draft", compute='_get_state')
	binary_file = fields.Binary("File")
	file_name = fields.Char("Nombre")
	import_date = fields.Date("Fecha importación", readonly=1)
	reason = fields.Char("Motivo", default="Saldo inicial", readonly=1)
	lines = fields.One2many('import.product.line', 'parent', 'Detalle', domain=[('state','=','invalid')])
	lines2 = fields.One2many('import.product.line', 'parent', 'Detalle', domain=[('state','=','valid')])
	lines3 = fields.One2many('import.product.line', 'parent', 'Detalle', domain=[('state','=','done')])
	done = fields.Boolean("Hecho")

	@api.model
	def create(self,vals):
		vals['import_date'] = fields.Date.today()
		return super(import_product,self).create(vals)

	@api.one
	def _get_state(self):
		if self.done:
			terminado = True
			for i in self.lines2:
				if i.state != 'done':
					terminado = False


			self.state = 'done' if terminado else 'process_exception'
		else:
			self.state = 'draft'
			lines = self.env['import.product.line'].search([('parent','=',self.id)])
			if lines:
				self.state = 'ready'
				for line in self.lines:
					if line.state == 'invalid':
						self.state = 'process_exception'
						break

	@api.one
	def pre_process_data(self):
		for line in self.lines:
			line.unlink()
		if self.binary_file:
			self.env.cr.execute("set client_encoding ='UTF8';")
			line_obj = self.env['import.product.line']
			data = self.read()[0]
			fileobj = TemporaryFile('w+')
			fileobj.write(base64.decodestring(data['binary_file']))
			fileobj.seek(0)
			c=base64.decodestring(data['binary_file'])
			fic = csv.reader(fileobj,delimiter=';',quotechar='"')
			#Creación de líneas en pantalla.
			for data in fic:
				uom_id = self.env['product.uom'].search([('name','=',data[2].strip())])
				types = {'ALMACENABLE':'product','CONSUMIBLE':'consu','SERVICIO':'service'}
				categ_id = self.env['product.category'].search([('name','=',data[4].strip())])
				uom_po_id = self.env['product.uom'].search([('name','=',data[7].strip())])
				routes = data[8].strip()#.split(',') if data[8] else ['']


				route_ids = self.env['stock.location.route'].search([('name','in',routes.split(',') if routes else [''])])
				p_income = self.env['account.account'].search([('code','=',data[9].strip())])
				p_expense = self.env['account.account'].search([('code','=',data[10].strip())])
				vals = {
					'parent'					: self.id,
					'default_code'				: data[0].strip(),
					'name'						: data[1].strip(),
					'uom_id'					: uom_id.id if uom_id else None,
					'type'						: types[data[3].strip()],
					'categ_id'					: categ_id.id if categ_id else None,
					'sale_ok'					: int(data[5].strip()) if data[5].strip() != '' else False,
					'purchase_ok'				: int(data[6].strip()) if data[6].strip() != '' else False,
					'uom_po_id'					: uom_id.id if uom_id else None,
					'routes_id'					: routes,
					'property_account_income'	: p_income.id if p_income else None,
					'property_account_expense'	: p_expense.id if p_expense else None,
					'state'						: 'valid',
				}
				vals['observations'] = ''
				if not data[3].strip() in types.keys():
					vals['observations'] += 'Tipo incorrecto, '
				#Validando datos.
				if not uom_id:
					vals['observations'] += 'Unidad no encontrada, '
				if not categ_id:
					vals['observations'] += 'Categoría no encontrada, '
				if not route_ids.ids:
					vals['observations'] += 'Ruta no encontrada, '
				if not p_income and data[9].strip() != '':
					vals['observations'] += 'Cuenta de ingresos no encontrada, '
				if not p_expense and data[10].strip() != '':
					vals['observations'] += 'Cuenta de egresos no encontrada, '
				if vals['observations'] == '':
					vals['state'] = 'valid'
				else:
					vals['state'] = 'invalid'
				
				#Las lineas inválidas son mostradas para corrección
				line_obj.create(vals)
		else:
			raise osv.except_osv('Alerta!',"No hay un archivo ingresado.")


	@api.one
	def correct_data(self):
		for line in self.lines:
			if line.state == 'invalid':
				product = self.env['product.product'].search([('default_code','=',line.default_code.strip(" "))])
				if product:
					line.state = 'valid'


	@api.one
	def import_data(self):
		for line in self.lines2:
			if line.state =='valid':
				product_obj = self.env['product.product']
				tt = line.routes_id.split(',')
				result_fin = []
				for i in tt:
					result_fin.append( i.strip() )
				route_ids = self.env['stock.location.route'].search([('name','in', result_fin )])
				vals = {
					'default_code'				: line.default_code,
					'name'						: line.name,
					'uom_id'					: line.uom_id.id,
					'type'						: line.type,
					'categ_id'					: line.categ_id.id,
					'sale_ok'					: line.sale_ok,
					'purchase_ok'				: line.purchase_ok,
					'uom_po_id'					: line.uom_po_id.id if line.uom_po_id else 0,
					'routes_id'					: [(6,0, route_ids)],
					'property_account_income'	: line.property_account_income.id if line.property_account_income else 0,
					'property_account_expense'	: line.property_account_expense.id if line.property_account_expense else 0,
				}
				product_obj.create(vals)
				line.state = 'done'

		self.done = True


class import_product_line(models.Model):
	_name = 'import.product.line'

	parent = fields.Many2one('import.product','Import')
	default_code = fields.Char("Código", readonly=1)
	name = fields.Char('Nombre', readonly=1)
	uom_id = fields.Many2one('product.uom', "Unidad")
	type = fields.Char("Tipo")
	categ_id = fields.Many2one('product.category', "Categoría contable")
	sale_ok = fields.Boolean("Puede ser vendido")
	purchase_ok = fields.Boolean("Puede ser comprado")
	uom_po_id = fields.Many2one('product.uom', "Unidad de Compra")
	routes_id = fields.Char("Rutas de Abastecimiento")
	property_account_income = fields.Many2one('account.account', "Cuenta Ingresos")
	property_account_expense = fields.Many2one('account.account', "Cuenta egresos")
	observations = fields.Text("Observaciones")
	state = fields.Selection([('invalid', 'Inválido'),('valid','Válido'),('done','Procesado')], readonly=1)