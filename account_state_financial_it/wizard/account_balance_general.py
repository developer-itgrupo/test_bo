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
class account_balance_general(models.Model):
	_name='account.balance.general'
	_auto= False
	_order = 'orden'
	
	name = fields.Char('Nombre', size=50)
	grupo = fields.Char('Grupo',size=200)
	saldo = fields.Float('Saldo', digits=(12,2))
	orden = fields.Integer('Orden')
	saldoc = fields.Float('Saldo C', digits=(12,2) )



class account_balance_general_wizard(osv.TransientModel):
	_name='account.balance.general.wizard'

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
		return self.env['automatic.fiscalyear'].get_wizard('Situacion Financiera',self.id,'account.balance.general.wizard','account_state_financial_it.view_account_balance_general_wizard_form','default_periodo_ini','default_periodo_fin')

	@api.onchange('fiscalyear_id')
	def onchange_fiscalyear(self):
		if self.fiscalyear_id:
			return {'domain':{'periodo_ini':[('fiscalyear_id','=',self.fiscalyear_id.id )], 'periodo_fin':[('fiscalyear_id','=',self.fiscalyear_id.id )]}}
		else:
			return {'domain':{'periodo_ini':[], 'periodo_fin':[]}}


	@api.multi
	def do_rebuild(self):
		self.save_page_states= []
		flag = 'false'

		self.env.cr.execute(""" 
			DROP VIEW IF EXISTS account_balance_general;
			create or replace view account_balance_general as(
					select row_number() OVER () AS id,* from ( select *,0 as saldoc from get_balance_general(""" + flag+ """ ,periodo_num('""" + self.periodo_ini.name+"""') ,periodo_num('""" +self.periodo_fin.name +"""' )) ) AS T
			)
			""")		

		if self.type_show == "pantalla":
			
			return {
				'context': {'tree_view_ref':'account_state_financial_it.view_account_balance_general_tree'},
				'name': 'Situación Financiera',
				'type': 'ir.actions.act_window',
				'res_model': 'account.balance.general',
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

			workbook = Workbook(direccion +'Reporte_Balance_general.xlsx')
			worksheet = workbook.add_worksheet(u"Balance General")
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


			numbertresbold = workbook.add_format({'num_format':'0.000','bold':True})
			numberdosbold = workbook.add_format({'num_format':'#,##0.00','bold':True})
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
			worksheet.write(2,2, u"ESTADO DE SITUACIÓN FINANCIERA", bold)
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


			###  B1
			self.env.cr.execute(""" select name as code,'' as concept,sum(saldo) from account_balance_general
				where grupo = 'B1'
				group by name ,grupo,orden
				order by orden,name """)
			listobjetosB1 =  self.env.cr.fetchall()

			
			worksheet.write(6,1, 'ACTIVO' , bold)
			#worksheet.write(6,2, self.fiscalyear_id.name , bold)

			worksheet.write(7,1, 'ACTIVO CORRIENTE' , bold)

			x=9
			for i in listobjetosB1:

				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[2], numberdos)
				x += 1

			x += 1

			if len(listobjetosB1)>0:
				worksheet.write(x,1, 'TOTAL ACTIVO CORRIENTE' , bold)

				self.env.cr.execute(""" select sum(saldo) from account_balance_general where grupo = 'B1' """)
				totalB1 = self.env.cr.fetchall()[0]
				
				worksheet.write(x,2, totalB1[0], numberdosbold)
				x+=1

			else:
				worksheet.write(x,1, 'TOTAL ACTIVO CORRIENTE' , bold)

				worksheet.write(x,2, 0, numberdosbold)
				x+=1


			# segunda parte B2
			x += 1

			self.env.cr.execute(""" select name as code,'' as concept, sum(saldo) from account_balance_general
				where grupo = 'B2'
				group by name,grupo,orden
				order by orden,name """)
			listobjetosB1 =  self.env.cr.fetchall()

			worksheet.write(x,1, 'ACTIVO NO CORRIENTE' , bold)

			for i in listobjetosB1:
				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[2], numberdos)
				x += 1

			data_inicial2 = 0

			if len(listobjetosB1)>0:
				worksheet.write(x,1, 'TOTAL ACTIVO NO CORRIENTE' , bold)

				self.env.cr.execute(""" select sum(saldo) from account_balance_general where grupo = 'B2' """)
				totalB1 = self.env.cr.fetchall()[0]

				worksheet.write(x,2, totalB1[0], numberdosbold)	
				data_inicial2 = totalB1[0]
				x+=1

			else:

				worksheet.write(x,1, 'TOTAL ACTIVO NO CORRIENTE' , bold)
				
				worksheet.write(x,2, 0, numberdosbold)			
				x+=1

			pos_inicial2 = x+1

			###  B3 AQUI ES EL LADO DERECHO

			x=6
			self.env.cr.execute(""" select name as code,'' as concept, sum(saldo) from account_balance_general
			where grupo = 'B3'
			group by name,grupo,orden
			order by orden,name """)
			listobjetosB1 =  self.env.cr.fetchall()

			worksheet.write(x,5, 'PASIVO Y PATRIMONIO' , bold)
			#worksheet.write(x,6, self.fiscalyear_id.name + '(' + self.periodo_ini.code[:2] +' - ' + self.periodo_fin.code[:2] + ')' , bold)
			
			x+=2


			worksheet.write(x,5, 'PASIVO CORRIENTE' , bold)
			x+=1

			for i in listobjetosB1:

				worksheet.write(x,5, i[0], normal)
				worksheet.write(x,6, i[2], numberdos)
				x+=1


			if len(listobjetosB1)>0:
				worksheet.write(x,5, 'TOTAL PASIVO CORRIENTE' , bold)
								
				self.env.cr.execute(""" select  sum(saldo) from account_balance_general where grupo = 'B3' """)
				totalB1 = self.env.cr.fetchall()[0]
				worksheet.write(x,6, totalB1[0], numberdosbold)
				x+=1

			else:

				worksheet.write(x,5, 'TOTAL PASIVO CORRIENTE' , bold)
								
				worksheet.write(x,6, 0, numberdosbold)
				x+=1

			x+= 1

			
			###  B4
			self.env.cr.execute(""" select name as code,'' as concept, sum(saldo) from account_balance_general
			where grupo = 'B4'
			group by name,grupo,orden
			order by orden,name """)
			listobjetosB1 =  self.env.cr.fetchall()
			
			worksheet.write(x,5, 'PASIVO NO CORRIENTE' , bold)
			x+=1

			for i in listobjetosB1:
				worksheet.write(x,5, i[0], normal)
				worksheet.write(x,6, i[2], numberdos)
				x+=1

		
			if len(listobjetosB1)>0:
				worksheet.write(x,5, 'TOTAL PASIVO NO CORRIENTE' , bold)
			
				self.env.cr.execute(""" select sum(saldo) from account_balance_general where grupo = 'B4' """)
				totalB1 = self.env.cr.fetchall()[0]

				worksheet.write(x,6, totalB1[0], numberdosbold)
				x+=1

			else:
				
				worksheet.write(x,5, 'TOTAL PASIVO NO CORRIENTE' , bold)
				worksheet.write(x,6, 0, numberdosbold)
				x+=1


			x+= 1




			###  B5
			self.env.cr.execute(""" select name as code,'' as concept,sum(saldo) from account_balance_general
			where grupo = 'B5'
			group by name,grupo,orden
			order by orden,name """)
			listobjetosB1 =  self.env.cr.fetchall()

			worksheet.write(x,5, 'PATRIMONIO' , bold)
			
			for i in listobjetosB1:
				worksheet.write(x,5, i[0] , bold)
				worksheet.write(x,6, i[2], numberdos)
				x+=1


			if len(listobjetosB1)>0:
				worksheet.write(x,5, 'TOTAL PATRIMONIO' , bold)
				
				self.env.cr.execute(""" select  sum(saldo) from account_balance_general where grupo = 'B5' """)
				totalB1 = self.env.cr.fetchall()[0]
				
				worksheet.write(x,6, totalB1[0], numberdosbold)
				x+=1

			else:

				worksheet.write(x,5, 'TOTAL PATRIMONIO' , bold)
								
				worksheet.write(x,6, 0, numberdosbold)
				x+=1

			x+= 1


			worksheet.write(x,5, 'RESULTADO DEL PERIODO' , bold)

			self.env.cr.execute(""" select coalesce(sum(saldo),0) from account_balance_general
			where grupo = 'B1' or grupo = 'B2' """)
			tmp_consultaB1B2 = self.env.cr.fetchall()
			totalA12 = tmp_consultaB1B2[0][0]
			self.env.cr.execute(""" select coalesce(sum(saldo),0) from account_balance_general
			where grupo = 'B3' or grupo = 'B4' or grupo = 'B5' """)
			tmp_consultaB345 = self.env.cr.fetchall()
			totalA345 = tmp_consultaB345[0][0]

			worksheet.write(x,6, totalA12- totalA345, numberdos)
		
			x+=2
			#### AQUI VAN LOS FINALES FINALES
			if x > pos_inicial2:
				pass
			else:
				x = pos_inicial2

			worksheet.write(x,5, 'TOTAL PASIVO Y PATRIMONIO' , bold)
			
			worksheet.write(x,1, 'TOTAL ACTIVO' , bold)


			self.env.cr.execute(""" select coalesce(sum(saldo),0) from account_balance_general
			where grupo = 'B1' or grupo = 'B2' """)
			tmp_totalA12 = self.env.cr.fetchall()
			
			totalA12 = tmp_totalA12[0][0]

			worksheet.write(x,2, totalA12 , numberdosbold)


			worksheet.write(x,6, totalA12 , numberdosbold)

			worksheet.set_column('B:B',57)
			worksheet.set_column('C:C',24)
			worksheet.set_column('F:F',57)
			worksheet.set_column('G:G',24)

			workbook.close()
			
			f = open(direccion + 'Reporte_Balance_general.xlsx', 'rb')
			
			vals = {
				'output_name': 'BalanceGeneral.xlsx',
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
				'output_name': 'Balance General.pdf',
				'output_file': open(direccion + "a.pdf", "rb").read().encode("base64"),	
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
	def cabezera(self,c,wReal,hReal):

		c.setFont("Times-Bold", 10)
		c.setFillColor(black)
		c.drawCentredString((wReal/2)+20,hReal, self.env["res.company"].search([])[0].name.upper())
		c.drawCentredString((wReal/2)+20,hReal-12, "ESTADO DE SITUACIÓN FINANCIERA")
		c.drawCentredString((wReal/2)+20,hReal-24, "AL "+ str(self.periodo_fin.date_stop))
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
		height ,width = A4  # 595 , 842
		wReal = width- 30
		hReal = height - 40

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas( direccion + "a.pdf", pagesize=(width,height) )
		self.save_page_states.append(dict(c.__dict__))
		inicio = 0
		pos_inicialL = hReal-60
		pos_inicialR = hReal-60

		pagina = 1
		textPos = 0
		
		tamanios = {}
		voucherTamanio = None
		contTamanio = 0

		self.cabezera(c,wReal,hReal)
		c.setFont("Times-Bold", 8)
		c.drawCentredString(300,25,'Pág. ' + str(pagina))

		###  B1
		self.env.cr.execute(""" select name as code,'' as concept,sum(saldo) from account_balance_general
			where grupo = 'B1'
			group by name ,grupo,orden
			order by orden,name

			--select * from account_balance_general where grupo = 'B1' order by orden,id""")
		listobjetosB1 =  self.env.cr.fetchall()

		c.setFont("Times-Bold", 8)
		c.drawString( 15 , pos_inicialL, "ACTIVO")
		c.line(15,pos_inicialL-1,52,pos_inicialL-1)
		c.drawString(15,pos_inicialL - 24,"ACTIVO CORRIENTE")

		pos_inicialL = pos_inicialL - 24
		for i in listobjetosB1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(18,pos_inicialL,i[0] )
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %i[2])

		if len(listobjetosB1)>0:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(15,pos_inicialL,"TOTAL ACTIVO CORRIENTE")

			self.env.cr.execute(""" select sum(saldo) from account_balance_general where grupo = 'B1' """)
			totalB1 = self.env.cr.fetchall()[0]
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %totalB1[0])
			c.line((wReal/2)-75, pos_inicialL-2, (wReal/2)-20 ,pos_inicialL-2)
			c.line((wReal/2)-75, pos_inicialL-4, (wReal/2)-20 ,pos_inicialL-4)
			c.line((wReal/2)-75, pos_inicialL+9, (wReal/2)-20 ,pos_inicialL+9)
		else:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(15,pos_inicialL,"TOTAL ACTIVO CORRIENTE")
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %(0.0) )
			c.line((wReal/2)-75, pos_inicialL-2, (wReal/2)-20 ,pos_inicialL-2)
			c.line((wReal/2)-75, pos_inicialL-4, (wReal/2)-20 ,pos_inicialL-4)
			c.line((wReal/2)-75, pos_inicialL+9, (wReal/2)-20 ,pos_inicialL+9)

		self.guardar_state(c)


		nivel_left_page = c._pageNumber
		nivel_left_fila = pos_inicialL
		
		
		self.cargar_pagina(c,1)
		
		###  B3
		self.env.cr.execute(""" select name as code,'' as concept,sum(saldo) from account_balance_general
where grupo = 'B3'
group by name,grupo,orden
order by orden,name

--select * from account_balance_general where grupo = 'B3' order by orden,id""")
		listobjetosB1 =  self.env.cr.fetchall()

		c.setFont("Times-Bold", 8)
		c.drawString( (wReal/2)+20 , pos_inicialR, "PASIVO Y PATRIMONIO")
		c.line( (wReal/2)+20,pos_inicialR-1,(wReal/2)+120,pos_inicialR-1)
		c.drawString((wReal/2)+20,pos_inicialR - 24,"PASIVO CORRIENTE")

		pos_inicialR = pos_inicialR - 24
		for i in listobjetosB1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+23,pos_inicialR,i[0] )
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %i[2])

		if len(listobjetosB1)>0:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PASIVO CORRIENTE")

			self.env.cr.execute(""" select sum(saldo) from account_balance_general where grupo = 'B3' """)
			totalB1 = self.env.cr.fetchall()[0]
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %totalB1[0])
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)
		else:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PASIVO CORRIENTE")
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %(0.0) )
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)

		self.guardar_state(c)


		nivel_right_page = c._pageNumber
		nivel_right_fila = pos_inicialR


		if nivel_left_page > nivel_right_page:
			pos_inicialL = nivel_left_fila
			pos_inicialR = nivel_left_fila
			c.__dict__.update(self.save_page_states[nivel_left_page-1])
		elif nivel_left_page < nivel_right_page:

			pos_inicialL = nivel_right_fila
			pos_inicialR = nivel_right_fila
			c.__dict__.update(self.save_page_states[nivel_right_page-1])

		else:
			if nivel_left_fila < nivel_right_fila:
				pos_inicialL = nivel_left_fila
				pos_inicialR = nivel_left_fila
			else:
				pos_inicialL = nivel_right_fila
				pos_inicialR = nivel_right_fila
			c.__dict__.update(self.save_page_states[nivel_right_page-1])

		# segunda parte B2

		self.env.cr.execute(""" select name as code,'' as concept,sum(saldo) from account_balance_general
			where grupo = 'B2'
			group by name,grupo,orden
			order by orden,name

			--select * from account_balance_general where grupo = 'B2' order by orden,id""")
		listobjetosB1 =  self.env.cr.fetchall()

		c.setFont("Times-Bold", 8)
		c.drawString(15,pos_inicialL - 24,"ACTIVO NO CORRIENTE")

		pos_inicialL = pos_inicialL - 24
		for i in listobjetosB1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(18,pos_inicialL,i[0] )
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %i[2])

		if len(listobjetosB1)>0:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(15,pos_inicialL,"TOTAL ACTIVO NO CORRIENTE")

			self.env.cr.execute(""" select sum(saldo) from account_balance_general where grupo = 'B2' """)
			totalB1 = self.env.cr.fetchall()[0]
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %totalB1[0])
			c.line((wReal/2)-75, pos_inicialL-2, (wReal/2)-20 ,pos_inicialL-2)
			c.line((wReal/2)-75, pos_inicialL-4, (wReal/2)-20 ,pos_inicialL-4)
			c.line((wReal/2)-75, pos_inicialL+9, (wReal/2)-20 ,pos_inicialL+9)
		else:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(15,pos_inicialL,"TOTAL ACTIVO NO CORRIENTE")
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %(0.0) )
			c.line((wReal/2)-75, pos_inicialL-2, (wReal/2)-20 ,pos_inicialL-2)
			c.line((wReal/2)-75, pos_inicialL-4, (wReal/2)-20 ,pos_inicialL-4)
			c.line((wReal/2)-75, pos_inicialL+9, (wReal/2)-20 ,pos_inicialL+9)

		self.guardar_state(c)

		if nivel_left_page > nivel_right_page:
			pos_inicialL = nivel_left_fila
			pos_inicialR = nivel_left_fila
			c.__dict__.update(self.save_page_states[nivel_left_page-1])
		elif nivel_left_page < nivel_right_page:

			pos_inicialL = nivel_right_fila
			pos_inicialR = nivel_right_fila
			c.__dict__.update(self.save_page_states[nivel_right_page-1])

		else:
			if nivel_left_fila < nivel_right_fila:
				pos_inicialL = nivel_left_fila
				pos_inicialR = nivel_left_fila
			else:
				pos_inicialL = nivel_right_fila
				pos_inicialR = nivel_right_fila
			c.__dict__.update(self.save_page_states[nivel_right_page-1])

		nivel_left_page = c._pageNumber
		nivel_left_fila = pos_inicialL
		###  B4
		self.env.cr.execute(""" select name as code,'' as concept,sum(saldo) from account_balance_general
where grupo = 'B4'
group by name,grupo,orden
order by orden,name

--select * from account_balance_general where grupo = 'B4' order by orden,id""")
		listobjetosB1 =  self.env.cr.fetchall()

		c.setFont("Times-Bold", 8)
		c.drawString((wReal/2)+20,pos_inicialR - 24,"PASIVO NO CORRIENTE")

		pos_inicialR = pos_inicialR - 24
		for i in listobjetosB1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+23,pos_inicialR,i[0] )
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %i[2])

		if len(listobjetosB1)>0:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PASIVO NO CORRIENTE")

			self.env.cr.execute(""" select sum(saldo) from account_balance_general where grupo = 'B4' """)
			totalB1 = self.env.cr.fetchall()[0]
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %totalB1[0])
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)
		else:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PASIVO NO CORRIENTE")
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %(0.0) )
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)

		self.guardar_state(c)



		###  B5
		self.env.cr.execute(""" select name as code,'' as concept,sum(saldo) from account_balance_general
where grupo = 'B5'
group by name,grupo,orden
order by orden,name

--select * from account_balance_general where grupo = 'B5' order by orden,id""")
		listobjetosB1 =  self.env.cr.fetchall()

		c.setFont("Times-Bold", 8)
		c.drawString((wReal/2)+20,pos_inicialR - 24,"PATRIMONIO")

		pos_inicialR = pos_inicialR - 24
		for i in listobjetosB1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+23,pos_inicialR,i[0] )
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %i[2])

		if len(listobjetosB1)>0:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PATRIMONIO")

			self.env.cr.execute(""" select sum(saldo) from account_balance_general where grupo = 'B5' """)
			totalB1 = self.env.cr.fetchall()[0]
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %totalB1[0])
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)
		else:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PATRIMONIO")
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %(0.0) )
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)

		c.setFont("Times-Roman", 8)
		pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,24,pagina)
		c.drawString((wReal/2)+20,pos_inicialR,"RESULTADO DEL PERIODO")
		self.env.cr.execute(""" select coalesce(sum(saldo),0) from account_balance_general
where grupo = 'B1' or grupo = 'B2' """)
		totalA12 = self.env.cr.fetchall()[0][0]
		self.env.cr.execute(""" select coalesce(sum(saldo),0) from account_balance_general
where grupo = 'B3' or grupo = 'B4' or grupo = 'B5' """)
		totalA345 = self.env.cr.fetchall()[0][0]
		c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %(totalA12- totalA345) )


		self.guardar_state(c)


		nivel_right_page = c._pageNumber
		nivel_right_fila = pos_inicialR


		if nivel_left_page > nivel_right_page:
			pos_inicialL = nivel_left_fila
			pos_inicialR = nivel_left_fila
			c.__dict__.update(self.save_page_states[nivel_left_page-1])
		elif nivel_left_page < nivel_right_page:

			pos_inicialL = nivel_right_fila
			pos_inicialR = nivel_right_fila
			c.__dict__.update(self.save_page_states[nivel_right_page-1])

		else:
			if nivel_left_fila < nivel_right_fila:
				pos_inicialL = nivel_left_fila
				pos_inicialR = nivel_left_fila
			else:
				pos_inicialL = nivel_right_fila
				pos_inicialR = nivel_right_fila
			c.__dict__.update(self.save_page_states[nivel_right_page-1])


		c.setFont("Times-Bold", 8)
		pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
		c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PASIVO Y PATRIMONIO")
		c.line((wReal/2)+20,pos_inicialR-1,(wReal/2)+145,pos_inicialR-1)

		c.drawString(15,pos_inicialR,"TOTAL ACTIVO")
		c.line(15,pos_inicialR-1,80,pos_inicialR-1)

		self.env.cr.execute(""" select coalesce(sum(saldo),0) from account_balance_general
where grupo = 'B1' or grupo = 'B2' """)
		totalA12 = self.env.cr.fetchall()[0][0]
		c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %totalA12)
		c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
		c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
		c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)


		c.drawRightString( (wReal/2)-20 ,pos_inicialR,"%0.2f" %totalA12)
		c.line((wReal/2)-75, pos_inicialR-2, (wReal/2)-20 ,pos_inicialR-2)
		c.line((wReal/2)-75, pos_inicialR-4, (wReal/2)-20 ,pos_inicialR-4)
		c.line((wReal/2)-75, pos_inicialR+9, (wReal/2)-20 ,pos_inicialR+9)

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

			c.setFont("Times-Bold", 8)
			c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-60
		else:
			return pagina,posactual-valor



class asientos_descuadrados(models.Model):
	_name = 'asientos.descuadrados'
	_auto = False

	periodo = fields.Many2one('account.period','Periodo')
	diario = fields.Many2one('account.journal','Diario')
	asiento = fields.Many2one('account.move','Asiento')
	debe = fields.Float('Debe')
	haber = fields.Float('Haber')
	descuadre = fields.Float('Descuadre')


class asientos_descuadrados_wizard(models.Model):
	_name = 'asientos.descuadrados.wizard'

	period_ini = fields.Many2one('account.period','Periodo Inicial')
	period_fin = fields.Many2one('account.period','Periodo Final')

	@api.model
	def get_wizard(self):
		return self.env['automatic.fiscalyear'].get_wizard('Vouchers Descuadrados',self.id,'asientos.descuadrados.wizard','account_state_financial_it.view_asientos_descuadrados_wizard_form','default_period_ini','default_period_fin')

	@api.onchange('period_ini','period_fin')
	def _change_periodo_ini(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
		if not year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			return {'domain':{'period_ini':[('fiscalyear_id','=',year.id )],'period_fin':[('fiscalyear_id','=',year.id )]}}

	@api.multi
	def do_rebuild(self):

		self.env.cr.execute("""
				drop view if exists asientos_descuadrados;
			create view asientos_descuadrados as (



					select row_number() OVER () AS id,* from (
					
					select am.id as asiento, am.journal_id as diario, ap.id as periodo , sum(debit) as debe, sum(credit) as haber, sum(debit-credit) as descuadre
					from account_move am
					inner join account_move_line aml on aml.move_id = am.id
					inner join account_period ap on ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable and coalesce(ap.special,false) = coalesce(am.fecha_special,false)
					where periodo_num(ap.code) >= periodo_num('""" +str(self.period_ini.code)+ """') and periodo_num(ap.code) <= periodo_num('""" +str(self.period_fin.code)+ """')
					group by am.id, am.journal_id, ap.id
					having abs(sum(debit-credit)) > 0.001

					) Todo


			); 

			""")

		return {
					'name': 'Asientos Descuadrados',
					'view_type': 'form',
					'view_mode': 'tree',
					'res_model': 'asientos.descuadrados',
					'type': 'ir.actions.act_window',
		}






class tc_descuadrados(models.Model):
	_name = 'tc.descuadrados'
	_auto = False

	estado = fields.Char('Estado Factura')
	periodo = fields.Char('Periodo')
	libro = fields.Char('Libro')
	voucher = fields.Char('Voucher')
	fechaemision = fields.Date('Fecha Emision')
	tipodocumento = fields.Char('Tipo de Documento')
	numero = fields.Char('Nro. Comprobante')
	tipodecambio = fields.Float('Tipo de Cambio Factura',digits=(12,3))
	tipo_venta = fields.Float('Tipo de Cambio Sunat',digits=(12,3))
	check_currency_rate = fields.Boolean('TC Personalizado')


class tc_descuadrados_wizard(models.Model):
	_name = 'tc.descuadrados.wizard'

	fecha_ini = fields.Many2one('account.period','Periodo Inicial')
	fecha_fin = fields.Many2one('account.period','Periodo Final')

	@api.model
	def get_wizard(self):
		return self.env['automatic.fiscalyear'].get_wizard('Ventas Factura TC Descuadrados',self.id,'tc.descuadrados.wizard','account_state_financial_it.view_tc_descuadrados_wizard_form','default_fecha_ini','default_fecha_fin')

	@api.onchange('fecha_ini','fecha_fin')
	def _change_periodo_ini(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
		if not year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			return {'domain':{'fecha_ini':[('fiscalyear_id','=',year.id )],'fecha_fin':[('fiscalyear_id','=',year.id )]}}

	@api.multi
	def do_rebuild(self):

		self.env.cr.execute("""
				drop view if exists tc_descuadrados;
			create view tc_descuadrados as (



					select row_number() OVER () AS id,* from (
					
					
					select ai.state as estado,a1.periodo,a1.libro,a1.voucher,a1.fechaemision,a1.tipodocumento,a1.numero,a1.tipodecambio,a2.type_sale as tipo_venta,ai.currency_rate_auto, ai.check_currency_rate 
from get_venta_1_1_1(201801,202212) a1
inner join account_move am on am.id = a1.am_id
left join account_invoice ai on ai.move_id = am.id
left join (select a1.name,a1.type_sale,a1.type_purchase from res_currency_rate a1  inner join res_currency a2 on a2.id = a1.currency_id where a2.name = 'USD') a2 on a2.name=a1.fechaemision
where a1.divisa<>'PEN' and a1.tipodecambio<>a2.type_sale and tipodocumento != '07'
and ( (ai.check_currency_rate= false) or (ai.id is null) ) and periodo_num(periodo) >= periodo_num('""" +str(self.fecha_ini.code)+ """') and periodo_num(periodo) <= periodo_num('""" +str(self.fecha_fin.code)+ """') 
order by fechaemision

					) Todo


			); 

			""")

		return {
					'name': 'TC Descuadrados',
					'view_type': 'form',
					'view_mode': 'tree',
					'res_model': 'tc.descuadrados',
					'type': 'ir.actions.act_window',
		}





class compra_tc_descuadrados_wizard(models.Model):
	_name = 'compra.tc.descuadrados.wizard'

	fecha_ini = fields.Many2one('account.period','Periodo Inicial')
	fecha_fin = fields.Many2one('account.period','Periodo Final')

	@api.model
	def get_wizard(self):
		return self.env['automatic.fiscalyear'].get_wizard('Ventas Factura TC Descuadrados',self.id,'compra.tc.descuadrados.wizard','account_state_financial_it.view_tc_descuadrados_wizard_form_compra','default_fecha_ini','default_fecha_fin')

	@api.onchange('fecha_ini','fecha_fin')
	def _change_periodo_ini(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
		if not year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			return {'domain':{'fecha_ini':[('fiscalyear_id','=',year.id )],'fecha_fin':[('fiscalyear_id','=',year.id )]}}

	@api.multi
	def do_rebuild(self):

		self.env.cr.execute("""
				drop view if exists tc_descuadrados;
			create view tc_descuadrados as (



					select row_number() OVER () AS id,* from (
					
					
					select ai.state as estado,a1.periodo,a1.libro,a1.voucher,a1.fechaemision,a1.tipodocumento,a1.numero,a1.tc as tipodecambio,a2.type_sale as tipo_venta,ai.currency_rate_auto, ai.check_currency_rate 
from get_compra_1_1_1(201801,202212) a1
inner join account_move am on am.id = a1.am_id
left join account_invoice ai on ai.move_id = am.id
left join (select a1.name,a1.type_sale,a1.type_purchase from res_currency_rate a1  inner join res_currency a2 on a2.id = a1.currency_id where a2.name = 'USD') a2 on a2.name=a1.fechaemision
where a1.moneda<>'PEN' and a1.tc<>a2.type_sale and tipodocumento != '08'
and ( (ai.check_currency_rate= false) or (ai.id is null) ) and periodo_num(periodo) >= periodo_num('""" +str(self.fecha_ini.code)+ """') and periodo_num(periodo) <= periodo_num('""" +str(self.fecha_fin.code)+ """') 
order by fechaemision

					) Todo


			); 

			""")

		return {
					'name': 'TC Descuadrados',
					'view_type': 'form',
					'view_mode': 'tree',
					'res_model': 'tc.descuadrados',
					'type': 'ir.actions.act_window',
		}