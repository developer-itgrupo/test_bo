# -*- coding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint
import io
from xlsxwriter.workbook import Workbook
import sys
from datetime import datetime
from datetime import timedelta
import os
from dateutil.relativedelta import *
import decimal
import calendar
from openerp import models, fields, api
import urllib2
import json

class account_invoice_ebill(models.Model):
	_name='account.invoice.ebill'

	total_anticipos =fields.Float('total_anticipos')
	total_descuentos=fields.Float('total_descuentos')
	total_gravado=fields.Float('total_gravado')
	total_inafecto=fields.Float('total_inafecto')
	total_exonerado=fields.Float('total_exonerado')
	total_igv=fields.Float('total_igv')
	total_gratuita=fields.Float('total_gratuita')
	total_otros_cargos=fields.Float('total_otros_cargos')
	total_incluido_percepcion=fields.Float('total_incluido_percepción')
	invoice_id=fields.Many2one('account.invoice','factura')


class account_invoice_line_ebill(models.Model):
	_name='account.invoice.line.ebill'

	porcentaje_impuesto=fields.Float('porcentaje_impuesto')
	precio_impuesto_incluido=fields.Float('precio_impuesto_incluido')
	precio_sin_impuestos_incluido=fields.Float('precio_sin_impuestos_incluido')
	monto_descuento=fields.Float('monto_descuento')
	monto_igv=fields.Float('monto_igv')
	monto_otros_impuestos=fields.Float('monto_otros_impuestos')
	subtotal_impuesto=fields.Float('subtotal_impuesto')
	subtotal_sin_impuesto=fields.Float('subtotal_impuesto')
	invoice_line_id=fields.Many2one('account.invoice.line','factura')