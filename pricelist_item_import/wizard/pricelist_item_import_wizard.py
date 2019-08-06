# -*- encoding: utf-8 -*-
##############################################################################
#
#	Odoo, Open Source Management Solution
#
#	Copyright (c) 2009-2015 Noviat nv/sa (www.noviat.com).
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU Affero General Public License as
#	published by the Free Software Foundation, either version 3 of the
#	License, or (at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#	GNU Affero General Public License for more details.
#
#	You should have received a copy of the GNU Affero General Public License
#	along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

try:
	import cStringIO as StringIO
except ImportError:
	import StringIO
import base64
import csv
from datetime import datetime
from sys import exc_info
from traceback import format_exception

from openerp import models, fields, api, _
from openerp.exceptions import Warning

import logging
_logger = logging.getLogger(__name__)


class ProductPricelistItemImport(models.TransientModel):
	_name = 'ppi.import'
	_description = 'Import Rate lines'

	ppi_data = fields.Binary(string='File', required=True)
	ppi_fname = fields.Char(string='Filename')
	lines = fields.Binary(
		compute='_compute_lines', string='Input Lines', required=True)
	dialect = fields.Binary(
		compute='_compute_dialect', string='Dialect', required=True)
	csv_separator = fields.Selection(
		[(',', ', (Coma)'), (';', '; (Punto y coma)')],
		string='CSV Separator', required=True)
	decimal_separator = fields.Selection(
		[('.', ' . (Punto)'), (',', ', (Coma)')],
		string='Decimal Separator',
		default='.', required=True)
	codepage = fields.Char(
		string='Code Page',
		default=lambda self: self._default_codepage(),
		help="Code Page of the system that has generated the csv file."
			 "\nE.g. Windows-1252, utf-8")
	mode_selector = fields.Selection([('id_product','iD de Producto'),('id_int','Referencia Interna')],string='importar por:', default='id_int') 
	note = fields.Text('Log')



	def _input_fields(self):
		"""
		Extend this dictionary if you want to add support for
		fields requiring pre-processing before being added to
		the pricelist line values dict.
		"""
		res = {
			'categ_id': {'method': self._handle_categ_id},
			'product_tmpl_id': {'method': self._handle_product_tmpl_id},
			'product_id': {'method': self._handle_product_id},
			'fixed_price': {'method': self._handle_fixed_price},
			'percent_price': {'method': self._handle_percent_price},
			'price_discount': {'method': self._handle_price_discount},
			'base_pricelist_id': {'method': self._handle_base_pricelist_id},
		}
		return res

	@api.multi
	def ppi_import(self):

		self._err_log = ''
		pricelist = self.env['product.pricelist'].browse(
			self._context['active_id'])
		self._get_orm_fields()
		lines, header = self._remove_leading_lines(self.lines)
		header_fields = csv.reader(
			StringIO.StringIO(header), dialect=self.dialect).next()
		
		header_fields = self.traslate_header_fields(header_fields)
		self._header_fields = self._process_header(header_fields)
		reader = csv.DictReader(
			StringIO.StringIO(lines), fieldnames=self._header_fields,
			dialect=self.dialect)

		item_lines = []
		error_line = False
		constrains = [['categ_id','product_id','product_tmpl_id'],['fixed_price','percent_price','price_discount']]
		for line in reader:
			if not self.verify_constrains_line(line,constrains):
				error_line = True
				break
			ppi_vals = {}
			# step 1: handle codepage
			for i, hf in enumerate(self._header_fields):
				try:
					line[hf] = line[hf].decode(self.codepage).strip()
				except:
					tb = ''.join(format_exception(*exc_info()))
					raise Warning(
						_("Wrong Code Page"),
						_("Error while processing line '%s' :\n%s")
						% (line, tb))

			# step 2: process input fields
			for i, hf in enumerate(self._header_fields):
				if i == 0 and line[hf] and line[hf][0] == '#':
					# lines starting with # are considered as comment lines
					break
				if hf in self._skip_fields:
					continue
				if line[hf] == '':
					continue

				if self._field_methods[hf].get('orm_field'):
					self._field_methods[hf]['method'](
						hf, line, pricelist, ppi_vals,
						orm_field=self._field_methods[hf]['orm_field'])
				else:
					self._field_methods[hf]['method'](
						hf, line, pricelist, ppi_vals)

			if ppi_vals:
				self._process_line_vals(line, pricelist, ppi_vals)
				item_lines.append(ppi_vals)

		if error_line:
			raise Warning(u'Existe una(s) lineas con errores de asignación de valores.')
		vals = [(0, 0, l) for l in item_lines]
		vals = self._process_vals(pricelist, vals)

		if self._err_log:
			self.note = self._err_log
			result_view = self.env.ref(
				'pricelist_item_import.ppi_import_view_form_result')
			return {
				'name': _("Import File result"),
				'res_id': self.id,
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'ppi.import',
				'view_id': result_view.id,
				'target': 'new',
				'type': 'ir.actions.act_window',
			}
		else:
			#pricelist.write({'line_ids': vals})
			for i in vals:	   
				#print (i[2],' anidado')
				data = i[2]

				data['pricelist_id'] = pricelist.id
				self.env['product.pricelist.item'].create(data)
				
			return {'type': 'ir.actions.act_window_close'}


#### other methods
	def _process_line_vals(self, line, pricelist, ppi_vals):
		"""
		Use this method if you want to check/modify the
		line input values dict before calling the pricelist write() method
		"""
		ppi_vals['applied_on'] = self._get_applied_on(line,ppi_vals)
		ppi_vals['compute_price'] = self._get_compute_price(line,ppi_vals)

		all_fields = self._field_methods
		required_fields = [x for x in all_fields
						   if all_fields[x].get('required')]
		for rf in required_fields:
			if rf not in ppi_vals:
				msg = _("The '%s' field is a required field "
						"that must be correctly set.") % rf
				self._log_line_error(line, msg)

	def _process_vals(self, pricelist, vals):
		"""
		Use this method if you want to check/modify the
		input values dict before calling the pricelist write() method
		"""
		return vals


####Lógica variada y manejadores de campos:
					
	def _get_applied_on(self, line, ppi_vals):
		if not ppi_vals.get('applied_on'):
			if line.get('categ_id'):
				if line['categ_id'] != '':
					ppi_vals['applied_on'] = '2_product_category'
			if line.get('product_tmpl_id'):
				if line['product_tmpl_id'] != '':
					ppi_vals['applied_on'] = '1_product'
			if line.get('product_id'):
				if line['product_id'] != '':
					ppi_vals['applied_on'] = '0_product_variant'
			return ppi_vals['applied_on']
					

	def _handle_categ_id(self, field, line, pricelist, ppi_vals):
		if not ppi_vals.get('categ_id'):
			input = line[field]
			categories = self.env['product.category'].search([('code','=',input)])
			if len(categories) == 1:
				ppi_vals['categ_id'] = categories.id
			if not categories:
				msg = _("Invalid Code of Category '%s' !") % input
				self._log_line_error(line, msg)
			elif len(categories) > 1:
				msg = _("Multiple Categories found "
						"that match with '%s' !") % input
				self._log_line_error(line, msg)

	def _handle_product_tmpl_id(self, field, line, pricelist, ppi_vals):
		if not ppi_vals.get('product_tmpl_id'):
			input = line[field]
			prod_tmpl = self.env['product.template']
			dom = []
			dom_ref = dom + [('name', '=', input)]
			products = prod_tmpl.search(dom_ref)
			if not products:
				msg = _("Product '%s' not found !") % input
				self._log_line_error(line, msg)
				return
			elif len(products) > 1:
				msg = _("Multiple products with Reference "
						"or Name '%s' found !") % input
				self._log_line_error(line, msg)
				return
			else:
				prod_t = products[0]
				ppi_vals['product_tmpl_id'] = prod_t.id


	def _handle_product_id(self, field, line, pricelist, ppi_vals):
		if not ppi_vals.get('product_product'):
			input = line[field]
			product = self.env['product.product']
			dom = []

			if not self.mode_selector:
				raise exceptions.Warning('No ha seleccionado un tipo de Criterio. \n'+'Debe elegir Producto o Categoria')

			if self.mode_selector == 'id_product':
				dom_ref = dom + [('id', '=', input)]
			

			if self.mode_selector == 'id_int':
				dom_ref = dom + [('default_code', '=', input)]
			
			products = product.search(dom_ref)
			if not products:
				msg = _("Product '%s' not found !") % input
				self._log_line_error(line, msg)
				return
			elif len(products) > 1:
				msg = _("Multiple products with Reference "
						"or Name '%s' found !") % input
				self._log_line_error(line, msg)
				return
			else:
				prod = products[0]
				ppi_vals['product_id'] = prod.id

	def _get_compute_price(self, line, ppi_vals):
		if not ppi_vals.get('compute_price'):
			if line.get('fixed_price'):
				if line['fixed_price'] != '':
					ppi_vals['compute_price'] = 'fixed'
			if line.get('percent_price'):
				if line['percent_price'] != '':
					ppi_vals['compute_price'] = 'percentage'
			if line.get('price_discount'):
				if line['price_discount'] != '':
					ppi_vals['compute_price'] = 'formula'
			return ppi_vals['compute_price']


	def _handle_fixed_price(self, field, line, pricelist, ppi_vals):
		if not ppi_vals.get('fixed_price'):
			input = line[field]
			if input == '':
				ppi_vals['fixed_price'] = ''
			else:
				fixed_price = str2float(input, self.decimal_separator)
				ppi_vals['fixed_price'] = fixed_price
				
	def _handle_percent_price(self, field, line, pricelist, ppi_vals):
		if not ppi_vals.get('percent_price'):
			if line.get('percent_price'):
				input = line[field]
				if input == '':
					ppi_vals['percent_price'] = ''
				else:
					percent_price = str2float(input, self.decimal_separator)
					ppi_vals['percent_price'] = percent_price		


	# def _handle_base(self, field, line, pricelist, ppi_vals):
	# 	if not ppi_vals.get('base'):
	# 		if line.get('price_discount'):
	# 			if line['price_discount'] != '':
	# 				#en un futuro cambiar, por ahora sólo se usará basado en otra tarifa
	# 				ppi_vals['base'] = 'pricelist'
	# 			else:
	# 				ppi_vals['base'] = ''
	# 			return ppi_vals['base']
	# 		else:
	# 			return ''

	def _handle_price_discount(self, field, line, pricelist, ppi_vals):
		if not ppi_vals.get('price_discount'):
			if line.get('price_discount'):
				if line['price_discount'] != '':
					#en un futuro cambiar, por ahora sólo se usará basado en otra tarifa
					ppi_vals['base'] = 'pricelist'
					price_discount = str2float(line[field], self.decimal_separator)
					ppi_vals['price_discount'] = price_discount
				else:
					ppi_vals['base'] = ''



	def _handle_base_pricelist_id(self, field, line, pricelist, ppi_vals):
		if not ppi_vals.get('base_pricelist_id'):
			#escribir solo si hay un price_discount existente:
			if line.get('price_discount'):
				if line['price_discount'] != '':
					ppricelist = self.env['product.pricelist']
					input = line[field]##entrada (campo de csv en la pos field)name
					ppricelist_list = ppricelist.search([('name', '=', input)])
					if len(ppricelist_list) == 1:
						ppi_vals['base_pricelist_id'] = ppricelist_list.id
					if not ppricelist_list:
						msg = _("Invalid Name of Pricelist '%s' !") % input
						self._log_line_error(line, msg)
					elif len(ppricelist_list) > 1:
						msg = _("Multiple Pricelists found "
								"that match with '%s' !") % input
						self._log_line_error(line, msg)


### logica predefinida

	def traslate_header_fields(self,header_fields):
		dic_values = {
			'categoria':'categ_id',
			'producto_template':'product_tmpl_id',
			'producto':'product_id',
			'precio_fijo':'fixed_price',
			'porcentaje_fijo':'percent_price',
			'precio_descuento':'price_discount',
			'lista_precios':'base_pricelist_id',
		}

		for i,header in enumerate(header_fields):
			if header in dic_values:
				header_fields[i] = dic_values[header]
		return header_fields

	def verify_constrains_line(self,line,array_constrains):
		aux = 0
		verify = True
		for sub_array in array_constrains:
			for i, item in enumerate(sub_array):
				if line.get(item):
					if line[item] != '':
						aux += 1
			if aux == 1:
				aux = 0
				continue
			else:
				verify = False
				break
		
		return verify



	def _get_orm_fields(self):
		ppi_mod = self.env['product.pricelist.item']
		orm_fields = ppi_mod.fields_get()
		blacklist = models.MAGIC_COLUMNS + [ppi_mod.CONCURRENCY_CHECK_FIELD]
		self._orm_fields = {
			f: orm_fields[f] for f in orm_fields
			if f not in blacklist
			and not orm_fields[f].get('depends')}


	def _process_header(self, header_fields):

		self._field_methods = self._input_fields()
		self._skip_fields = []

		# header fields after blank column are considered as comments
		column_cnt = 0

		for cnt in range(len(header_fields)):
			if header_fields[cnt] == '':
				column_cnt = cnt
				break
			elif cnt == len(header_fields) - 1:
				column_cnt = cnt + 1
				break
		header_fields = header_fields[:column_cnt]

		# check for duplicate header fields
		header_fields2 = []
		for hf in header_fields:
			if hf in header_fields2:
				raise Warning(_(
					"Duplicate header field '%s' found !"
					"\nPlease correct the input file.")
					% hf)
			else:
				header_fields2.append(hf)

		for i, hf in enumerate(header_fields):

			if hf in self._field_methods:
				continue

			if hf not in self._orm_fields \
					and hf not in [self._orm_fields[f]['string'].lower()
								   for f in self._orm_fields]:
				_logger.error(
					_("%s, undefined field '%s' found "
					  "while importing move lines"),
					self._name, hf)
				self._skip_fields.append(hf)
				continue

			field_def = self._orm_fields.get(hf)
			if not field_def:
				for f in self._orm_fields:
					if self._orm_fields[f]['string'].lower() == hf:
						orm_field = f
						field_def = self._orm_fields.get(f)
						break
			else:
				orm_field = hf
			field_type = field_def['type']

			if field_type in ['char', 'text']:
				self._field_methods[hf] = {
					'method': self._handle_orm_char,
					'orm_field': orm_field,
					}
			elif field_type == 'integer':
				self._field_methods[hf] = {
					'method': self._handle_orm_integer,
					'orm_field': orm_field,
					}
			elif field_type == 'float':
				self._field_methods[hf] = {
					'method': self._handle_orm_float,
					'orm_field': orm_field,
					}
			elif field_type == 'many2one':
				self._field_methods[hf] = {
					'method': self._handle_orm_many2one,
					'orm_field': orm_field,
					}
			else:
				_logger.error(
					_("%s, the import of ORM fields of type '%s' "
					  "is not supported"),
					self._name, hf, field_type)
				self._skip_fields.append(hf)

		return header_fields

	def _log_line_error(self, line, msg):
		data = self.csv_separator.join(
			[line[hf] for hf in self._header_fields])
		self._err_log += _(
			"Error when processing line '%s'") % data + ':\n' + msg + '\n\n'

	def _handle_orm_char(self, field, line, pricelist, ppi_vals,
						 orm_field=False):
		orm_field = orm_field or field
		if not ppi_vals.get(orm_field):
			ppi_vals[orm_field] = line[field]

	def _handle_orm_integer(self, field, line, pricelist, ppi_vals,
							orm_field=False):
		orm_field = orm_field or field
		if not ppi_vals.get(orm_field):
			val = str2int(
				line[field], self.decimal_separator)
			if val is False:
				msg = _(
					"Incorrect value '%s' "
					"for field '%s' of type Integer !"
					) % (line[field], field)
				self._log_line_error(line, msg)
			else:
				ppi_vals[orm_field] = val

	def _handle_orm_float(self, field, line, pricelist, ppi_vals,
						  orm_field=False):
		orm_field = orm_field or field
		if not ppi_vals.get(orm_field):
			ppi_vals[orm_field] = str2float(
				line[field], self.decimal_separator)

			val = str2float(
				line[field], self.decimal_separator)
			if val is False:
				msg = _(
					"Incorrect value '%s' "
					"for field '%s' of type Numeric !"
					) % (line[field], field)
				self._log_line_error(line, msg)
			else:
				ppi_vals[orm_field] = val

	def _handle_orm_many2one(self, field, line, pricelist, ppi_vals,
							 orm_field=False):
		orm_field = orm_field or field
		if not ppi_vals.get(orm_field):
			val = str2int(
				line[field], self.decimal_separator)
			if val is False:
				msg = _(
					"Incorrect value '%s' "
					"for field '%s' of type Many2One !"
					"\nYou should specify the database key "
					"or contact your IT department "
					"to add support for this field."
					) % (line[field], field)
				self._log_line_error(line, msg)
			else:
				ppi_vals[orm_field] = val

	@api.model
	def _default_codepage(self):
		return 'Windows-1252'

	@api.one
	@api.depends('ppi_data')
	def _compute_lines(self):
		if self.ppi_data:
			self.lines = base64.decodestring(self.ppi_data)

	@api.one
	@api.depends('lines', 'csv_separator')
	def _compute_dialect(self):
		if self.lines:
			try:
				self.dialect = csv.Sniffer().sniff(
					self.lines[:128], delimiters=';,')
			except:
				# csv.Sniffer is not always reliable
				# in the detection of the delimiter
				self.dialect = csv.Sniffer().sniff(
					'"header 1";"header 2";\r\n')
				if ',' in self.lines[128]:
					self.dialect.delimiter = ','
				elif ';' in self.lines[128]:
					self.dialect.delimiter = ';'
		if self.csv_separator:
			self.dialect.delimiter = str(self.csv_separator)

	@api.onchange('ppi_data')
	def _onchange_ppi_data(self):
		if self.lines:
			self.csv_separator = self.dialect.delimiter
			if self.csv_separator == ';':
				self.decimal_separator = '.'

	@api.onchange('csv_separator')
	def _onchange_csv_separator(self):
		if self.csv_separator and self.ppi_data:
			self.dialect.delimiter = self.csv_separator

	def _remove_leading_lines(self, lines):
		""" remove leading blank or comment lines """
		input = StringIO.StringIO(lines)
		header = False
		while not header:
			ln = input.next()
			if not ln or ln and ln[0] in [self.csv_separator, '#']:
				continue
			else:
				header = ln.lower()
		if not header:
			raise Warning(
				_("No header line found in the input file !"))
		output = input.read()
		return output, header

		# verificar los if de las entradas con estructuras nuevas para luego darle como seria la forma final.
		# tomar en cuenta que no son ids sino code
		# probar caoss 1 o 2 new campos o 0.


def str2float(amount, decimal_separator):
	if not amount:
		return 0.0
	try:
		if decimal_separator == '.':
			return float(amount.replace(',', ''))
		else:
			return float(amount.replace('.', '').replace(',', '.'))
	except:
		return False


def str2int(amount, decimal_separator):
	if not amount:
		return 0
	try:
		if decimal_separator == '.':
			return int(amount.replace(',', ''))
		else:
			return int(amount.replace('.', '').replace(',', '.'))
	except:
		return False
