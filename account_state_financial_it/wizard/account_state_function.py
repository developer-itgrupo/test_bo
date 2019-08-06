# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
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
from datetime import *
from odoo.exceptions import UserError, ValidationError

import base64
class account_state_function(models.Model):
	_name='account.state.function'
	_auto= False
	_order = 'orden'

	name = fields.Char('Nombre', size=50)
	grupo = fields.Char('Grupo',size=200)
	saldo = fields.Float('Saldo', digits=(12,2))
	orden = fields.Integer('Orden')




class account_state_function_wizard(osv.TransientModel):
	_name='account.state.function.wizard'

	periodo_ini = fields.Many2one('account.period','Periodo Inicio', required="1")
	periodo_fin = fields.Many2one('account.period','Periodo Fin', required="1")
	type_show =  fields.Selection([('pantalla','Pantalla'),('pdf','Pdf'),('excel','Excel')], 'Mostrar en', required=True)

	def get_fiscalyear(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		id_year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1).id
		if not id_year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			return id_year

	fiscalyear_id = fields.Many2one('account.fiscalyear','Año Fiscal',required=True,default=lambda self: self.get_fiscalyear(),readonly=True)
	save_page_states= []

	@api.model
	def get_wizard(self):
		return self.env['automatic.fiscalyear'].get_wizard('R. por Funcion',self.id,'account.state.function.wizard','account_state_financial_it.view_account_estate_function_wizard_form','default_periodo_ini','default_periodo_fin')

	@api.onchange('fiscalyear_id')
	def onchange_fiscalyear(self):
		if self.fiscalyear_id:
			return {'domain':{'periodo_ini':[('fiscalyear_id','=',self.fiscalyear_id.id )], 'periodo_fin':[('fiscalyear_id','=',self.fiscalyear_id.id )]}}
		else:
			return {'domain':{'periodo_ini':[], 'periodo_fin':[]}}



	@api.multi
	def do_rebuild(self):
		flag = 'false'

		self.env.cr.execute(""" 
			DROP VIEW IF EXISTS account_state_function;
			create or replace view account_state_function as(
					select row_number() OVER () AS id,* from ( select *,0 as saldoc from get_estado_funcion(""" + flag+ """ ,periodo_num('""" + self.periodo_ini.name+"""') ,periodo_num('""" +self.periodo_fin.name +"""' )) ) AS T
			)
			""")		

		if self.type_show == 'pantalla':
			
			return {
				'context': {'tree_view_ref':'account_state_financial_it.view_account_state_function_tree'},
				'name': 'Resultado por Función',
				'type': 'ir.actions.act_window',
				'res_model': 'account.state.function',
				'view_mode': 'tree',
				'view_type': 'form',
			}




		if self.type_show == 'excel':
			import io
			from xlsxwriter.workbook import Workbook
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			if not direccion:
				raise osv.except_osv('Alerta!', u"No fue configurado el directorio para los archivos en Configuracion.")

			workbook = Workbook(direccion +'Reporte_state_function.xlsx')
			worksheet = workbook.add_worksheet(u"Estado Función")
			bold = workbook.add_format({'bold': True})
			normal = workbook.add_format()
			boldbord = workbook.add_format({'bold': True})
			boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(9)
			boldbord.set_bg_color('#DCE6F1')
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'#,##0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)

			numbertresbold = workbook.add_format({'num_format':'0.000','bold': True})
			numberdosbold = workbook.add_format({'num_format':'#,##0.00','bold': True})
			numberdosbold.set_border(style=1)
			numbertresbold.set_border(style=1)	

			numberdoscon = workbook.add_format({'num_format':'#,##0.00'})

			boldtotal = workbook.add_format({'bold': True})
			boldtotal.set_align('right')
			boldtotal.set_align('vright')

			merge_format = workbook.add_format({
												'bold': 1,
												'border': 1,
												'align': 'center',
												'valign': 'vcenter',
												})	
			merge_format.set_bg_color('#DCE6F1')
			merge_format.set_text_wrap()
			merge_format.set_font_size(9)

			worksheet.write(1,2, self.env["res.company"].search([])[0].name.upper(), bold)
			worksheet.write(2,2, u"ESTADO DE RESULTADO POR FUNCION", bold)
			worksheet.write(3,2, u"AL "+ str(self.periodo_fin.date_stop), bold)
			worksheet.write(4,2, u"(Expresado en Nuevos Soles)", bold)
		

			colum = {
				1: "Enero",
				2: "Febrero",
				3: "Marzo",
				4: "Abril",
				5: "Mayo",
				6: "Junio",
				7: "Julio",
				8: "Agosto",
				9: "Septiembre",
				10: "Octubre",
				11: "Noviembre",
				12: "Diciembre",
			}


			#### nuevo ini
			x=6

			self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),sum(saldo) ,orden from account_state_function
				where grupo = 'F1'
				group by name,grupo,orden
				order by orden,name   """)
			listobjetosF1 =  self.env.cr.fetchall()

			worksheet.write(x,1, "INGRESOS OPERACIONALES", bold)

			#worksheet.write(x,2, self.fiscalyear_id.name, bold)

			x+=1					

			sumgrupo1 = None
			sumgrupo1N = None
			for i in listobjetosF1:

				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[3], numberdos)
				x += 1

			x+=1

			if len(listobjetosF1)>0:
				worksheet.write(x,1, "TOTAL INGRESOS BRUTOS", bold)

				self.env.cr.execute(""" select sum(saldo), sum(saldo) from account_state_function where grupo = 'F1' """)
				totalB1 = self.env.cr.fetchall()[0]
				sumgrupo1 = totalB1[0]
				sumgrupo1N = totalB1[1]

				worksheet.write(x,2, totalB1[0], numberdosbold)
				x += 1

			else:
				sumgrupo1 = 0
				sumgrupo1N = 0
				
				worksheet.write(x,1, "TOTAL INGRESOS BRUTOS", bold)

				worksheet.write(x,2, 0, numberdosbold)
				x += 1

			self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),sum(saldo),orden from account_state_function
				where grupo = 'F2'
				group by name,grupo,orden
				order by orden,name   """)
			listobjetosF2 =  self.env.cr.fetchall()

			x+=1

			sumgrupo2 = None
			sumgrupo2N = None
			for i in listobjetosF2:

				worksheet.write(x,1, i[0], bold)

				worksheet.write(x,2, i[3], numberdos)
				x += 1

			x+=1

			if len(listobjetosF2)>0:

				self.env.cr.execute(""" select sum(saldo),sum(saldo) from account_state_function where grupo = 'F2' """)
				totalB1 = self.env.cr.fetchall()[0]
				sumgrupo2 = totalB1[0]
				sumgrupo2N = totalB1[1]


				worksheet.write(x,1, "TOTAL COSTOS OPERACIONALES", bold)

				worksheet.write(x,2, totalB1[0], numberdosbold)
				x += 1

			else:
				sumgrupo2 = 0
				sumgrupo2N = 0


				worksheet.write(x,1, "TOTAL COSTOS OPERACIONALES", bold)

				worksheet.write(x,2, 0, numberdosbold)
				x += 1

			x+=1

			worksheet.write(x,1, "UTILIDAD BRUTA", bold)

			worksheet.write(x,2, sumgrupo1 + sumgrupo2, numberdosbold)
			x += 1

			self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),sum(saldo),orden from account_state_function
				where grupo = 'F3'
				group by name,grupo,orden
				order by orden,name   """)
			listobjetosF3 =  self.env.cr.fetchall()

			for i in listobjetosF3:

				worksheet.write(x,1, i[0], bold)

				worksheet.write(x,2, i[3], numberdos)
				x += 1

			totalF3 = sumgrupo1 + sumgrupo2
			totalF3N = sumgrupo1N + sumgrupo2N
			if len(listobjetosF3)>0:
				self.env.cr.execute(""" select sum(saldo),sum(saldo) from account_state_function where grupo = 'F3' """)
				totalB1 = self.env.cr.fetchall()[0]
				totalF3 += totalB1[0]
				totalF3N += totalB1[1]

			x+=1


			worksheet.write(x,1, "UTILIDAD OPERATIVA", bold)

			worksheet.write(x,2, totalF3, numberdosbold)
			x += 1


			self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),sum(saldo),orden from account_state_function
				where grupo = 'F4'
				group by name,grupo,orden
				order by orden,name   """)
			listobjetosF4 =  self.env.cr.fetchall()

			for i in listobjetosF4:

				worksheet.write(x,1, i[0], bold)

				worksheet.write(x,2, i[3], numberdos)
				x += 1


			totalF4 = totalF3
			totalF4N = totalF3N
			if len(listobjetosF4)>0:
				self.env.cr.execute(""" select sum(saldo),sum(saldo) from account_state_function where grupo = 'F4' """)
				totalB1 = self.env.cr.fetchall()[0]
				totalF4 += totalB1[0]
				totalF4N += totalB1[1]

			x+=1
			worksheet.write(x,1, "RESULTADO ANTES DE PARTICIPACIONES E IMPUESTOS", bold)

			worksheet.write(x,2, totalF4, numberdosbold)
			x += 1


			self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),sum(saldo),orden from account_state_function
				where grupo = 'F5'
				group by name,grupo,orden
				order by orden,name   """)
			listobjetosF5 =  self.env.cr.fetchall()

			for i in listobjetosF5:
				worksheet.write(x,1, i[0], bold)

				worksheet.write(x,2, i[3], numberdos)
				x += 1


			totalF5 = totalF4
			totalF5N = totalF4N
			if len(listobjetosF5)>0:
				self.env.cr.execute(""" select sum(saldo),sum(saldo) from account_state_function where grupo = 'F5' """)
				totalB1 = self.env.cr.fetchall()[0]
				totalF5 += totalB1[0]
				totalF5N += totalB1[1]



			x+=1
			worksheet.write(x,1, "UTILIDAD(PERDIDA) NETA ACT DISCONTINUAS", bold)

			worksheet.write(x,2, totalF5, numberdosbold)
			x += 1


			self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),sum(saldo),orden from account_state_function
				where grupo = 'F6'
				group by name,grupo,orden
				order by orden,name   """)
			listobjetosF6 =  self.env.cr.fetchall()

			for i in listobjetosF6:
				worksheet.write(x,1, i[0], bold)

				worksheet.write(x,2, i[3], numberdos)
				x += 1

			totalF6 = totalF5
			totalF6N = totalF5N
			if len(listobjetosF6)>0:
				self.env.cr.execute(""" select sum(saldo),sum(saldo) from account_state_function where grupo = 'F6' """)
				totalB1 = self.env.cr.fetchall()[0]
				totalF6 += totalB1[0]
				totalF6N += totalB1[1]



			x+=1

			worksheet.write(x,1, "UTILIDAD(PERDIDA) NETA DEL EJERCICIO", bold)

			worksheet.write(x,2, totalF6, numberdosbold)
			x += 1


			worksheet.set_column('B:B',57)
			worksheet.set_column('C:C',24)
			#### FIN

			workbook.close()
			
			f = open(direccion + 'Reporte_state_function.xlsx', 'rb')
			
			vals = {
				'output_name': 'EstadoFuncion.xlsx',
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
			self.reporteador()
			
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			import os
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			vals = {
				'output_name': 'Estado de Resultados.pdf',
				'output_file': open(direccion + "a.pdf", "rb").read().encode("base64"),	
			}
			sfs_id = self.env['export.file.save'].create(vals)
			#result = {}
			#view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
			#view_id = view_ref and view_ref[1] or False
			#result = act_obj.read( [view_id] )			
			return {
				"type": "ir.actions.act_window",
				"res_model": "export.file.save",
				"views": [[False, "form"]],
				"res_id": sfs_id.id,
				"target": "new",
			}

	@api.multi
	def cabezera(self,c,wReal,hReal):

		c.setFont("Times-Bold", 12)
		c.setFillColor(black)
		c.drawCentredString((wReal/2)+20,hReal, self.env["res.company"].search([])[0].name.upper())
		c.drawCentredString((wReal/2)+20,hReal-12, "ESTADO DE RESULTADOS")
		c.drawCentredString((wReal/2)+20,hReal-24, "al "+ str(self.periodo_fin.date_stop))
		c.drawCentredString((wReal/2)+20,hReal-36, "(Expresado en Nuevos Soles)")

	@api.multi
	def reporteador(self):

		import sys
		nivel_left_page = 1
		nivel_left_fila = 0
		
		nivel_right_page = 1
		nivel_right_fila = 0

		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		width , height = A4  # 595 , 842
		wReal = width- 30
		hReal = height - 40

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas( direccion + "a.pdf", pagesize=A4)
		inicio = 0
		pos_inicial = hReal-60

		pagina = 1
		textPos = 0
		
		tamanios = {}
		voucherTamanio = None
		contTamanio = 0

		self.cabezera(c,wReal,hReal)
		c.setFont("Times-Bold", 10)
		c.drawCentredString(300,25,'Pág. ' + str(pagina))


		self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),orden from account_state_function
			where grupo = 'F1'
			group by name,grupo,orden
			order by orden,name   """)
		listobjetosF1 =  self.env.cr.fetchall()

		c.setFont("Times-Bold", 10)
		c.drawString( 85 , pos_inicial, "INGRESOS OPERACIONALES")

		sumgrupo1 = None
		for i in listobjetosF1:
			c.setFont("Times-Roman", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,16,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])

		if len(listobjetosF1)>0:
			c.setFont("Times-Bold", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.drawString(85,pos_inicial,"TOTAL INGRESOS BRUTOS")

			self.env.cr.execute(""" select sum(saldo) from account_state_function where grupo = 'F1' """)
			totalB1 = self.env.cr.fetchall()[0]
			sumgrupo1 = totalB1[0]
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %totalB1[0])
			c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
			c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)
		else:
			sumgrupo1 = 0
			c.setFont("Times-Bold", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.drawString(85,pos_inicial,"TOTAL INGRESOS BRUTOS")
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %(0.0) )
			c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
			c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)

		self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),orden from account_state_function
			where grupo = 'F2'
			group by name,grupo,orden
			order by orden,name   """)
		listobjetosF2 =  self.env.cr.fetchall()

		sumgrupo2 = None
		for i in listobjetosF2:
			c.setFont("Times-Roman", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,16,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])

		if len(listobjetosF2)>0:
			c.setFont("Times-Bold", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.drawString(85,pos_inicial,"TOTAL COSTOS OPERACIONALES")

			self.env.cr.execute(""" select sum(saldo) from account_state_function where grupo = 'F2' """)
			totalB1 = self.env.cr.fetchall()[0]
			sumgrupo2 = totalB1[0]
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %totalB1[0])
			c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
			c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)
		else:
			sumgrupo2 = 0
			c.setFont("Times-Bold", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.drawString(85,pos_inicial,"TOTAL COSTOS OPERACIONALES")
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %(0.0) )
			c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
			c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)

		c.setFont("Times-Bold", 10)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
		c.drawString( 85 , pos_inicial, "UTILIDAD BRUTA")
		c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %( sumgrupo1 + sumgrupo2 ) )
		c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
		c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)


		self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),orden from account_state_function
			where grupo = 'F3'
			group by name,grupo,orden
			order by orden,name   """)
		listobjetosF3 =  self.env.cr.fetchall()

		for i in listobjetosF3:
			c.setFont("Times-Roman", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,16,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])

		totalF3 = sumgrupo1+ sumgrupo2
		if len(listobjetosF3)>0:
			self.env.cr.execute(""" select sum(saldo) from account_state_function where grupo = 'F3' """)
			totalB1 = self.env.cr.fetchall()[0]
			totalF3 += totalB1[0]

		c.setFont("Times-Bold", 10)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
		c.drawString( 85 , pos_inicial, "UTILIDAD OPERATIVA")
		c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %( totalF3 ) )
		c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
		c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)


		self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),orden from account_state_function
			where grupo = 'F4'
			group by name,grupo,orden
			order by orden,name   """)
		listobjetosF4 =  self.env.cr.fetchall()

		for i in listobjetosF4:
			c.setFont("Times-Roman", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,16,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])

		totalF4 = totalF3
		if len(listobjetosF4)>0:
			self.env.cr.execute(""" select sum(saldo) from account_state_function where grupo = 'F4' """)
			totalB1 = self.env.cr.fetchall()[0]
			totalF4 += totalB1[0]

		c.setFont("Times-Bold", 10)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
		c.drawString( 85 , pos_inicial, "RESULTADO ANTES DE PARTICIPACIONES E IMPUESTOS")
		c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %( totalF4 ) )
		c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
		c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)



		self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),orden from account_state_function
			where grupo = 'F5'
			group by name,grupo,orden
			order by orden,name   """)
		listobjetosF5 =  self.env.cr.fetchall()

		for i in listobjetosF5:
			c.setFont("Times-Roman", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,16,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])

		totalF5 = totalF4
		if len(listobjetosF5)>0:
			self.env.cr.execute(""" select sum(saldo) from account_state_function where grupo = 'F5' """)
			totalB1 = self.env.cr.fetchall()[0]
			totalF5 += totalB1[0]

		c.setFont("Times-Bold", 10)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
		c.drawString( 85 , pos_inicial, "UTILIDAD(PERDIDA) NETA ACT DISCONTINUAS")
		c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %( totalF5 ) )
		c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
		c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)



		self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),orden from account_state_function
			where grupo = 'F6'
			group by name,grupo,orden
			order by orden,name   """)
		listobjetosF6 =  self.env.cr.fetchall()

		for i in listobjetosF6:
			c.setFont("Times-Roman", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,16,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])

		totalF6 = totalF5
		if len(listobjetosF6)>0:
			self.env.cr.execute(""" select sum(saldo) from account_state_function where grupo = 'F6' """)
			totalB1 = self.env.cr.fetchall()[0]
			totalF6 += totalB1[0]

		c.setFont("Times-Bold", 10)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
		c.drawString( 85 , pos_inicial, "UTILIDAD(PERDIDA) NETA DEL EJERCICIO")
		c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %( totalF6 ) )
		c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
		c.line((wReal-75)-75, pos_inicial-4, (wReal-75)-20 ,pos_inicial-4)
		c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)

		self.finalizar(c)

	@api.multi
	def particionar_text(self,c):
		tet = ""
		for i in range(len(c)):
			tet += c[i]
			lines = simpleSplit(tet,'Times-Roman',8,95)
			if len(lines)>1:
				return tet[:-1]
		return tet

	@api.multi
	def cargar_pagina(self,c,pagina):
		c.__dict__.update(self.save_page_states[pagina-1])

	@api.multi
	def finalizar(self,c):
		for state in self.save_page_states:
			c.__dict__.update(state)
			canvas.Canvas.showPage(c)
		canvas.Canvas.save(c)

	@api.multi
	def guardar_state(self,c):
		if c._pageNumber > len(self.save_page_states):
			self.save_page_states.append(dict(c.__dict__))
		else:
			self.save_page_states[c._pageNumber-1] = dict(c.__dict__)
		return True

	@api.multi
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina):
		if posactual <40:
			if c._pageNumber > len(self.save_page_states):
				self.save_page_states.append(dict(c.__dict__))
			else:
				self.save_page_states[c._pageNumber-1] = dict(c.__dict__)
			c._startPage()
			self.cabezera(c,wReal,hReal)

			c.setFont("Times-Bold", 10)
			c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-60
		else:
			return pagina,posactual-valor



		


