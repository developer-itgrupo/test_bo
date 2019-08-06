# -*- encoding: utf-8 -*-
from openerp import fields, models, api
from openerp.osv import osv
import base64
from zipfile import ZipFile

class it_invoice_serie(models.Model):
	_inherit = 'it.invoice.serie'


	manual = fields.Boolean(string="Es manual")