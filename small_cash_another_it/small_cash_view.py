# -*- coding: utf-8 -*-
import base64
import codecs

from openerp.osv import osv
from openerp import models, fields, api


from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table
from reportlab.lib.units import  cm,mm
from reportlab.lib.utils import simpleSplit
from cgi import escape
import decimal

	
class small_cash_view(models.Model):
	_name = 'small.cash.view'
	_auto = False

	caja_nro = fields.Char('Nro. Caja')
	responsable = fields.Char('Responsable')	
	periodo = fields.Char('Periodo')
	libro = fields.Char('Libro')
	voucher = fields.Char('Voucher')
	cuenta = fields.Char('Cuenta')
	proveedor = fields.Char('Proveedor')
	fecha = fields.Char('Fecha')
	tipo_doc = fields.Char('Tipo Doc.')
	nro_comprobante = fields.Char('Nro. Comprobante')
	monto = fields.Float('Monto',digits=(12,2))

	_order = 'caja_nro,periodo,libro,voucher'

	@api.model_cr 
	def init(self):

		self.env.cr.execute(""" DROP VIEW IF EXISTS small_cash_view;
			create or replace view small_cash_view as (
			

select 
tt.move_id as id,
z7.name as caja_nro,
z7.responsable,
z5.name as periodo,
z4.name as libro,
z1.name as voucher,
z2.code as cuenta,
z3.name as proveedor,
z1.date as fecha,
z6.code as tipo_doc,
tt.nro_comprobante,
tt.monto
--tt.pagos 
from 
	(select distinct 
	provision.identifica,
	provision.move_id,
	provision.partner_id,
	provision.account_id,
	provision.type_document_it,
	provision.nro_comprobante,
	provision.monto as monto,
	--pago.debit as pagos,
	pago.small_cash_id
	
	from 
		(select concat(a1.partner_id,a1.account_id,a1.type_document_it,nro_comprobante) as identifica,a1.id,move_id,partner_id,type_document_it,account_id,nro_comprobante,credit as monto from account_move_line as a1
		left join account_account a2 on a2.id=a1.account_id
		left join account_account_type at3 on at3.id = a2.user_type_id
		where at3.type='payable' and debit =0 and credit > 0) as provision
		inner join (
		select concat(x3.partner_id,x3.account_id,x3.type_document_it,x3.nro_comprobante) as identifica,x4.small_cash_id,x3.move_id,x3.partner_id,x3.type_document_it,x3.account_id, x3.nro_comprobante
		--x3.debit 
		from (select x1.id,x1.move_id,x1.partner_id,x1.type_document_it,x1.account_id,x1.nro_comprobante 
		      --,x1.debit
		      from account_move_line as x1
		left join account_account x2 on x2.id=x1.account_id
		left join account_account_type ax3 on ax3.id = x2.user_type_id
		where ax3.type='payable') as x3
	inner join (select move_id,small_cash_id from account_move_line where small_cash_id is not null) x4 on x4.move_id=x3.move_id) pago
	on pago.identifica=provision.identifica) as tt

left join account_move z1 on z1.id=tt.move_id
left join account_account z2 on z2.id=tt.account_id
left join res_partner z3 on z3.id=tt.partner_id
left join account_journal z4 on z4.id=z1.journal_id
left join account_period z5 on z5.date_start <= z1.date and z5.date_stop >= z1.date and z5.special = z1.fecha_special
left join einvoice_catalog_01 z6 on z6.id=tt.type_document_it
left join(select small_cash_another.id,small_cash_another.name,res_partner.name as responsable,small_cash_another.name as nro_caja from small_cash_another
	  left join res_users on res_users.id=small_cash_another.user_id
	  left join res_partner on res_partner.id=res_users.partner_id) z7 on z7.id=tt.small_cash_id
order by caja_nro,periodo,libro,voucher )""")