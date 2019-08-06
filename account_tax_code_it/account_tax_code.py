# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class account_tax_code(models.Model):
	_name = 'account.tax.code'

	name = fields.Char(u'Nombre Código de Impuesto')
	code = fields.Char('Código')
	parent_id = fields.Many2one('account.tax.code','Código Padre')
	sequence = fields.Integer('Secuencia')

	record_shop = fields.Selection((('1','Base Imponible destinadas a operaciones de Gravadas y/o de exportación.'),
									('2','Base Imponible destinadas a operaciones gravadas y/o de exportación y a operaciones no gravadas. '),
									('3','Base Imponible destinadas a operaciones no gravadas.'),
									('4','Compras No Gravadas.'),
									('5','Impuesto Selectivo al Consumo.'),
									('6','Otros.'),
									('7','Impuesto para Base Imponible destinadas a operacioens de Gravadas y/o de exportación.'),
									('8','Impuesto para Base Imponible destinadas a operaciones gravadas y/o de exportación y a operacioens no gravadas.'),
									('9','Impuesto para Base Imponible destinadas a operaciones no gravadas')
									),'Registro de Compra')


	record_sale = fields.Selection((('1','Valor de Exportacion.'),
									('2','Base Imponible Ventas.'),
									('3','Ventas Inafectas.'),
									('4','Ventas Exoneradas.'),
									('5','Impuesto Selectivo al Consumo.'),
									('6','Otros.'),
									('7','Impuesto para Base Imponible Ventas.')
									),'Registro de Venta')

	record_fees = fields.Selection((('1','Renta de Cuarta.'),
									('2','Retencion.')
									),'Libro de Honorarios')


class account_tax(models.Model):
	_name = 'account.tax'
	_inherit='account.tax'

	base_code_id = fields.Many2one('account.tax.code','Código Base Cuenta')
	tax_code_id = fields.Many2one('account.tax.code','Código Impuesto Contable')


	ref_base_code_id = fields.Many2one('account.tax.code','Código Base Reintegro')
	ref_tax_code_id = fields.Many2one('account.tax.code','Código Impuesto Reintegro')

class account_move_line(models.Model):
	_inherit = 'account.move.line'

	tax_code_id = fields.Many2one('account.tax.code','Código Impuesto Contable')


class account_invoice(models.Model):
	_inherit = 'account.invoice'

	@api.model
	def invoice_line_move_line_get(self):
		t = super(account_invoice,self).invoice_line_move_line_get()
		for i in t:
			invoice_line_id = self.env['account.invoice.line'].browse(i['invl_id'])
			if self.type not in ('out_refund','in_refund'):
				i['tax_code_id'] = invoice_line_id.invoice_line_tax_ids[0].base_code_id.id if len(invoice_line_id.invoice_line_tax_ids) >0 else 0
			else:
				i['tax_code_id'] = invoice_line_id.invoice_line_tax_ids[0].ref_base_code_id.id if len(invoice_line_id.invoice_line_tax_ids) >0 else 0

			i['tax_amount'] = (i['price'])
		return t

	@api.model
	def tax_line_move_line_get(self):
		t = super(account_invoice,self).tax_line_move_line_get()
		for i in t:
			tax_id = self.env['account.tax'].browse(i['tax_line_id'])

			if self.type not in ('out_refund','in_refund'):
				i['tax_code_id'] = tax_id.tax_code_id.id
			else:
				i['tax_code_id'] = tax_id.ref_tax_code_id.id

			i['tax_amount'] = (i['price'])
		return t


	@api.model
	def line_get_convert(self, line, part):
		t = super(account_invoice,self).line_get_convert(line,part)
		t['tax_code_id'] = line.get('tax_code_id',False)
		t['tax_amount'] = line.get('tax_amount',0)
		return  t