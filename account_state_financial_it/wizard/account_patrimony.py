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
import base64
import re
from datetime import *
from odoo.exceptions import UserError, ValidationError

class account_patrimony(models.Model):
	_name='account.patrimony'

	concept = fields.Char(string='Descripción', size=50)
	
	capital = fields.Float('Capital',digits=(12,2))
	capital_aditional = fields.Float('Capital Adicional',digits=(12,2))
	parti_pat_tra = fields.Float('Parti. Patr. Trab.',digits=(12,2))
	reserva = fields.Float('Reserva Legal',digits=(12,2))
	otras = fields.Float('Otras Reservas',digits=(12,2))
	resultads = fields.Float('Resultados Acumulados',digits=(12,2))
	_rec_name='concept'

class account_patrimony_wizard(osv.TransientModel):
	_name='account.patrimony.wizard'

	def get_fiscalyear(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		id_year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1).id
		if not id_year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			return id_year

	fiscalyear_id = fields.Many2one('account.fiscalyear',string="Año Fiscal",default=lambda self: self.get_fiscalyear(),readonly=True)
	period_ini = fields.Many2one('account.period',string="Periodo Inicial")
	period_fin = fields.Many2one('account.period',string="Periodo Final")
	type_show =  fields.Selection([('pdf','Pdf'),('excel','Excel')], 'Mostrar en',default='excel', required=True)
	save_page_states= []

	@api.model
	def get_wizard(self):
		return self.env['automatic.fiscalyear'].get_wizard('Patrimonio Neto',self.id,'account.patrimony.wizard','account_state_financial_it.view_account_patrimony_wizard_form','default_period_ini','default_period_fin')

	@api.multi
	def do_rebuild(self):

		for i in self.env['account.patrimony'].search([]):
			i.unlink()

		periodos = []
		periodos.append(self.period_ini.id)
		mes = int(self.period_ini.code.split('/')[0])
		anio = int(self.period_ini.code.split('/')[1])
		per = ("%2d"%mes).replace(' ','0') + '/' + str(anio)

		while per != self.period_fin.code:
			mes +=1
			per = ("%2d"%mes).replace(' ','0') + '/' + str(anio)
			t = self.env['account.period'].search([('code','=',per)])
			if len(t)>0:
				periodos.append( t[0].id )


		t_i = [0,0,0,0,0,0]


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
			worksheet = workbook.add_worksheet(u"Patrimonio Neto")
			bold = workbook.add_format({'bold': True})
			normal = workbook.add_format()
			boldbord = workbook.add_format({'bold': True})
			boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(9)
			#boldbord.set_bg_color('#DCE6F1')
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'#,##0.00'})

			numbertresbold = workbook.add_format({'num_format':'0.000','bold': True})
			numberdosbold = workbook.add_format({'num_format':'#,##0.00','bold': True,'top':1,'bottom':6})
			bord = workbook.add_format()
			bord.set_border(style=1)

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
			#merge_format.set_bg_color('#DCE6F1')
			merge_format.set_text_wrap()
			merge_format.set_font_size(9)


			worksheet.write(1,2, self.env["res.company"].search([])[0].name.upper(), bold)
			worksheet.write(2,2, "ESTADO DE CAMBIOS EN EL PATRIMONIO NETO", bold)
			worksheet.write(3,2, "AL "+ str(self.period_fin.date_stop), bold)
			worksheet.write(4,2, "(Expresado en Nuevos Soles)", bold)
		
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


			x=6
			worksheet.write(x,1, 'CONCEPTOS', boldbord)
			pos_tittle = 2
			patrimonios_order = []
			for i in self.env['account.patrimony.it'].search([]):
				worksheet.write(x,pos_tittle, i.name,boldbord)

				patrimonios_order.append(i.id)
				pos_tittle += 1

			worksheet.write(x,pos_tittle, 'TOTALES', boldbord)
			x+=1
			listobjetos1 =  self.env['account.patrimony'].search([])

			totales = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			for j in self.env['account.move.line'].search([('move_id.fecha_contable','>=',self.period_ini.date_start),('move_id.fecha_contable','<=',self.period_fin.date_stop),('account_id.patrimony_id','!=',False)]):
				periodo = self.env['account.period'].search([('date_start','<=',j.move_id.fecha_contable),('date_stop','>=',j.move_id.fecha_contable),('special','=',j.move_id.fecha_special)])[0]
				if periodo.id in periodos:

					worksheet.write(x,1, j.name if j.name else '', normal)  #credit-debit

					cont_data = 2
					for m in patrimonios_order:
						if m == j.account_id.patrimony_id.id:
							worksheet.write(x,cont_data, j.credit - j.debit , numberdos)
							totales[cont_data-2] += j.credit - j.debit
							cont_data += 1
						else:
							worksheet.write(x,cont_data, 0 , numberdos)
							cont_data += 1

					worksheet.write(x,cont_data, j.credit - j.debit , numberdos)
					totales[cont_data-2] += j.credit - j.debit

					x+= 1


			worksheet.write(x,1, 'TOTALES' , bold)
			
			for tot in range(len(patrimonios_order)+1):
				worksheet.write(x,2+ tot, totales[tot] , numberdosbold)

			#### FIN


			worksheet.set_column('B:B',57)
			worksheet.set_column('C:C',19)
			worksheet.set_column('F:F',19)
			worksheet.set_column('G:G',19)
			worksheet.set_column('H:H',19)
			worksheet.set_column('I:I',19)
			worksheet.set_column('J:J',19)
			worksheet.set_column('K:K',19)
			worksheet.set_column('L:L',19)
			worksheet.set_column('M:ZZ',19)


			workbook.close()
			
			f = open(direccion + 'Reporte_state_function.xlsx', 'rb')
			
			vals = {
				'output_name': 'PatrimonioNeto.xlsx',
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
				'output_name': 'Patrimonio Neto.pdf',
				'output_file': open(direccion + "a.pdf", "rb").read().encode("base64"),	
			}
			sfs_id = self.env['export.file.save'].create(vals)
			#result = {}
			#view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
			#view_id = view_ref and view_ref[1] or False
			#result = act_obj.read( [view_id] )
			#print sfs_id
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
		c.drawCentredString((wReal/2)+20,hReal-12, "ESTADO DE CAMBIOS EN EL PATRIMONIO NETO")
		c.drawCentredString((wReal/2)+20,hReal-24, "AL "+ str(self.period_fin.date_stop))
		c.drawCentredString((wReal/2)+20,hReal-36, "(Expresado en Nuevos Soles)")

		style = getSampleStyleSheet()["Normal"]
		style.leading = 8
		style.alignment= 1
		paragraph1 = Paragraph(
		    "<font size=7><b>CONCEPTOS</b></font>",
		    style
		)
		paragraph2 = Paragraph(
		    "<font size=7><b>Capital</b></font>",
		    style
		)
		paragraph3 = Paragraph(
		    "<font size=7><b>Capital Adicional</b></font>",
		    style
		)
		paragraph4 = Paragraph(
		    "<font size=7><b>Parti. Patrimon. De Trabajo</b></font>",
		    style
		)
		paragraph5 = Paragraph(
		    "<font size=7><b>Reserva Legal</b></font>",
		    style
		)
		paragraph6 = Paragraph(
		    "<font size=7><b>Otras Reservas</b></font>",
		    style
		)
		paragraph7 = Paragraph(
		    "<font size=7><b>Resultados Acumulados</b></font>",
		    style
		)
		paragraph8 = Paragraph(
		    "<font size=7><b>Totales</b></font>",
		    style
		)
		paragraph9 = Paragraph(
		    "<font size=7><b>S/.</b></font>",
		    style
		)
		data= [[ paragraph1 , paragraph2 , paragraph3 , paragraph4, paragraph5 , paragraph6 , paragraph7 , paragraph8 ],
		['',  paragraph9,  paragraph9,  paragraph9,  paragraph9,  paragraph9,  paragraph9,  paragraph9]]
		t=Table(data,colWidths=(270,75, 75, 75, 75,75, 75, 75), rowHeights=(30,10))
		t.setStyle(TableStyle([
			('SPAN',(0,0),(0,1)),
			('GRID',(0,0),(-1,-1), 1, colors.black),
			('ALIGN',(0,0),(-1,-1),'CENTER'),
			('VALIGN',(0,0),(-1,-1),'MIDDLE'),
			('TEXTFONT', (0, 0), (-1, -1), 'Times-Bold'),
			('FONTSIZE',(0,0),(-1,-1),7)
		]))
		t.wrapOn(c,22,500)
		t.drawOn(c,22,hReal-85)

	@api.multi
	def x_aument(self,a):
		a[0] = a[0]+1

	@api.multi
	def reporteador(self):

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		height , width = A4  # 595 , 842
		wReal = width- 30
		hReal = height - 40

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas( direccion + "a.pdf", pagesize= (width,height) )
		inicio = 0
		pos_inicial = hReal-100
		libro = None
		voucher = None
		total = 0
		debeTotal = 0
		haberTotal = 0
		pagina = 1
		textPos = 0
		
		self.cabezera(c,wReal,hReal)

		c.setFont("Times-Bold", 8)
		#c.drawCentredString(300,25,'Pág. ' + str(pagina))


		listobjetos1 =  self.env['account.patrimony'].search([])

		totales = [0,0,0,0,0,0,0,0]
		for i in listobjetos1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			#c.drawString(15,pos_inicial,i[8])
			c.drawString(22,pos_inicial,i.concept if i.concept else '')
			
			cont = [0]

			c.drawRightString( 365 ,pos_inicial,"%0.2f" %i.capital)
			totales[0] += i.capital 
			c.drawRightString( 440 ,pos_inicial,"%0.2f" %i.capital_aditional) 
			totales[1] += i.capital_aditional
			c.drawRightString( 515 ,pos_inicial,"%0.2f" %i.parti_pat_tra)
			totales[2] += i.parti_pat_tra
			c.drawRightString( 590 ,pos_inicial,"%0.2f" %i.reserva)
			totales[3] += i.reserva
			c.drawRightString( 665 ,pos_inicial,"%0.2f" %i.otras)
			totales[4] += i.otras
			c.drawRightString( 740 ,pos_inicial,"%0.2f" %i.resultads)
			totales[5] += i.resultads
			c.drawRightString( 815 ,pos_inicial,"%0.2f" %(i.capital + i.capital_aditional + i.parti_pat_tra + i.reserva + i.otras + i.resultads  ) ) 
			totales[6] += i.capital + i.capital_aditional + i.parti_pat_tra + i.reserva + i.otras + i.resultads
		

		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,18,pagina)			
		c.setFont("Times-Bold", 8)
		c.drawString(22,pos_inicial, 'Totales')			
		c.drawRightString( 365 ,pos_inicial,"%0.2f" %totales[0]) 
		c.drawRightString( 440 ,pos_inicial,"%0.2f" %totales[1]) 
		c.drawRightString( 515 ,pos_inicial,"%0.2f" %totales[2])
		c.drawRightString( 590 ,pos_inicial,"%0.2f" %totales[3])
		c.drawRightString( 665 ,pos_inicial,"%0.2f" %totales[4])
		c.drawRightString( 740 ,pos_inicial,"%0.2f" %totales[5])
		c.drawRightString( 815 ,pos_inicial,"%0.2f" %totales[6]) 
	
		c.line(290,pos_inicial -4, 815 , pos_inicial -4)
		c.line(290,pos_inicial -6, 815 , pos_inicial -6)
		c.line(290,pos_inicial +8, 815 , pos_inicial +8)
			
		#pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
		#c.drawString(100, pos_inicial, "SALDO AL         " + str(self.date_si))

		#self.env.cr.execute(""" select exercise, sum(capital), sum(capital_aditional), sum(action_inversion), sum(reservas), sum(excedente_revaluacion), sum(resultados_acum) from account_patrimony
		#	where exercise = '0'
		#	and ( capital !=0 or action_inversion !=0 or capital_aditional != 0 or result_no_realizate != 0 or excedente_revaluacion != 0 or reservas!= 0 or resultados_acum != 0 )
		#	group by exercise
		#	order by exercise  """)
		#listobjetos1 =  self.env.cr.fetchall()
		#if len(listobjetos1)>0:

		#	i = listobjetos1[0]
		#	cont = [0]
		#	c.drawRightString( 365 ,pos_inicial,"%0.2f" %i[1]) if i[1] else self.x_aument(cont)
		#	c.drawRightString( 440 ,pos_inicial,"%0.2f" %i[2]) if i[2] else self.x_aument(cont)
		#	c.drawRightString( 515 ,pos_inicial,"%0.2f" %i[3]) if i[3] else self.x_aument(cont)
		#	c.drawRightString( 590 ,pos_inicial,"%0.2f" %i[4]) if i[4] else self.x_aument(cont)
		#	c.drawRightString( 665 ,pos_inicial,"%0.2f" %i[5]) if i[5] else self.x_aument(cont)
		#	c.drawRightString( 740 ,pos_inicial,"%0.2f" %i[6]) if i[6] else self.x_aument(cont)
		#	c.drawRightString( 815 ,pos_inicial,"%0.2f" %(i[1] +i[2] +i[3] +i[4] +i[5] +i[6]  ) ) if cont[0] <6 else self.x_aument(cont)
			
		#else:
		#	c.drawRightString( 815 ,pos_inicial,"%0.2f" %0)



		c.save()


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
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina):
		if posactual <40:
			c.showPage()
			self.cabezera(c,wReal,hReal)

			c.setFont("Times-Bold", 8)
			#c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-100
		else:
			return pagina,posactual-valor