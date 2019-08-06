# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class it_invoice_serie(models.Model):
	_name = 'it.invoice.serie'
	
	name = fields.Char(string="Serie",size=64)
	type_document_id = fields.Many2one('einvoice.catalog.01', string="Tipo de Documento",index=True)
	sequence_id = fields.Many2one('ir.sequence', string="Secuencia",index=True)
	description = fields.Char(string="Descripción",size=255)