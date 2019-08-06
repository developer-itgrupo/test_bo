# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api  , exceptions , _
from datetime import datetime, date, time, timedelta
import codecs
import pprint

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

class account_sale_register_report_wizard(osv.TransientModel):
	_name='account.sale.register.report.wizard'
	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end = fields.Many2one('account.period','Periodo Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('pdf','PDF'),('csv','CSV')], 'Mostrar en', required=True)
	simplificado = fields.Boolean('Registro Simplificado',default=True)

	@api.model
	def get_wizard(self):
		return self.env['automatic.fiscalyear'].get_wizard('Registro de Ventas',self.id,'account.sale.register.report.wizard','account_registro_venta_it.view_account_sale_register_report_wizard_form','default_period_ini','default_period_end')

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

	@api.multi
	def do_rebuild(self):
		period_ini = self.period_ini
		period_end = self.period_end
		
		filtro = []	
				
		self.env.cr.execute("""
			CREATE OR REPLACE view account_sale_register as (
				SELECT * 
				FROM get_venta_1_1_1(periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""')) order by periodo, libro, voucher
		)""")

		#DSC_Exportar a CSV por el numero de filas
		self.env.cr.execute("""select count(*)  from account_sale_register""")
		rows = self.env.cr.fetchone()
		#if self.type_show == 'excel' and rows[0] > 1000:
		#	self.type_show = 'csv'


		if self.type_show == 'pantalla':
			view_id = self.env.ref('account_registro_venta_it.view_move_sale_register_tree',False)
			if self.simplificado:
				view_id = self.env.ref('account_registro_venta_it.view_move_sale_register_tree_simplificado',False)
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.sale.register',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(view_id.id, 'tree')],
			}

		#DSC_
		if self.type_show == 'csv':
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			docname = 'RegistroVentas.csv'
			#CSV
			sql_query = """	COPY (SELECT * FROM account_sale_register )TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
							"""

			if self.simplificado:
				sql_query = """	COPY (select voucher,fechaemision,fechavencimiento,tipodocumento,serie,numero,tipodoc as td,numdoc as numero, partner as cliente,glosa as concepto, coalesce(valorexp,0)+ coalesce(inafecto,0)+ coalesce(exonerado,0)+ coalesce(otros ,0) as nogravado, isc, baseimp as baseimponible, igv as igv, total, tipodocmod,seriemod,numeromod,fechadm,fechad,numeromodd,tipodecambio FROM account_sale_register )TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
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
				pass


				import io
				from xlsxwriter.workbook import Workbook
				output = io.BytesIO()
				########### PRIMERA HOJA DE LA DATA EN TABLA
				#workbook = Workbook(output, {'in_memory': True})
				direccion = self.env['main.parameter'].search([])[0].dir_create_file
				workbook = Workbook( direccion + 'tempo_libroventas.xlsx')
				worksheet = workbook.add_worksheet("Registro Ventas")
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
				tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
				tam_letra = 1.2
				import sys
				reload(sys)
				sys.setdefaultencoding('iso-8859-1')				

				worksheet.merge_range(0,0,0,23,"REGISTRO DE VENTA",title)			
				company = self.env['res.company'].search([])[0].partner_id			
				worksheet.write(1,0, "Empresa:".upper(),bold)
				worksheet.write(1,1, company.name.upper(), bold)
				
				worksheet.write(2,0, "RUC:",bold)
				worksheet.write(2,1, company.nro_documento, bold)
				
				worksheet.write(3,0, u"Dirección:".upper(),bold)
				worksheet.write(3,1, company.street.upper() if company.street else '', bold)
				
				worksheet.write(4,0, "Registro Ventas:".upper(), bold)
				tam_col[0] = tam_letra* len("Registro Ventas:") if tam_letra* len("Registro Ventas:")> tam_col[0] else tam_col[0]

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
				

				worksheet.write(7,0, "Voucher",boldbord)
				worksheet.write(7,1, u"Fecha Emisión",boldbord)
				worksheet.write(7,2, u"Fecha Vencimiento",boldbord)
				worksheet.write(7,3, "TD.",boldbord)
				worksheet.write(7,4, "Serie",boldbord)
				worksheet.write(7,5, u"Número",boldbord)
				worksheet.write(7,6, "TDP.",boldbord)
				worksheet.write(7,7, "RUC/DNI",boldbord)
				worksheet.write(7,8, u"Cliente",boldbord)
				worksheet.write(7,9, u"Concepto",boldbord)
				worksheet.write(7,10, u"No Gravado",boldbord)
				worksheet.write(7,11, "ISC",boldbord)
				worksheet.write(7,12, "Base Imponible",boldbord)
				worksheet.write(7,13, u"IGV",boldbord)
				worksheet.write(7,14, u"Total",boldbord)
				worksheet.write(7,15, u"TD Doc.",boldbord)
				worksheet.write(7,16, u"Serie",boldbord)
				worksheet.write(7,17, u"Número",boldbord)
				worksheet.write(7,18, u"F. Doc. M.",boldbord)
				worksheet.write(7,19, u"Fecha Doc.",boldbord)
				worksheet.write(7,20, u"Número Doc",boldbord)
				worksheet.write(7,21, u"TC.",boldbord)
				

				
				totales = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
				for line in self.env['account.sale.register'].search([]):
					worksheet.write(x,0,line.voucher if line.voucher  else '',bord)
					worksheet.write(x,1,line.fechaemision if line.fechaemision else '',bord)
					worksheet.write(x,2,line.fechavencimiento if line.fechavencimiento else '',bord)
					worksheet.write(x,3,line.tipodocumento if line.tipodocumento else '',bord)
					worksheet.write(x,4,line.serie if line.serie else '',bord)
					worksheet.write(x,5,line.numero if line.numero  else '',bord)
					worksheet.write(x,6,line.tipodoc if line.tipodoc  else '',bord)
					worksheet.write(x,7,line.numdoc if line.numdoc  else '',bord)
					worksheet.write(x,8,line.partner.upper() if line.partner  else '',bord)
					worksheet.write(x,9,line.glosa if line.glosa else '',bord)
					worksheet.write(x,10,line.nogravado ,numberdos)
					worksheet.write(x,11,line.isc ,numberdos)
					worksheet.write(x,12,line.baseimp ,numberdos)
					worksheet.write(x,13,line.igv ,numberdos)
					worksheet.write(x,14,line.total ,numberdos)
					worksheet.write(x,15,line.tipodocmod if line.tipodocmod else '',bord)
					worksheet.write(x,16,line.seriemod if line.seriemod else '',bord)
					worksheet.write(x,17,line.numeromod if line.numeromod else '',bord)
					worksheet.write(x,18,line.fechadm if line.fechadm else '',bord)
					worksheet.write(x,19,line.fechad if line.fechad else '',bord)
					worksheet.write(x,20,line.numeromodd if line.numeromodd else '',bord)
					worksheet.write(x,21,line.tipodecambio ,numbertres)
					

					totales[0] += line.nogravado
					totales[1] += line.isc
					totales[2] += line.baseimp
					totales[3] += line.igv
					totales[4] += line.total
						
									
					x = x +1




				worksheet.write(x,9, 'Totales:',bord)
				worksheet.write(x,10, totales[0] ,numberdos)
				worksheet.write(x,11, totales[1] ,numberdos)
				worksheet.write(x,12, totales[2] ,numberdos)
				worksheet.write(x,13, totales[3] ,numberdos)
				worksheet.write(x,14, totales[4] ,numberdos)


				tam_col = [18,12,12,6,12,15,6,10,45,20,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15]
				worksheet.set_row(0, 30)
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
				worksheet.set_column('X:X', tam_col[24])

				workbook.close()
				
				f = open(direccion + 'tempo_libroventas.xlsx', 'rb')

				
				
				sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
				vals = {
					'output_name': 'RegistroVentas.xlsx',
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
				workbook = Workbook( direccion + 'tempo_libroventas.xlsx')
				worksheet = workbook.add_worksheet("Registro Ventas")
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
				tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
				tam_letra = 1.2
				import sys
				reload(sys)
				sys.setdefaultencoding('iso-8859-1')				

				worksheet.merge_range(0,0,0,23,"REGISTRO DE VENTA",title)			
				company = self.env['res.company'].search([])[0].partner_id			
				worksheet.write(1,0, "Empresa:".upper(),bold)
				worksheet.write(1,1, company.name.upper(), bold)
				
				worksheet.write(2,0, "RUC:",bold)
				worksheet.write(2,1, company.nro_documento, bold)
				
				worksheet.write(3,0, u"Dirección:".upper(),bold)
				worksheet.write(3,1, company.street.upper() if company.street else '', bold)
				
				worksheet.write(4,0, "Registro Ventas:".upper(), bold)
				tam_col[0] = tam_letra* len("Registro Ventas:") if tam_letra* len("Registro Ventas:")> tam_col[0] else tam_col[0]

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
				worksheet.write(7,1, "Libro",boldbord)
				worksheet.write(7,2, "Voucher",boldbord)
				worksheet.write(7,3, u"Fecha Emisión",boldbord)
				worksheet.write(7,4, u"Fecha Vencimiento",boldbord)
				worksheet.write(7,5, "TD.",boldbord)
				worksheet.write(7,6, "Serie",boldbord)
				worksheet.write(7,7, u"Número",boldbord)
				worksheet.write(7,8, "TDP.",boldbord)
				worksheet.write(7,9, "RUC/DNI",boldbord)
				worksheet.write(7,10, u"Razon Social",boldbord)
				worksheet.write(7,11, u"Valor Exp.",boldbord)
				worksheet.write(7,12, u"Base Imp.",boldbord)
				worksheet.write(7,13, "Inafecto",boldbord)
				worksheet.write(7,14, "Exonerado",boldbord)
				worksheet.write(7,15, u"ISC",boldbord)
				worksheet.write(7,16, u"IGV",boldbord)
				worksheet.write(7,17, u"Otros",boldbord)
				worksheet.write(7,18, u"Total",boldbord)
				worksheet.write(7,19, u"Divisa",boldbord)
				worksheet.write(7,20, u"TC.",boldbord)
				worksheet.write(7,21, u"TD Doc.",boldbord)
				worksheet.write(7,22, u"Serie",boldbord)
				worksheet.write(7,23, u"Número",boldbord)
				worksheet.write(7,24, u"Glosa",boldbord)
				
				totales = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
				for line in self.env['account.sale.register'].search([]):
					worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
					worksheet.write(x,1,line.libro if line.libro  else '',bord )
					worksheet.write(x,2,line.voucher if line.voucher  else '',bord)
					worksheet.write(x,3,line.fechaemision if line.fechaemision else '',bord)
					worksheet.write(x,4,line.fechavencimiento if line.fechavencimiento else '',bord)
					worksheet.write(x,5,line.tipodocumento if line.tipodocumento else '',bord)
					worksheet.write(x,6,line.serie if line.serie else '',bord)
					worksheet.write(x,7,line.numero if line.numero  else '',bord)
					worksheet.write(x,8,line.tipodoc if line.tipodoc  else '',bord)
					worksheet.write(x,9,line.numdoc if line.numdoc  else '',bord)
					worksheet.write(x,10,line.partner.upper() if line.partner  else '',bord)
					worksheet.write(x,11,line.valorexp ,numberdos)
					worksheet.write(x,12,line.baseimp ,numberdos)
					worksheet.write(x,13,line.inafecto ,numberdos)
					worksheet.write(x,14,line.exonerado ,numberdos)
					worksheet.write(x,15,line.isc ,numberdos)
					worksheet.write(x,16,line.igv ,numberdos)
					worksheet.write(x,17,line.otros ,numberdos)
					worksheet.write(x,18,line.total ,numberdos)
					worksheet.write(x,19,line.divisa if  line.divisa else '',bord)
					worksheet.write(x,20,line.tipodecambio ,numbertres)
					worksheet.write(x,21,line.tipodocmod if line.tipodocmod else '',bord)
					worksheet.write(x,22,line.seriemod if line.seriemod else '',bord)
					worksheet.write(x,23,line.numeromod if line.numeromod else '',bord)
					worksheet.write(x,24,line.glosa if line.glosa else '',bord)

					totales[0] += line.valorexp
					totales[1] += line.baseimp
					totales[2] += line.inafecto
					totales[3] += line.exonerado
					totales[4] += line.isc
					totales[5] += line.igv
					totales[6] += line.otros
					totales[7] += line.total
						
					tam_col[0] = tam_letra* len(line.periodo if line.periodo else '' ) if tam_letra* len(line.periodo if line.periodo else '' )> tam_col[0] else tam_col[0]
					tam_col[1] = tam_letra* len(line.libro if line.libro  else '') if tam_letra* len(line.libro if line.libro  else '')> tam_col[1] else tam_col[1]
					tam_col[2] = tam_letra* len(line.voucher if line.voucher  else '') if tam_letra* len(line.voucher if line.voucher  else '')> tam_col[2] else tam_col[2]
					tam_col[3] = tam_letra* len(line.fechaemision if line.fechaemision else '') if tam_letra* len(line.fechaemision if line.fechaemision else '')> tam_col[3] else tam_col[3]
					tam_col[4] = tam_letra* len(line.fechavencimiento if line.fechavencimiento else '') if tam_letra* len(line.fechavencimiento if line.fechavencimiento else '')> tam_col[4] else tam_col[4]
					tam_col[5] = tam_letra* len(line.tipodocumento if line.tipodocumento else '') if tam_letra* len(line.tipodocumento if line.tipodocumento else '')> tam_col[5] else tam_col[5]
					tam_col[6] = tam_letra* len(line.serie if line.serie else '') if tam_letra* len(line.serie if line.serie else '')> tam_col[6] else tam_col[6]
					tam_col[7] = tam_letra* len(line.numero if line.numero  else '') if tam_letra* len(line.numero if line.numero  else '')> tam_col[7] else tam_col[7]
					tam_col[8] = tam_letra* len(line.tipodoc if line.tipodoc  else '') if tam_letra* len(line.tipodoc if line.tipodoc  else '')> tam_col[8] else tam_col[8]
					tam_col[9] = tam_letra* len(line.numdoc if line.numdoc  else '') if tam_letra* len(line.numdoc if line.numdoc  else '')> tam_col[9] else tam_col[9]
					tam_col[10] = tam_letra* len(line.partner if line.partner  else '') if tam_letra* len(line.partner if line.partner  else '')> tam_col[10] else tam_col[10]
					tam_col[11] = tam_letra* len("%0.2f"%line.valorexp ) if tam_letra* len("%0.2f"%line.valorexp )> tam_col[11] else tam_col[11]
					tam_col[12] = tam_letra* len("%0.2f"%line.baseimp ) if tam_letra* len("%0.2f"%line.baseimp )> tam_col[12] else tam_col[12]
					tam_col[13] = tam_letra* len("%0.2f"%line.inafecto ) if tam_letra* len("%0.2f"%line.inafecto )> tam_col[13] else tam_col[13]
					tam_col[14] = tam_letra* len("%0.2f"%line.exonerado ) if tam_letra* len("%0.2f"%line.exonerado )> tam_col[14] else tam_col[14]
					tam_col[15] = tam_letra* len("%0.2f"%line.isc ) if tam_letra* len("%0.2f"%line.isc )> tam_col[15] else tam_col[15]
					tam_col[16] = tam_letra* len("%0.2f"%line.igv ) if tam_letra* len("%0.2f"%line.igv )> tam_col[16] else tam_col[16]
					tam_col[17] = tam_letra* len("%0.2f"%line.otros ) if tam_letra* len("%0.2f"%line.otros )> tam_col[17] else tam_col[17]
					tam_col[18] = tam_letra* len("%0.2f"%line.total ) if tam_letra* len("%0.2f"%line.total )> tam_col[18] else tam_col[18]
					tam_col[19] = tam_letra* len(line.divisa if  line.divisa else '') if tam_letra* len(line.divisa if  line.divisa else '')> tam_col[19] else tam_col[19]
					tam_col[20] = tam_letra* len("%0.3f"%line.tipodecambio ) if tam_letra* len("%0.3f"%line.tipodecambio )> tam_col[20] else tam_col[20]
					tam_col[21] = tam_letra* len(line.tipodocmod if line.tipodocmod else '') if tam_letra* len(line.tipodocmod if line.tipodocmod else '')> tam_col[21] else tam_col[21]
					tam_col[22] = tam_letra* len(line.seriemod if line.seriemod else '') if tam_letra* len(line.seriemod if line.seriemod else '')> tam_col[22] else tam_col[22]
					tam_col[23] = tam_letra* len(line.numeromod if line.numeromod else '') if tam_letra* len(line.numeromod if line.numeromod else '')> tam_col[23] else tam_col[23]
					tam_col[24] = tam_letra* len(line.glosa if line.glosa else '') if tam_letra* len(line.glosa if line.glosa else '')> tam_col[24] else tam_col[24]
									
					x = x +1




				worksheet.write(x,10, 'Totales:',bord)
				worksheet.write(x,11, totales[0] ,numberdos)
				worksheet.write(x,12, totales[1] ,numberdos)
				worksheet.write(x,13, totales[2] ,numberdos)
				worksheet.write(x,14, totales[3] ,numberdos)
				worksheet.write(x,15, totales[4] ,numberdos)
				worksheet.write(x,16, totales[5] ,numberdos)
				worksheet.write(x,17, totales[6] ,numberdos)
				worksheet.write(x,18, totales[7] ,numberdos)


				tam_col = [18,13,10,14,14,4,6,8,5,13,45,15,15,15,15,15,15,15,15,6,8,10,8,9,20,15,15,15,15,15,15,6,8,10,8,9,20]
				worksheet.set_row(0, 30)
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
				worksheet.set_column('X:X', tam_col[24])

				workbook.close()
				
				f = open(direccion + 'tempo_libroventas.xlsx', 'rb')

				
				
				sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
				vals = {
					'output_name': 'RegistroVentas.xlsx',
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
				'output_name': 'RegistroVentas.pdf',
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
		texto = "Reporte de Registro de Ventas"		
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
		texto = 'Registro Ventas: ' + str(self.period_ini.name) + ' - ' + self.period_end.name
		elements.append(Paragraph(texto,style_form))
		elements.append(Spacer(1, 12))
		texto = 'Fecha de Reporte: ' + str(date.today()) 
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 80))


	#Crear Tabla
		data = [[
			'Periodo',
			'Libro',
			'Voucher',
			'Fecha_Emisión',
			'Fecha_Vencimiento',
			'TD.',
			'Serie',			
			'Número',
			'TDP.',
			'RUC/DNI',
			'Razon_Social',
			'Valor_Exp.',
			'Base_Imp.',
			'Inafecto',
			'Exonerado',
			'ISC',			
			'IGV',
			'Otros',
			'Total',
			'Divisa',			
			'TC.',
			'TD Doc.',
			'Serie',
			'Número',
			'Glosa'
		]]	

		sql_query = """SELECT * FROM account_sale_register"""
		self.env.cr.execute(sql_query)
		dicc = self.env.cr.dictfetchall()

		totales = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		for fila in dicc:
			periodo = str(fila['periodo']) if fila['periodo'] else ''
			libro = str(fila['libro']) if fila['libro'] else ''
			voucher = str(fila['voucher']) if fila['voucher'] else ''			
			fechaemision = str(fila['fechaemision']) if fila['fechaemision'] else ''
			fechavencimiento = str(fila['fechavencimiento']) if fila['fechavencimiento'] else ''

			tipodocumento = str(fila['tipodocumento']) if fila['tipodocumento'] else ''
			serie = str(fila['serie']) if fila['serie'] else ''						
			numero = str(fila['numero']) if fila['numero'] else ''
			tipodoc = str(fila['tipodoc']) if fila['tipodoc'] else ''
			numdoc = str(fila['numdoc']) if fila['numdoc'] else ''
			partner = str(fila['partner']) if fila['partner'] else ''
			valorexp = fila['valorexp'] if fila['valorexp'] else 0
			baseimp = fila['baseimp'] if fila['baseimp'] else 0
			inafecto = fila['inafecto'] if fila['inafecto'] else 0
			
			exonerado = fila['exonerado'] if fila['exonerado'] else 0
			isc = fila['isc'] if fila['isc'] else 0
			igv = fila['igv'] if fila['igv'] else 0
			otros = fila['otros'] if fila['otros'] else 0
			total = fila['total'] if fila['total'] else 0
			divisa = str(fila['divisa']) if fila['divisa'] else ''
			tipodecambio = str(fila['tipodecambio']) if fila['tipodecambio'] else ''
			tipodocmod = str(fila['tipodocmod']) if fila['tipodocmod'] else ''
			seriemod = str(fila['seriemod']) if fila['seriemod'] else ''			
			numeromod = str(fila['numeromod']) if fila['numeromod'] else ''
			glosa = str(fila['glosa']) if fila['glosa'] else ''

			totales[0] += valorexp
			totales[1] += baseimp
			totales[2] += inafecto
			totales[3] += exonerado
			totales[4] += isc
			totales[5] += igv
			totales[6] += otros
			totales[7] += total
 
			data.append([
					periodo ,
					libro ,
					voucher,
					fechaemision,
					fechavencimiento ,
					tipodocumento ,
					serie ,
					numero ,
					tipodoc ,
					numdoc ,
					partner ,
					str(valorexp) ,
					str(baseimp) ,
					str(inafecto) ,
					str(exonerado) ,
					str(isc),
					str(igv) ,
					str(otros) ,
					str(total) ,
					divisa ,
					tipodecambio ,
					tipodocmod,
					seriemod ,
					numeromod ,
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
			'Totales',
			str(totales[0]),
			str(totales[1]),
			str(totales[2]),
			str(totales[3]),
			str(totales[4]),
			str(totales[5]),
			str(totales[6]),
			str(totales[7]),			
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