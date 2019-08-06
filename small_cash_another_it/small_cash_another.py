# -*- coding: utf-8 -*-
import codecs

from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _


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

class small_cash_another(models.Model):
	_name = 'small.cash.another'

	STATE_SELECTION = [
		('draft', 'Borrador'),
		('done', 'Monitoreando'),
		('checked', 'Revisado Contable'),
		('cancel', 'Cancelado')
	]
	
	@api.multi
	def export_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})

		direccion = self.env['main.parameter'].search([])[0].dir_create_file

		workbook = Workbook(direccion +'tempo_cajachica.xlsx')
		worksheet = workbook.add_worksheet("Caja Chica")
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
		numberdos = workbook.add_format({'num_format':'0.00'})
		bord = workbook.add_format()
		bord.set_border(style=1)
		numberdos.set_border(style=1)
		numbertres.set_border(style=1)			
		x= 6				
		tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tam_letra = 1.2
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		
		worksheet.write(0,0, self.name, bold)
		worksheet.write(1,0, "Caja Chica:", bold)
		worksheet.write(1,1, self.journal_id.name, normal)
		worksheet.write(2,0, "Responsable:", bold)
		worksheet.write(2,1, self.user_id.name, normal)
		worksheet.write(3,0, "Periodo:",bold)
		worksheet.write(3,1, self.period_id.name,bold)
		#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
		import datetime
		#worksheet.write(1,1, str(datetime.datetime.today())[:10], normal)
		
		worksheet.write(5,0, "Voucher",boldbord)
		worksheet.write(5,1, "Nro. Comprobante",boldbord)
		worksheet.write(5,2, "Factura",boldbord)
		worksheet.write(5,3, "Fecha",boldbord)
		worksheet.write(5,4, u"Descripción",boldbord)
		worksheet.write(5,5, u"Empresa",boldbord)
		worksheet.write(5,6, "Ingreso",boldbord)
		worksheet.write(5,7, "Egreso",boldbord)
		worksheet.write(5,8, "Saldo",boldbord)
		worksheet.write(5,9, "Control",boldbord)
		
		for line in self.lines_id:
			worksheet.write(x,0,line.voucher if line.voucher else '' ,bord )
			worksheet.write(x,1,line.nro_comprobante if line.nro_comprobante  else '',bord )
			worksheet.write(x,2,line.nro_invoice if line.nro_invoice  else '',bord)
			worksheet.write(x,3,line.date if line.date  else '',bord)
			worksheet.write(x,4,line.description if line.description  else '',bord)
			worksheet.write(x,5,line.partner_id.name if line.partner_id.id  else '',bord)
			worksheet.write(x,6,line.incoming_amount ,numberdos)
			worksheet.write(x,7,line.outcoming_amount ,numberdos)
			worksheet.write(x,8,line.result_amount ,numberdos)
			worksheet.write(x,9,line.state if  line.state else '',bord)
			x+=1
		
		tam_col = [11,30,11,11,30,11,11,11,11]

		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])
		worksheet.set_column('H:H', tam_col[7])
		worksheet.set_column('I:I', tam_col[8])
		
		workbook.close()
			
		f = open(direccion + 'tempo_cajachica.xlsx', 'rb')


		vals = {
			'output_name': 'CajaChica.xlsx',
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


	@api.multi
	def exportar_pdf(self):
		
		self.reporteador()
		
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		import os

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		vals = {
			'output_name': 'CajaChica.pdf',
			'output_file': open(direccion + "cajachica.pdf", "rb").read().encode("base64"),	
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

		c.setFont("Calibri-Bold", 10)
		c.setFillColor(black)
		c.drawCentredString((wReal/2)+20,hReal, self.env["res.company"].search([])[0].name.upper())
		c.drawCentredString((wReal/2)+20,hReal-12, "Caja Chica: "+ self.name )

		c.setFont("Calibri-Bold", 8)

		c.drawString( 10,hReal-36, 'Caja Chica:')
		c.drawString( 10,hReal-48, 'Responsable:')
		c.drawString( 400,hReal-36, 'Periodo:')


		c.setFont("Calibri", 8)
		c.drawString( 10+90,hReal-36, self.journal_id.name)
		c.drawString( 10+90,hReal-48, self.user_id.name)
		c.drawString( 400+60,hReal-36, self.period_id.name)




		style = getSampleStyleSheet()["Normal"]
		style.leading = 8
		style.alignment= 1
		paragraph1 = Paragraph(
		    "<font size=6><b>Voucher</b></font>",
		    style
		)
		paragraph2 = Paragraph(
		    "<font size=6><b>Comprobante</b></font>",
		    style
		)
		paragraph3 = Paragraph(
		    "<font size=6><b>Factura</b></font>",
		    style
		)
		paragraph4 = Paragraph(
		    "<font size=6><b>Fecha</b></font>",
		    style
		)
		paragraph5 = Paragraph(
		    "<font size=6><b>Descripción</b></font>",
		    style
		)
		paragraph6 = Paragraph(
		    "<font size=6><b>Empresa</b></font>",
		    style
		)
		paragraph7 = Paragraph(
		    "<font size=6><b>Ingreso</b></font>",
		    style
		)
		paragraph8 = Paragraph(
		    "<font size=6><b>Egreso</b></font>",
		    style
		)
		paragraph9 = Paragraph(
		    "<font size=6><b>Saldo</b></font>",
		    style
		)
		paragraph10 = Paragraph(
		    "<font size=6><b>Control</b></font>",
		    style
		)

		data= [[ paragraph1 ,paragraph2,paragraph3,paragraph4,paragraph5,paragraph6,paragraph7,paragraph8,paragraph9,paragraph10]]

		t=Table(data,colWidths=(40,55,55,45,90,80,55,55,55,55), rowHeights=(15))

		t.setStyle(TableStyle([
			('GRID',(0,0),(-1,-1), 1, colors.black),
			('ALIGN',(0,0),(-1,-1),'LEFT'),
			('VALIGN',(0,0),(-1,-1),'MIDDLE'),
			('TEXTFONT', (0, 0), (-1, -1), 'Calibri-Bold'),
			('FONTSIZE',(0,0),(-1,-1),4),
			('BACKGROUND', (0, 0), (-1, -1), colors.gray)
		]))

		t.wrapOn(c,10,hReal-82)
		t.drawOn(c,10,hReal-82)





	@api.multi
	def x_aument(self,a):
		a[0] = a[0]+1

	@api.multi
	def reporteador(self):

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')


		pdfmetrics.registerFont(TTFont('Calibri', 'Calibri.ttf'))
		pdfmetrics.registerFont(TTFont('Calibri-Bold', 'CalibriBold.ttf'))

		width ,height  = A4  # 595 , 842
		wReal = width- 30
		hReal = height - 40

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas( direccion + "cajachica.pdf", pagesize= A4 )
		inicio = 0
		pos_inicial = hReal-82
		libro = None
		voucher = None
		total = 0
		debeTotal = 0
		haberTotal = 0
		pagina = 1
		textPos = 0
		
		self.cabezera(c,wReal,hReal)

		tam = [40,55,55,45,90,80,55,55,55,55]


		for line in self.lines_id:
			c.setFont("Calibri", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			
			c.drawString( 10 ,pos_inicial, line.voucher if line.voucher else '' )
			c.drawString( 50 ,pos_inicial, line.nro_comprobante if line.nro_comprobante  else '' )
			c.drawString( 105 ,pos_inicial, line.nro_invoice if line.nro_invoice  else '' )
			c.drawString( 160 ,pos_inicial, line.date if line.date  else '' )
			c.drawString( 205 ,pos_inicial, self.particionar_text( line.description if line.description  else '',80) )
			c.drawString( 295 ,pos_inicial, self.particionar_text( line.partner_id.name if line.partner_id.id  else '',70) )
			c.drawRightString( 425 ,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%line.incoming_amount )))
			c.drawRightString( 475 ,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % line.outcoming_amount)))
			c.drawRightString( 535 ,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % line.result_amount)))
			c.drawString( 542 ,pos_inicial, line.state if  line.state else '' )


		c.save()


	@api.multi
	def particionar_text(self,c,tam):
		tet = ""
		for i in range(len(c)):
			tet += c[i]
			lines = simpleSplit(tet,'Calibri',8,tam)
			if len(lines)>1:
				return tet[:-1]
		return tet

	@api.multi
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina):
		if posactual <40:
			c.showPage()
			self.cabezera(c,wReal,hReal)

			c.setFont("Calibri-Bold", 8)
			#c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-82
		else:
			return pagina,posactual-valor









	
	@api.one
	def checked(self):
		self.write({'state': 'checked'})
		
	@api.one
	def aprove(self):
		if self.named == False:

			id_seq = self.env['ir.sequence'].search([('name','=','Caja Chica 8.0')])
			if len(id_seq)>0:
				id_seq = id_seq[0]
			else:
				id_seq = self.env['ir.sequence'].create({'name':'Caja Chica 8.0','implementation':'standard','active':True,'prefix':'CC-','padding':4,'number_increment':1,'number_next_actual' :1})
			
			name_tmp = id_seq.next_by_id()

			self.write({'state': 'done', 'name': name_tmp, 'named': True})
		else:
			self.write({'state': 'done'})
	
	@api.one
	def action_cancel(self):
		self.write({'state': 'draft'})

	
	@api.multi
	def _get_lines(self):
		for cash in self:
			if cash.state in ['done','checked']:
				#Borro todas las lineas de la caja
				ids = self.env['small.cash.line'].search([('line_id','=',cash.id)])
				ids.unlink()
				
				#Busco los ids de los asientos contables
				#ids_moves = self.env['account.move'].search([('period_id','=',cash.period_id.id),('journal_id','=',cash.journal_id.id),('state','=','posted')]).mapped('id')
				#print 'ids_moves', ids_moves
				
				#moves_lines = self.env['account.move.line'].search([('move_id','in',ids_moves), ('account_id','=',cash.journal_id.default_debit_account_id.id)]).sorted(key=lambda r: r.date)
				
				#Nueva version ordenada por fecha, voucher
				self.env.cr.execute("""
					select 
						aml.id,
						am.name,
						am.date,
						aml.debit, 
						aml.credit 
					from 
						account_move_line aml JOIN 
						account_move am ON aml.move_id = am.id
					where
						aml.small_cash_id = """ + str(cash.id) +"""
					order by am.date,am.name
				""")
				moves_lines = self.env.cr.dictfetchall()
				
				new_lines = []
				total = 0.00
				for move_line in moves_lines:
					total += move_line['debit'] - move_line['credit']
					state = ''
					if total > cash.journal_id.max_import_cash:
						state = 'Saldo Excedido'
					new_lines += self.env['small.cash.line'].create({'move_line_id': move_line['id'], 'line_id': cash.id, 'result_amount': total, 'state': state})

				cash.lines_id = False
				cash.lines_id = [(6,0,[x['id'] for x in new_lines])]
	
	@api.depends('state')
	def _get_initial_amount(self):
		for cash in self:
			if cash.state in ['done', 'checked']:
				ids_moves = self.env['account.move'].search([('date','>=', cash.period_id.fiscalyear_id.name + '-01-01'),('date','<=',cash.period_id.date_stop),('journal_id','=',cash.journal_id.id),('state','=','posted')]).mapped('id')
				moves_lines = self.env['account.move.line'].search([('move_id','in',ids_moves),('account_id','=',cash.journal_id.default_debit_account_id.id)]).sorted(key=lambda r: r.date)
				
				debit = 0.00
				credit = 0.00
				for move_line in moves_lines:
					debit += move_line.debit
					credit += move_line.credit
				cash.initial_amount = debit - credit
	
	name = fields.Char('Nombre',size=50, default='Caja Borrador')
	journal_id = fields.Many2one('account.journal','Caja Chica')
	user_id = fields.Many2one('res.users','Responsable')
	period_id = fields.Many2one('account.period','Periodo')
	named = fields.Boolean('Tiene Nombre', default=False)
	lines_id = fields.One2many('small.cash.line', 'line_id', string="Movimientos", compute='_get_lines')
	state = fields.Selection(STATE_SELECTION, 'Status', readonly=True, select=True, default='draft')
	
	
class small_cash_line(models.Model):
	_name = 'small.cash.line'
	_order = 'date'
	
	@api.depends('move_line_id', 'line_id')
	def _get_incoming_amount(self):
		for cash_line in self:
			cash_line.incoming_amount = cash_line.move_line_id.debit
	
	@api.depends('move_line_id', 'line_id')
	def _get_outcoming_amount(self):
		for cash_line in self:
			cash_line.outcoming_amount = cash_line.move_line_id.credit
	
	'''
	@api.depends('move_line_id', 'line_id')
	def _get_date(self):
		for cash_line in self:
			cash_line.date = cash_line.move_line_id.date
	'''
	
	@api.model
	def create(self,vals):
		if 'move_line_id' in vals:
			line = self.env['account.move.line'].browse( vals['move_line_id'] )
			vals.update({'date':line.move_id.date})
		return super(small_cash_line, self).create( vals)
		
	@api.depends('move_line_id', 'line_id')
	def _get_voucher(self):
		for cash_line in self:
			cash_line.voucher = cash_line.move_line_id.move_id.name	
	
	@api.depends('move_line_id', 'line_id')
	def _get_nro_comprobante(self):
		for cash_line in self:
			cash_line.nro_comprobante = cash_line.move_line_id.nro_comprobante

	
	@api.depends('move_line_id', 'line_id')
	def _get_partner_id(self):
		for cash_line in self:
			cash_line.partner_id = cash_line.move_line_id.partner_id.id
	
	@api.depends('move_line_id', 'line_id')
	def _get_nro_invoice(self):
		for cash_line in self:
			invoice = None
			for line in cash_line.move_line_id.move_id.line_ids:
				if line.account_id.id != cash_line.line_id.journal_id.default_debit_account_id.id:
					if invoice is None:
						invoice = line.nro_comprobante
					if invoice != line.nro_comprobante:
						invoice = 'VARIOS'
			cash_line.nro_invoice = invoice
	
	@api.depends('move_line_id', 'line_id')
	def _get_description(self):
		for cash_line in self:
			cash_line.description = cash_line.move_line_id.name

	@api.depends('move_line_id','line_id')
	def _get_doc_type(self):
		for cash_line in self:
			cash_line.doc_type = cash_line.move_line_id.type_document_it.name if cash_line.move_line_id.type_document_it else ''

	move_line_id = fields.Many2one('account.move.line', 'Apunte Contable')
	date = fields.Date('Fecha')
	voucher = fields.Char('Voucher', size=50, compute='_get_voucher')
	nro_comprobante = fields.Char('Nro Op. Caja Chica', size=50, compute='_get_nro_comprobante')
	doc_type = fields.Char('Tipo de Documento',compute='_get_doc_type')
	nro_invoice = fields.Char('Nro Comprobante', size=50, compute='_get_nro_invoice')
	description = fields.Char('Descripcion', size=255, compute='_get_description')
	incoming_amount = fields.Float('Ingreso', digits=(12,2), compute='_get_incoming_amount')
	outcoming_amount = fields.Float('Egreso', digits=(12,2), compute='_get_outcoming_amount')
	result_amount = fields.Float('Saldo', digits=(12,2))
	state = fields.Char('Control', size=50)
	line_id = fields.Many2one('small.cash.another', 'Caja Chica')
	partner_id = fields.Many2one('res.partner', string="Proveedor", compute='_get_partner_id')


