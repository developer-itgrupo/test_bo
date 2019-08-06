# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
import codecs
from openerp import models, fields, api  , exceptions , _
from datetime import datetime, date, time, timedelta
from openerp.osv import osv
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


from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

import time
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import *
from odoo.exceptions import UserError, ValidationError


class account_purchase_register_wizard(osv.TransientModel):
	_name='account.purchase.register.wizard'

	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end = fields.Many2one('account.period','Periodo Final',required=True)	
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('pdf','PDF'),('csv','CSV')], 'Mostrar en', required=True)
	simplificado = fields.Boolean('Registro Simplificado',default=True)

	@api.model
	def get_wizard(self):
		return self.env['automatic.fiscalyear'].get_wizard('Registro de Compras',self.id,'account.purchase.register.wizard','account_registro_compra_it.view_account_purchase_register_wizard_form','default_period_ini','default_period_end')

	@api.onchange('period_ini','period_end')
	def _change_periodo_ini(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
		if not year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			return {'domain':{'period_ini':[('fiscalyear_id','=',year.id )],'period_end':[('fiscalyear_id','=',year.id )]}}

	save_page_states= []

	@api.multi
	def do_rebuild(self):
		period_ini = self.period_ini
		period_end = self.period_end
		
		filtro = []
		self.save_page_states= []
				
		self.env.cr.execute("""
			CREATE OR REPLACE view account_purchase_register as (
				SELECT * 
				FROM get_compra_1_1_1(periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""')) 
		)""")

		#DSC_Exportar a CSV por el numero de filas
		self.env.cr.execute("""select count(*)  from account_purchase_register""")
		rows = self.env.cr.fetchone()
		#if self.type_show == 'excel' and rows[0] > 1000:
		#	self.type_show = 'csv'

		#if self.type_show == 'pdf' and rows[0] > 1000:
		#	self.type_show = 'csv'


		if self.type_show == 'pantalla':
			view_id = self.env.ref('account_registro_compra_it.view_move_purchase_register_tree',False)
			if self.simplificado:
				view_id = self.env.ref('account_registro_compra_it.view_move_purchase_register_tree_simplificado',False)
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.purchase.register',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(view_id.id, 'tree')],
			}


		#DSC_
		if self.type_show == 'csv':
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			docname = 'RegistroCompras.csv'
			#CSV
			sql_query = """	COPY (SELECT * FROM account_purchase_register )TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
							"""
			if self.simplificado:
				sql_query = """	COPY (SELECT libro,voucher,fechaemision,fechavencimiento,tipodocumento,serie,numero,tdp as td,ruc as numero, razonsocial as proveedor,glosa as concepto, coalesce(cng,0)+ coalesce(otros,0) as nogravado, isc, coalesce(bioge,0)+coalesce(biogeng,0)+coalesce(biong,0) as baseimponible, coalesce(igva,0)+coalesce(igvb,0)+coalesce(igvc,0) as igv, total, td,seried,numerodd,fechadm,fechad,numerod,tc FROM account_purchase_register )TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
							"""

			self.env.cr.execute(sql_query)
			#Caracteres Especiales
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			f = open(direccion + docname, 'rb')			
			vals = {
				'output_name': docname,
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

		if self.type_show == 'excel':

			if self.simplificado:
				import io
				from xlsxwriter.workbook import Workbook
				output = io.BytesIO()
				########### PRIMERA HOJA DE LA DATA EN TABLA
				#workbook = Workbook(output, {'in_memory': True})
				direccion = self.env['main.parameter'].search([])[0].dir_create_file
				workbook = Workbook(direccion + 'tempo_librocompras.xlsx')
				worksheet = workbook.add_worksheet("Registro Compras")
				#Print Format
				worksheet.set_landscape() #Horizontal
				worksheet.set_paper(9) #A-4
				worksheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
				worksheet.fit_to_pages(1, 0)  # Ajustar por Columna	

				bold = workbook.add_format({'bold': True})
				normal = workbook.add_format()
				boldbord = workbook.add_format({'bold': True})
				boldbord.set_border(style=2)
				boldbord.set_align('center')
				boldbord.set_align('vcenter')
				boldbord.set_text_wrap()
				boldbord.set_font_size(9)
				boldbord.set_bg_color('#DCE6F1')


				title = workbook.add_format({'bold': True})
				title.set_align('center')
				title.set_align('vcenter')
				title.set_text_wrap()
				title.set_font_size(20)

				numbertres = workbook.add_format({'num_format':'0.000'})
				numberdos = workbook.add_format({'num_format':'0.00'})
				bord = workbook.add_format()
				bord.set_border(style=1)
				bord.set_text_wrap()
				numberdos.set_border(style=1)
				numbertres.set_border(style=1)			
				x= 8				
				tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
				tam_letra = 1.2
				import sys
				reload(sys)
				sys.setdefaultencoding('iso-8859-1')

				worksheet.merge_range(0,0,0,23,"REGISTRO DE COMPRA",title)
				
				company = self.env['res.company'].search([])[0].partner_id
				
				worksheet.write(1,0, "Empresa:".upper(),bold)
				worksheet.write(1,1, company.name.upper(), bold)
				
				worksheet.write(2,0, "RUC:",bold)
				worksheet.write(2,1, company.nro_documento, bold)
				
				worksheet.write(3,0, u"Dirección:".upper(),bold)
				worksheet.write(3,1, company.street.upper() if company.street else '', bold)

				worksheet.write(4,0, "Registro Compras:".upper(), bold)
				tam_col[0] = tam_letra* len("Registro Compras:") if tam_letra* len("Registro Compras:")> tam_col[0] else tam_col[0]

				worksheet.write(4,1, self.period_ini.name, normal)
				tam_col[1] = tam_letra* len(self.period_ini.name) if tam_letra* len(self.period_ini.name)> tam_col[1] else tam_col[1]

				worksheet.write(4,2, self.period_end.name, normal)
				tam_col[2] = tam_letra* len(self.period_end.name) if tam_letra* len(self.period_end.name)> tam_col[2] else tam_col[2]

				worksheet.write(5,0, "Fecha:".upper(),bold)
				tam_col[0] = tam_letra* len("Fecha:") if tam_letra* len("Fecha:")> tam_col[0] else tam_col[0]

				#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
				import datetime
				worksheet.write(5,1, str(datetime.datetime.today())[:10], normal)
				tam_col[1] = tam_letra* len(str(datetime.datetime.today())[:10]) if tam_letra* len(str(datetime.datetime.today())[:10])> tam_col[1] else tam_col[1]
				

				worksheet.write(7,0, "Libro",boldbord)
				worksheet.write(7,1, "Voucher",boldbord)
				worksheet.write(7,2, u"Fecha Emisión",boldbord)
				worksheet.write(7,3, u"Fecha Vencimiento",boldbord)
				worksheet.write(7,4, "TD.",boldbord)
				worksheet.write(7,5, "Serie",boldbord)
				worksheet.write(7,6, u"Número",boldbord)
				worksheet.write(7,7, "TDP.",boldbord)
				worksheet.write(7,8, "RUC/DNI",boldbord)
				worksheet.write(7,9, u"Proveedor",boldbord)
				worksheet.write(7,10, u"Concepto",boldbord)
				worksheet.write(7,11, "No Gravado",boldbord)
				worksheet.write(7,12, u"ISC",boldbord)
				worksheet.write(7,13, "Base Imponible",boldbord)
				worksheet.write(7,14, u"IGV",boldbord)
				worksheet.write(7,15, u"Total",boldbord)
				worksheet.write(7,16, u"TD Doc.",boldbord)
				worksheet.write(7,17, u"Serie",boldbord)
				worksheet.write(7,18, u"Número",boldbord)
				worksheet.write(7,19, u"F. Doc. M.",boldbord)
				worksheet.write(7,20, u"Fecha Doc.",boldbord)
				worksheet.write(7,21, u"Número Doc",boldbord)
				worksheet.write(7,22, u"TC.",boldbord)
				
				totales = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]


				for line in self.env['account.purchase.register'].search([]):
					worksheet.write(x,0,line.libro if line.libro  else '',bord )
					worksheet.write(x,1,line.voucher if line.voucher  else '',bord)
					worksheet.write(x,2,line.fechaemision if line.fechaemision else '',bord)
					worksheet.write(x,3,line.fechavencimiento if line.fechavencimiento else '',bord)
					worksheet.write(x,4,line.tipodocumento if line.tipodocumento else '',bord)
					worksheet.write(x,5,line.serie if line.serie else '',bord)
					worksheet.write(x,6,line.numero if line.numero  else '',bord)
					worksheet.write(x,7,line.tdp if line.tdp  else '',bord)
					worksheet.write(x,8,line.ruc if line.ruc  else '',bord)
					worksheet.write(x,9,line.razonsocial.upper() if line.razonsocial  else '',bord)					
					worksheet.write(x,10,line.glosa if line.glosa else '',bord)
					worksheet.write(x,11,line.nogravado ,numberdos)
					worksheet.write(x,12,line.isc ,numberdos)
					worksheet.write(x,13,line.baseimponible ,numberdos)
					worksheet.write(x,14,line.igvtotal ,numberdos)
					worksheet.write(x,15,line.total ,numberdos)
					worksheet.write(x,16,line.td if line.td else '',bord)
					worksheet.write(x,17,line.seried if line.seried else '',bord)
					worksheet.write(x,18,line.numerodd if line.numerodd else '',bord)
					worksheet.write(x,19,line.fechadm if line.fechadm else '',bord)
					worksheet.write(x,20,line.fechad if line.fechad else '',bord)
					worksheet.write(x,21,line.numerod if line.numerod else '',bord)
					worksheet.write(x,22,line.tc ,numbertres)


					totales[0] += line.cng
					totales[1] += line.isc
					totales[2] += line.baseimponible
					totales[3] += line.igvtotal
					totales[4] += line.total


					x = x +1



				worksheet.write(x,10,'Totales:',bord)
				worksheet.write(x,11,totales[0] ,numberdos)
				worksheet.write(x,12,totales[1] ,numberdos)
				worksheet.write(x,13,totales[2] ,numberdos)
				worksheet.write(x,14,totales[3] ,numberdos)
				worksheet.write(x,15,totales[4] ,numberdos)


				tam_col = [18,16,12,12,6,12,15,6,10,45,20,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15]

				worksheet.set_row(0, 31)
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
				worksheet.set_column('M:M', tam_col[12])
				worksheet.set_column('N:N', tam_col[13])
				worksheet.set_column('O:O', tam_col[14])
				worksheet.set_column('P:P', tam_col[15])
				worksheet.set_column('Q:Q', tam_col[16])
				worksheet.set_column('R:R', tam_col[17])
				worksheet.set_column('S:S', tam_col[18])
				worksheet.set_column('T:T', tam_col[19])
				worksheet.set_column('U:U', tam_col[20])
				worksheet.set_column('V:V', tam_col[21])
				worksheet.set_column('W:W', tam_col[22])
				worksheet.set_column('X:X', tam_col[23])
				worksheet.set_column('Y:Y', tam_col[24])
				worksheet.set_column('Z:Z', tam_col[25])
				worksheet.set_column('AA:AA', tam_col[26])
				worksheet.set_column('AB:AB', tam_col[27])
				worksheet.set_column('AC:AC', tam_col[28])
				worksheet.set_column('AD:AD', tam_col[29])
				worksheet.set_column('AE:AE', tam_col[30])
				worksheet.set_column('AF:AF', tam_col[31])

				workbook.close()
				
				f = open( direccion + 'tempo_librocompras.xlsx', 'rb')			
				
				vals = {
					'output_name': 'RegistroCompras.xlsx',
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


			else:

				import io
				from xlsxwriter.workbook import Workbook
				output = io.BytesIO()
				########### PRIMERA HOJA DE LA DATA EN TABLA
				#workbook = Workbook(output, {'in_memory': True})
				direccion = self.env['main.parameter'].search([])[0].dir_create_file
				workbook = Workbook(direccion + 'tempo_librocompras.xlsx')
				worksheet = workbook.add_worksheet("Registro Compras")
				#Print Format
				worksheet.set_landscape() #Horizontal
				worksheet.set_paper(9) #A-4
				worksheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
				worksheet.fit_to_pages(1, 0)  # Ajustar por Columna	

				bold = workbook.add_format({'bold': True})
				normal = workbook.add_format()
				boldbord = workbook.add_format({'bold': True})
				boldbord.set_border(style=2)
				boldbord.set_align('center')
				boldbord.set_align('vcenter')
				boldbord.set_text_wrap()
				boldbord.set_font_size(9)
				boldbord.set_bg_color('#DCE6F1')


				title = workbook.add_format({'bold': True})
				title.set_align('center')
				title.set_align('vcenter')
				title.set_text_wrap()
				title.set_font_size(20)

				numbertres = workbook.add_format({'num_format':'0.000'})
				numberdos = workbook.add_format({'num_format':'0.00'})
				bord = workbook.add_format()
				bord.set_border(style=1)
				bord.set_text_wrap()
				numberdos.set_border(style=1)
				numbertres.set_border(style=1)			
				x= 8				
				tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
				tam_letra = 1.2
				import sys
				reload(sys)
				sys.setdefaultencoding('iso-8859-1')

				worksheet.merge_range(0,0,0,23,"REGISTRO DE COMPRA",title)
				
				company = self.env['res.company'].search([])[0].partner_id
				
				worksheet.write(1,0, "Empresa:".upper(),bold)
				worksheet.write(1,1, company.name.upper(), bold)
				
				worksheet.write(2,0, "RUC:",bold)
				worksheet.write(2,1, company.nro_documento, bold)
				
				worksheet.write(3,0, u"Dirección:".upper(),bold)
				worksheet.write(3,1, company.street.upper() if company.street else '', bold)

				worksheet.write(4,0, "Registro Compras:".upper(), bold)
				tam_col[0] = tam_letra* len("Registro Compras:") if tam_letra* len("Registro Compras:")> tam_col[0] else tam_col[0]

				worksheet.write(4,1, self.period_ini.name, normal)
				tam_col[1] = tam_letra* len(self.period_ini.name) if tam_letra* len(self.period_ini.name)> tam_col[1] else tam_col[1]

				worksheet.write(4,2, self.period_end.name, normal)
				tam_col[2] = tam_letra* len(self.period_end.name) if tam_letra* len(self.period_end.name)> tam_col[2] else tam_col[2]

				worksheet.write(5,0, "Fecha:".upper(),bold)
				tam_col[0] = tam_letra* len("Fecha:") if tam_letra* len("Fecha:")> tam_col[0] else tam_col[0]

				#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
				import datetime
				worksheet.write(5,1, str(datetime.datetime.today())[:10], normal)
				tam_col[1] = tam_letra* len(str(datetime.datetime.today())[:10]) if tam_letra* len(str(datetime.datetime.today())[:10])> tam_col[1] else tam_col[1]
				

				worksheet.write(7,0, "Periodo",boldbord)
				tam_col[0] = tam_letra* len("Periodo") if tam_letra* len("Periodo")> tam_col[0] else tam_col[0]
				worksheet.write(7,1, "Libro",boldbord)
				tam_col[1] = tam_letra* len("Libro") if tam_letra* len("Libro")> tam_col[1] else tam_col[1]
				worksheet.write(7,2, "Voucher",boldbord)
				tam_col[2] = tam_letra* len("Voucher") if tam_letra* len("Voucher")> tam_col[2] else tam_col[2]
				worksheet.write(7,3, u"Fecha Emisión",boldbord)
				tam_col[3] = tam_letra* len(u"Fecha Emisión") if tam_letra* len(u"Fecha Emisión")> tam_col[3] else tam_col[3]
				worksheet.write(7,4, u"Fecha Vencimiento",boldbord)
				tam_col[4] = tam_letra* len(u"Fecha Vencimiento") if tam_letra* len(u"Fecha Vencimiento")> tam_col[4] else tam_col[4]
				worksheet.write(7,5, "TD.",boldbord)
				tam_col[5] = tam_letra* len("TD.") if tam_letra* len("TD.")> tam_col[5] else tam_col[5]
				worksheet.write(7,6, "Serie",boldbord)
				tam_col[6] = tam_letra* len("Serie") if tam_letra* len("Serie")> tam_col[6] else tam_col[6]
				worksheet.write(7,7, u"Año",boldbord)
				tam_col[7] = tam_letra* len(u"Año") if tam_letra* len(u"Año")> tam_col[7] else tam_col[7]
				worksheet.write(7,8, u"Número",boldbord)
				tam_col[8] = tam_letra* len(u"Número") if tam_letra* len(u"Número")> tam_col[8] else tam_col[8]
				worksheet.write(7,9, "TDP.",boldbord)
				tam_col[9] = tam_letra* len("TDP.") if tam_letra* len("TDP.")> tam_col[9] else tam_col[9]
				worksheet.write(7,10, "RUC/DNI",boldbord)
				tam_col[10] = tam_letra* len("RUC/DNI") if tam_letra* len("RUC/DNI")> tam_col[10] else tam_col[10]
				worksheet.write(7,11, u"Razon Social",boldbord)
				tam_col[11] = tam_letra* len(u"Razon Social") if tam_letra* len(u"Razon Social")> tam_col[11] else tam_col[11]
				worksheet.write(7,12, u"BIOGE",boldbord)
				tam_col[12] = tam_letra* len(u"BIOGE") if tam_letra* len(u"BIOGE")> tam_col[12] else tam_col[12]
				worksheet.write(7,13, u"BIOGENG",boldbord)
				tam_col[13] = tam_letra* len(u"BIOGENG") if tam_letra* len(u"BIOGENG")> tam_col[13] else tam_col[13]
				worksheet.write(7,14, "BIONG",boldbord)
				tam_col[14] = tam_letra* len("BIONG") if tam_letra* len("BIONG")> tam_col[14] else tam_col[14]
				worksheet.write(7,15, "CNG",boldbord)
				tam_col[15] = tam_letra* len("CNG") if tam_letra* len("CNG")> tam_col[15] else tam_col[15]
				worksheet.write(7,16, u"ISC",boldbord)
				tam_col[16] = tam_letra* len(u"ISC") if tam_letra* len(u"ISC")> tam_col[16] else tam_col[16]
				worksheet.write(7,17, u"IGVA",boldbord)
				tam_col[17] = tam_letra* len(u"IGVA") if tam_letra* len(u"IGVA")> tam_col[17] else tam_col[17]
				worksheet.write(7,18, u"IGVB",boldbord)
				tam_col[18] = tam_letra* len(u"IGVB") if tam_letra* len(u"IGVB")> tam_col[18] else tam_col[18]
				worksheet.write(7,19, u"IGBC",boldbord)
				tam_col[19] = tam_letra* len(u"IGBC") if tam_letra* len(u"IGBC")> tam_col[19] else tam_col[19]
				worksheet.write(7,20, u"Otros",boldbord)
				tam_col[20] = tam_letra* len(u"Otros") if tam_letra* len(u"Otros")> tam_col[20] else tam_col[20]
				worksheet.write(7,21, u"Total",boldbord)
				tam_col[21] = tam_letra* len(u"Total") if tam_letra* len(u"Total")> tam_col[21] else tam_col[21]
				worksheet.write(7,22, u"CSND",boldbord)
				tam_col[22] = tam_letra* len(u"CSND") if tam_letra* len(u"CSND")> tam_col[22] else tam_col[22]
				worksheet.write(7,23, u"Moneda",boldbord)
				tam_col[23] = tam_letra* len(u"Moneda") if tam_letra* len(u"Moneda")> tam_col[23] else tam_col[23]
				worksheet.write(7,24, u"TC.",boldbord)
				tam_col[24] = tam_letra* len(u"TC.") if tam_letra* len(u"TC.")> tam_col[24] else tam_col[24]
				worksheet.write(7,25, u"Fecha Doc.",boldbord)
				tam_col[25] = tam_letra* len(u"Fecha Doc.") if tam_letra* len(u"Fecha Doc.")> tam_col[25] else tam_col[25]
				worksheet.write(7,26, u"Número Doc",boldbord)
				tam_col[26] = tam_letra* len(u"Número Doc") if tam_letra* len(u"Número Doc")> tam_col[26] else tam_col[26]
				worksheet.write(7,27, u"F. Doc. M.",boldbord)
				tam_col[27] = tam_letra* len(u"F. Doc. M.") if tam_letra* len(u"F. Doc. M.")> tam_col[27] else tam_col[27]
				worksheet.write(7,28, u"TD Doc.",boldbord)
				tam_col[28] = tam_letra* len(u"TD Doc.") if tam_letra* len(u"TD Doc.")> tam_col[28] else tam_col[28]
				worksheet.write(7,29, u"Serie",boldbord)
				tam_col[29] = tam_letra* len(u"Serie") if tam_letra* len(u"Serie")> tam_col[29] else tam_col[29]
				worksheet.write(7,30, u"Número",boldbord)
				tam_col[30] = tam_letra* len(u"Número") if tam_letra* len(u"Número")> tam_col[30] else tam_col[30]
				worksheet.write(7,31, u"Glosa",boldbord)
				tam_col[31] = tam_letra* len(u"Glosa") if tam_letra* len(u"Glosa")> tam_col[31] else tam_col[31]

				totales = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
				for line in self.env['account.purchase.register'].search([]):
					worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
					worksheet.write(x,1,line.libro if line.libro  else '',bord )
					worksheet.write(x,2,line.voucher if line.voucher  else '',bord)
					worksheet.write(x,3,line.fechaemision if line.fechaemision else '',bord)
					worksheet.write(x,4,line.fechavencimiento if line.fechavencimiento else '',bord)
					worksheet.write(x,5,line.tipodocumento if line.tipodocumento else '',bord)
					worksheet.write(x,6,line.serie if line.serie else '',bord)
					worksheet.write(x,7,line.anio if line.anio else '',bord)
					worksheet.write(x,8,line.numero if line.numero  else '',bord)
					worksheet.write(x,9,line.tdp if line.tdp  else '',bord)
					worksheet.write(x,10,line.ruc if line.ruc  else '',bord)
					worksheet.write(x,11,line.razonsocial.upper() if line.razonsocial  else '',bord)
					worksheet.write(x,12,line.bioge ,numberdos)
					worksheet.write(x,13,line.biogeng ,numberdos)
					worksheet.write(x,14,line.biong ,numberdos)
					worksheet.write(x,15,line.cng ,numberdos)
					worksheet.write(x,16,line.isc ,numberdos)
					worksheet.write(x,17,line.igva ,numberdos)
					worksheet.write(x,18,line.igvb ,numberdos)
					worksheet.write(x,19,line.igvc ,numberdos)
					worksheet.write(x,20,line.otros ,numberdos)
					worksheet.write(x,21,line.total ,numberdos)
					worksheet.write(x,22,line.comprobante if line.comprobante  else '',bord)
					worksheet.write(x,23,line.moneda if  line.moneda else '',bord)
					worksheet.write(x,24,line.tc ,numbertres)
					worksheet.write(x,25,line.fechad if line.fechad else '',bord)
					worksheet.write(x,26,line.numerod if line.numerod else '',bord)
					worksheet.write(x,27,line.fechadm if line.fechadm else '',bord)
					worksheet.write(x,28,line.td if line.td else '',bord)
					worksheet.write(x,29,line.seried if line.seried else '',bord)
					worksheet.write(x,30,line.numerodd if line.numerodd else '',bord)
					worksheet.write(x,31,line.glosa if line.glosa else '',bord)

					totales[0] += line.bioge
					totales[1] += line.biogeng
					totales[2] += line.biong
					totales[3] += line.cng
					totales[4] += line.isc
					totales[5] += line.igva
					totales[6] += line.igvb
					totales[7] += line.igvc
					totales[8] += line.otros
					totales[9] += line.total


					tam_col[0] = tam_letra* len(line.periodo if line.periodo else '' ) if tam_letra* len(line.periodo if line.periodo else '' )> tam_col[0] else tam_col[0]
					tam_col[1] = tam_letra* len(line.libro if line.libro  else '') if tam_letra* len(line.libro if line.libro  else '')> tam_col[1] else tam_col[1]
					tam_col[2] = tam_letra* len(line.voucher if line.voucher  else '') if tam_letra* len(line.voucher if line.voucher  else '')> tam_col[2] else tam_col[2]
					tam_col[3] = tam_letra* len(line.fechaemision if line.fechaemision else '') if tam_letra* len(line.fechaemision if line.fechaemision else '')> tam_col[3] else tam_col[3]
					tam_col[4] = tam_letra* len(line.fechavencimiento if line.fechavencimiento else '') if tam_letra* len(line.fechavencimiento if line.fechavencimiento else '')> tam_col[4] else tam_col[4]
					tam_col[5] = tam_letra* len(line.tipodocumento if line.tipodocumento else '') if tam_letra* len(line.tipodocumento if line.tipodocumento else '')> tam_col[5] else tam_col[5]
					tam_col[6] = tam_letra* len(line.serie if line.serie else '') if tam_letra* len(line.serie if line.serie else '')> tam_col[6] else tam_col[6]
					tam_col[7] = tam_letra* len(line.anio if line.anio else '') if tam_letra* len(line.anio if line.anio else '')> tam_col[7] else tam_col[7]
					tam_col[8] = tam_letra* len(line.numero if line.numero  else '') if tam_letra* len(line.numero if line.numero  else '')> tam_col[8] else tam_col[8]
					tam_col[9] = tam_letra* len(line.tdp if line.tdp  else '') if tam_letra* len(line.tdp if line.tdp  else '')> tam_col[9] else tam_col[9]
					tam_col[10] = tam_letra* len(line.ruc if line.ruc  else '') if tam_letra* len(line.ruc if line.ruc  else '')> tam_col[10] else tam_col[10]
					tam_col[11] = tam_letra* len(line.razonsocial if line.razonsocial  else '') if tam_letra* len(line.razonsocial if line.razonsocial  else '')> tam_col[11] else tam_col[11]
					tam_col[12] = tam_letra* len("%0.2f"%line.bioge ) if tam_letra* len("%0.2f"%line.bioge )> tam_col[12] else tam_col[12]
					tam_col[13] = tam_letra* len("%0.2f"%line.biogeng ) if tam_letra* len("%0.2f"%line.biogeng )> tam_col[13] else tam_col[13]
					tam_col[14] = tam_letra* len("%0.2f"%line.biong ) if tam_letra* len("%0.2f"%line.biong )> tam_col[14] else tam_col[14]
					tam_col[15] = tam_letra* len("%0.2f"%line.cng ) if tam_letra* len("%0.2f"%line.cng )> tam_col[15] else tam_col[15]
					tam_col[16] = tam_letra* len("%0.2f"%line.isc ) if tam_letra* len("%0.2f"%line.isc )> tam_col[16] else tam_col[16]
					tam_col[17] = tam_letra* len("%0.2f"%line.igva ) if tam_letra* len("%0.2f"%line.igva )> tam_col[17] else tam_col[17]
					tam_col[18] = tam_letra* len("%0.2f"%line.igvb ) if tam_letra* len("%0.2f"%line.igvb )> tam_col[18] else tam_col[18]
					tam_col[19] = tam_letra* len("%0.2f"%line.igvc ) if tam_letra* len("%0.2f"%line.igvc )> tam_col[19] else tam_col[19]
					tam_col[20] = tam_letra* len("%0.2f"%line.otros ) if tam_letra* len("%0.2f"%line.otros )> tam_col[20] else tam_col[20]
					tam_col[21] = tam_letra* len("%0.2f"%line.total ) if tam_letra* len("%0.2f"%line.total )> tam_col[21] else tam_col[21]
					tam_col[22] = tam_letra* len(line.comprobante if line.comprobante  else '') if tam_letra* len(line.comprobante if line.comprobante  else '')> tam_col[22] else tam_col[22]
					tam_col[23] = tam_letra* len(line.moneda if  line.moneda else '') if tam_letra* len(line.moneda if  line.moneda else '')> tam_col[23] else tam_col[23]
					tam_col[24] = tam_letra* len("%0.3f"%line.tc ) if tam_letra* len("%0.3f"%line.tc )> tam_col[24] else tam_col[24]
					tam_col[25] = tam_letra* len(line.fechad if line.fechad else '') if tam_letra* len(line.fechad if line.fechad else '')> tam_col[25] else tam_col[25]
					tam_col[26] = tam_letra* len(line.numerod if line.numerod else '') if tam_letra* len(line.numerod if line.numerod else '')> tam_col[26] else tam_col[26]
					tam_col[27] = tam_letra* len(line.fechadm if line.fechadm else '') if tam_letra* len(line.fechadm if line.fechadm else '')> tam_col[27] else tam_col[27]
					tam_col[28] = tam_letra* len(line.td if line.td else '') if tam_letra* len(line.td if line.td else '')> tam_col[28] else tam_col[28]
					tam_col[29] = tam_letra* len(line.seried if line.seried else '') if tam_letra* len(line.seried if line.seried else '')> tam_col[29] else tam_col[29]
					tam_col[30] = tam_letra* len(line.numerodd if line.numerodd else '') if tam_letra* len(line.numerodd if line.numerodd else '')> tam_col[30] else tam_col[30]
					tam_col[31] = tam_letra* len(line.glosa if line.glosa else '') if tam_letra* len(line.glosa if line.glosa else '')> tam_col[31] else tam_col[31]

					x = x +1



				worksheet.write(x,11,'Totales:',bord)
				worksheet.write(x,12,totales[0] ,numberdos)
				worksheet.write(x,13,totales[1] ,numberdos)
				worksheet.write(x,14,totales[2] ,numberdos)
				worksheet.write(x,15,totales[3] ,numberdos)
				worksheet.write(x,16,totales[4] ,numberdos)
				worksheet.write(x,17,totales[5] ,numberdos)
				worksheet.write(x,18,totales[6] ,numberdos)
				worksheet.write(x,19,totales[7] ,numberdos)
				worksheet.write(x,20,totales[8] ,numberdos)
				worksheet.write(x,21,totales[9] ,numberdos)

				tam_col = [19,13,10,14,14,4,6,8,8,5,13,45,15,15,15,15,15,15,15,15,15,15,5,7,10,13,13,13,9,7,9,20]		

				worksheet.set_row(0, 31)
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
				worksheet.set_column('M:M', tam_col[12])
				worksheet.set_column('N:N', tam_col[13])
				worksheet.set_column('O:O', tam_col[14])
				worksheet.set_column('P:P', tam_col[15])
				worksheet.set_column('Q:Q', tam_col[16])
				worksheet.set_column('R:R', tam_col[17])
				worksheet.set_column('S:S', tam_col[18])
				worksheet.set_column('T:T', tam_col[19])
				worksheet.set_column('U:U', tam_col[20])
				worksheet.set_column('V:V', tam_col[21])
				worksheet.set_column('W:W', tam_col[22])
				worksheet.set_column('X:X', tam_col[23])
				worksheet.set_column('Y:Y', tam_col[24])
				worksheet.set_column('Z:Z', tam_col[25])
				worksheet.set_column('AA:AA', tam_col[26])
				worksheet.set_column('AB:AB', tam_col[27])
				worksheet.set_column('AC:AC', tam_col[28])
				worksheet.set_column('AD:AD', tam_col[29])
				worksheet.set_column('AE:AE', tam_col[30])
				worksheet.set_column('AF:AF', tam_col[31])

				workbook.close()
				
				f = open( direccion + 'tempo_librocompras.xlsx', 'rb')			
				
				vals = {
					'output_name': 'RegistroCompras.xlsx',
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




		if self.type_show == 'pdf':
			if self.simplificado:
				raise osv.except_osv('Alerta!', u"La version Simplificada cuenta con exportacion Pantalla , Csv y Excel.")

			self.reporteador()			
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			import os
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			vals = {
				'output_name': 'RegistroCompras.pdf',
				'output_file': open(str(direccion)+"a.pdf", "rb").read().encode("base64"),	
			}

			sfs_id = self.env['export.file.save'].create(vals)
			return {
				"type": "ir.actions.act_window",
				"res_model": "export.file.save",
				"views": [[False, "form"]],
				"res_id": sfs_id.id,
				"target": "new",
			}
			
	@api.multi
	def reporteador(self):		
		#CREANDO ARCHIVO PDF
		direccion = self.env['main.parameter'].search([])[0].dir_create_file	
	
		archivo_pdf = SimpleDocTemplate(str(direccion)+"a.pdf", pagesize=(2200,1000), rightMargin=30,leftMargin=30, topMargin=30,bottomMargin=18)

		elements = []
		#Estilos 
		style_title = ParagraphStyle(name = 'Center',alignment = TA_CENTER, fontSize = 40, fontName="Times-Roman" )
		style_form = ParagraphStyle(name='Justify', alignment=TA_JUSTIFY , fontSize = 24, fontName="Times-Roman" )
		style_cell = ParagraphStyle(name = 'Center',alignment = TA_CENTER, fontSize = 12, fontName="Times-Roman" )
		

		company = self.env['res.company'].search([])[0].partner_id
		texto = "Reporte de Registro de Compras"		
		elements.append(Paragraph(texto, style_title))
		elements.append(Spacer(1, 60))
		texto = 'Empresa: ' + str(company.name)
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 12))
		texto = 'Dirección: ' + str(company.street)
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 12))
		texto = 'Ruc: ' + str(company.nro_documento)
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 12))
		texto = 'Registro Compras: ' + str(self.period_ini.name) + ' - ' + self.period_end.name
		elements.append(Paragraph(texto,style_form))
		elements.append(Spacer(1, 12))
		texto = 'Fecha de Reporte: ' + str(date.today()) 
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 80))


	#Crear Tabla
		data = [[
			u'Periodo',
			u'Libro',
			u'Voucher',
			u'Fecha_Emisión',
			u'Fecha_Vencimiento',
			u'TD.',
			u'Serie',
			u'Año',
			u'Número',
			u'TDP.',
			u'RUC/DNI',
			u'Razon_Social',
			u'BIOGE',
			u'BIOGENG',
			u'BIONG',
			u'CNG',
			u'ISC',
			u'IGVA',
			u'IGVB',
			u'IGBC',
			u'Otros',
			u'Total',
			u'CSND',
			u'Moneda',
			u'TC.',
			u'Fecha_Doc.',
			u'Número_Doc',
			u'F._Doc._M.',
			u'TD_Doc.',
			u'Serie',
			u'Número',
			u'Glosa'
		]]	

		sql_query = """SELECT * FROM account_purchase_register"""
		self.env.cr.execute(sql_query)
		dicc = self.env.cr.dictfetchall()

		totales = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		for fila in dicc:
			periodo = (fila['periodo']) if fila['periodo'] else ''
			libro = (fila['libro']) if fila['libro'] else ''
			voucher = (fila['voucher']) if fila['voucher'] else ''			
			fechaemision = (fila['fechaemision']) if fila['fechaemision'] else ''
			fechavencimiento = (fila['fechavencimiento']) if fila['fechavencimiento'] else ''
			tipodocumento = (fila['tipodocumento']) if fila['tipodocumento'] else ''
			serie = (fila['serie']) if fila['serie'] else ''			
			anio = str(fila['anio']) if fila['anio'] else ''
			numero = (fila['numero']) if fila['numero'] else ''
			tdp = (fila['tdp']) if fila['tdp'] else ''
			ruc = (fila['ruc']) if fila['ruc'] else ''
			razonsocial = (fila['razonsocial']) if fila['razonsocial'] else ''
			bioge = fila['bioge'] if fila['bioge'] else 0.0
			biogeng = fila['biogeng'] if fila['biogeng'] else 0.0
			biong = fila['biong'] if fila['biong'] else 0.0
			cng = fila['cng'] if fila['cng'] else 0.0
			isc = fila['isc'] if fila['isc'] else 0.0
			igva = fila['igva'] if fila['igva'] else 0.0
			igvb = fila['igvb'] if fila['igvb'] else 0.0
			igvc = fila['igvc'] if fila['igvc'] else 0.0
			otros = fila['otros'] if fila['otros'] else 0.0
			total = fila['total'] if fila['total'] else 0.0
			comprobante = (fila['comprobante']) if fila['comprobante'] else ''
			moneda = (fila['moneda']) if fila['moneda'] else ''
			tc = str(fila['tc']) if fila['tc'] else ''
			fechad = (fila['fechad']) if fila['fechad'] else ''
			numerod = (fila['numerod']) if fila['numerod'] else ''
			fechadm = (fila['fechadm']) if fila['fechadm'] else ''
			td = (fila['td']) if fila['td'] else ''			
			seried = (fila['seried']) if fila['seried'] else ''
			numerodd = (fila['numerodd']) if fila['numerodd'] else ''
			glosa = (fila['glosa']) if fila['glosa'] else ''
	
			totales[0] += bioge
			totales[1] += biogeng
			totales[2] += biong
			totales[3] += cng
			totales[4] += isc
			totales[5] += igva
			totales[6] += igvb
			totales[7] += igvc
			totales[8] += otros
			totales[9] += total

			data.append([
				 periodo , 
				 libro , 
				 voucher , 
				 fechaemision , 
				 fechavencimiento , 
				 tipodocumento ,
				 serie ,
				 anio,
				 numero , 
				 tdp , 
				 ruc , 
				 razonsocial ,
				 str(bioge) ,
				 str(biogeng) ,
				 str(biong),
				 str(cng),
				 str(isc),
				 str(igva),
				 str(igvb),
				 str(igvc),
				 str(otros),
				 str(total) ,
				 comprobante ,
				 moneda ,
				 tc ,
				 fechad ,
				 numerod ,
				 fechadm ,
				 td ,				 
				 seried ,
				 numerodd ,
				 glosa 
				])
		data.append([
			'',
			'',
			'',
			'',
			'',
			'',
			'',
			'',
			'',
			'',
			'',
			'Totales',
			str(totales[0]),
			str(totales[1]),
			str(totales[2]),
			str(totales[3]),
			str(totales[4]),
			str(totales[5]),
			str(totales[6]),
			str(totales[7]),
			str(totales[8]),
			str(totales[9])
			])

	#Estilo de Tabla
		style = TableStyle([
			('ALIGN',(1,1),(-2,-2),'RIGHT'),					   
		   ('VALIGN',(0,0),(0,-1),'TOP'),					   
		   ('ALIGN',(0,-1),(-1,-1),'CENTER'),
		   ('VALIGN',(0,-1),(-1,-1),'MIDDLE'),					   
		   ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
		   ('BOX', (0,0), (-1,-1), 0.25, colors.black),
		])		
	#Configure style and word wrap		
		style_cell.wordWrap = 'CJK'
		data2 = [[Paragraph(cell, style_cell) for cell in row] for row in data]

		pdftable=Table(data2)
		pdftable.setStyle(style)		 
		elements.append(pdftable)


	#Build
		archivo_pdf.build(elements)
