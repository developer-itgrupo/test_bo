# -*- coding: utf-8 -*-

from openerp import models, fields, api , exceptions , _
from openerp.osv import osv
import re
import base64



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

class account_move_comprobante(models.Model):
	_name='account.move.comprobante'
	_auto = False

	name = fields.Char('Comprobante')
	aml_id = fields.Integer('aml_id')
	partner_id = fields.Many2one('res.partner','Partner')

	@api.model_cr
	def init(self):
		self.env.cr.execute(""" 
			drop view if exists account_move_comprobante;
			create or replace view account_move_comprobante as (


select aml_id as id,* from
(
select 
aml.nro_comprobante || ' (' || coalesce(itd.code,'') || ' )' as name, 
aat.type,
aml.id as aml_id, 
aml.debit,
aml.credit ,
aml.partner_id

from account_move_line aml
left join einvoice_catalog_01 itd on itd.id = aml.type_document_it
inner join account_account aa on aa.id = aml.account_id
inner join account_account_type aat on aat.id = aa.user_type_id
where aat.type in ('payable','receivable')
and aml.nro_comprobante is not null and aml.nro_comprobante !=''
and ( (aat.type = 'payable' and aml.credit >0 ) or (aat.type = 'receivable' and aml.debit >0 ) )
order by aml.nro_comprobante



						) AS T  )

			""")



class account_move_line(models.Model):
	_inherit='account.move.line'

	@api.multi
	def edit_linea_it(self):
		if self.move_id.state != 'draft':
			raise osv.except_osv('Alerta!', "No se puede modificar una linea de un Asiento Asentado.")
		data = {
			'default_glosa':self.name,
			'default_empresa': self.partner_id.id,
			'default_comprobante_manual': self.nro_comprobante,
			'default_account_id':self.account_id.id,
			'default_date_vencimiento': self.date_maturity,
			'default_debit': self.debit,
			'default_credit':self.credit,
			'default_analytic_id': self.analytic_account_id.id,
			'default_import_divisa': self.amount_currency,
			'default_currency_id': self.currency_id.id,
			'default_impuesto':self.tax_code_id.id,
			'default_importe_impuesto':self.tax_amount,
			'default_type_change':self.tc,
			'default_type_doc_id':self.type_document_it.id,
			'default_rendicion_id': self.rendicion_id.id,
			'active_ids_line': self.id,
			'default_uom_id': self.product_uom_id.id,
			'default_cantidad': self.quantity,
			'default_etiqueta_analitica': self.analytic_tag_ids[0].id if len(self.analytic_tag_ids)>0 else False,
		}
		return {
            'name': 'Agregar Linea',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move.wizard.add.linea',
            'target': 'new',
            'context': data
		}


class account_move(models.Model):
	_inherit= 'account.move'
	_name = "account.move"

	def _get_move_from_lines(self, cr, uid, ids, context=None):
		line_obj = self.pool.get('account.move.line')
		return [line.move_id.id for line in line_obj.browse(cr, uid, ids, context=context)]


	@api.multi
	def button_add_linea(self):
		return {
            'name': 'Agregar Linea',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move.wizard.add.linea',
            'target': 'new',
            'context': {'active_ids':[self.id]},
		}


	@api.multi
	def export_excel(self):

		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		if not direccion:
			raise osv.except_osv('Alerta!', "No fue configurado el directorio para los archivos en Configuración.")
		workbook = Workbook( direccion + 'tempo_account_move_line.xlsx')
		worksheet = workbook.add_worksheet("Asiento Contable")
		bold = workbook.add_format({'bold': True})
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		bord = workbook.add_format()
		bord.set_border(style=1)
		numberdos.set_border(style=1)
		numbertres.set_border(style=1)			
		x= 6				
		tam_col = [12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tam_letra = 1.1
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		worksheet.write(0,0, "Asiento Contable:", bold)

		worksheet.write(0,1, self.name, normal)

		worksheet.write(1,0, "Diario:", bold)

		worksheet.write(1,1, self.journal_id.name, normal)
	
	
		worksheet.write(3,0, "Empresa:",bold)
		
		worksheet.write(3,1, self.partner_id.name if self.partner_id.name else '', normal)
		

		worksheet.write(1,2, "Referencia:", bold)
		
		worksheet.write(1,3, self.ref if self.ref else "", normal)
		

		worksheet.write(2,2, "Fecha:", bold)
		
		worksheet.write(2,3, self.date if self.date else "", normal)
		





		worksheet.write(5,1, "Nombre",boldbord)
		worksheet.write(5,2, "Empresa",boldbord)
		worksheet.write(5,3, "Comprobante",boldbord)
		worksheet.write(5,4, "Cuenta",boldbord)
		worksheet.write(5,5, "Fecha V.",boldbord)
		worksheet.write(5,6, "Debe",boldbord)
		worksheet.write(5,7, "Haber",boldbord)
		worksheet.write(5,8, u"Cta. Analítica",boldbord)
		worksheet.write(5,9, u"Importe Divisa",boldbord)
		worksheet.write(5,10, "Divisa",boldbord)
		worksheet.write(5,11, "Cuenta Impuesto",boldbord)
		worksheet.write(5,12, u"Importe Impuestos",boldbord)
		worksheet.write(5,13, u"Tipo Cambio Sunat",boldbord)
		worksheet.write(5,14, "Tipo Documento",boldbord)
		worksheet.write(5,15, u"Conciliar",boldbord)

		dict_state = {'draft':'Descuadrado','valid':'Cuadrado'}
		for line in self.line_ids:
			worksheet.write(x,1,line.name if line.name  else '',bord )
			worksheet.write(x,2,line.partner_id.name if line.partner_id.name  else '',bord)
			worksheet.write(x,3,line.nro_comprobante if line.nro_comprobante  else '',bord)
			worksheet.write(x,4,line.account_id.code if line.account_id.code  else '',bord)
			worksheet.write(x,5,line.date_maturity if line.date_maturity  else '',bord)
			worksheet.write(x,6,line.debit ,numberdos)
			worksheet.write(x,7,line.credit,numberdos)
			worksheet.write(x,8,line.analytic_account_id.name if line.analytic_account_id.name  else '',bord)
			worksheet.write(x,9,line.amount_currency,bord)
			worksheet.write(x,10,line.currency_id.name if line.currency_id.name  else '',bord)
			worksheet.write(x,11,line.tax_code_id.name if line.tax_code_id.name  else '',bord)
			worksheet.write(x,12,line.tax_amount,numberdos)
			worksheet.write(x,13,line.tc,numbertres)
			worksheet.write(x,14,line.type_document_it.code if line.type_document_it.code  else '',bord)
			worksheet.write(x,15,str(line.full_reconcile_id.name) if line.full_reconcile_id.id  else '',bord)


			x = x +1

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


		workbook.close()
		
		f = open( direccion + 'tempo_account_move_line.xlsx', 'rb')
		
		vals = {
			'output_name': 'AsientoContable.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		sfs_id = self.env['export.file.save'].create(vals)

		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id.id,
		    "target": "new",
		}



class account_move_wizard_add_linea(models.TransientModel):
	_name = 'account.move.wizard.add.linea'

	currency_id = fields.Many2one('res.currency','Moneda')
	account_id = fields.Many2one('account.account','Cuenta')
	type_change = fields.Float('Tipo Cambio',digits=(12,3))
	import_divisa = fields.Float('Importe Divisa', digits=(12,2))
	glosa = fields.Char('Glosa',size=200)
	debit = fields.Float('Debe', digits=(12,2))
	credit = fields.Float('Haber', digits=(12,2))
	analytic_id = fields.Many2one('account.analytic.account','Cta. Analítica')



	is_pago  = fields.Boolean('Se esta registrando un pago')
	comprobante_auto = fields.Many2one('account.move.comprobante','Número Comprobante')
	comprobante_manual = fields.Char('Número Comprobante',size=200)
	empresa = fields.Many2one('res.partner','Empresa')

	type_doc_id = fields.Many2one('einvoice.catalog.01','Tipo Documento')
	impuesto = fields.Many2one('account.tax.code','Impuesto')
	importe_impuesto = fields.Float('Importe Impuesto/Base', digits=(12,2))
	date_vencimiento = fields.Date('Fecha Vencimiento')

	rendicion_id = fields.Many2one('account.rendicion.it','Rendicion')



	product_id = fields.Many2one('product.product', 'Producto')
	cantidad = fields.Float('Cantidad')
	uom_id = fields.Many2one('product.uom', 'Unidad')
	precio_unitario = fields.Float(string='P.Unit')
	etiqueta_analitica = fields.Many2one('account.analytic.tag', string='Etiqueta Analitica')
	#comprobante_manual = fields.Many2one('einvoice.catalog.01', 'Numero de Comprobante')


	@api.onchange('comprobante_manual','type_doc_id')
	def onchange_suplier_invoice_number_it(self):
		if self.comprobante_manual:
			self.comprobante_manual = str(self.comprobante_manual).replace(' ','')
			
			if self.comprobante_manual and self.type_doc_id.id:
				self.comprobante_manual = str(self.comprobante_manual).replace(' ','')
				t = self.comprobante_manual.split('-')
				n_serie = 0
				n_documento = 0
				self.env.cr.execute("select coalesce(n_serie,0), coalesce(n_documento,0) from einvoice_catalog_01 where id = "+ str(self.type_doc_id.id))
				
				forelemn = self.env.cr.fetchall()
				for ielem in forelemn:
					n_serie = ielem[0]
					n_documento = ielem[1]
				if len(t) == 2:
					parte1= t[0]
					if len(t[0]) < n_serie:
						for i in range(0,n_serie-len(t[0])):
							parte1 = '0'+parte1
					parte2= t[1]
					if len(t[1]) < n_documento:
						for i in range(0,n_documento-len(t[1])):
							parte2 = '0'+parte2
					self.comprobante_manual = parte1 + '-' + parte2
				elif len(t) == 1:
					parte2= t[0]
					if len(t[0]) < n_documento:
						for i in range(0,n_documento-len(t[0])):
							parte2 = '0'+parte2
					self.comprobante_manual = parte2
				else:
					pass

	@api.onchange('debit')
	def onchange_debit(self):
		if self.debit==0:
			return
		self.credit=0

	@api.onchange('credit')
	def onchange_credit(self):
		if self.credit==0:
			return
		self.debit=0


	@api.onchange('type_change','currency_id','import_divisa')
	def onchange_type_change_currency(self):
		if self.currency_id.id:
			if self.import_divisa > 0:
				self.debit = float("%0.2f"% ( (self.import_divisa) * float(self.type_change) ))
				self.credit = 0
			elif self.import_divisa < 0 :
				self.credit = float("%0.2f"% ( (-self.import_divisa) * float(self.type_change) ))
				self.debit = 0
			else:
				self.credit = 0
				self.debit = 0

	@api.multi
	def do_rebuild(self):
		if 'active_ids_line' in self._context:
			tt = self._context['active_ids_line']

			comprobante = self.comprobante_manual if self.is_pago == False else self.comprobante_auto.name
			data = {
				'name':self.glosa,
				'partner_id': self.empresa.id,
				'nro_comprobante': comprobante if comprobante else '',
				'account_id':self.account_id.id,
				'date_maturity': self.date_vencimiento,
				'debit': self.debit,
				'credit':self.credit,
				'analytic_account_id': self.analytic_id.id,
				'amount_currency': self.import_divisa,
				'currency_id': self.currency_id.id,
				'tax_code_id':self.impuesto.id,
				'tax_amount':self.importe_impuesto,
				'tc':self.type_change,
				'type_document_it':self.type_doc_id.id,
				'rendicion_id':self.rendicion_id.id,
				'product_id': self.product_id.id,
				'product_uom_id':self.uom_id.id,
				'quantity':self.cantidad,
				'analytic_tag_ids': [(6,0,[self.etiqueta_analitica.id])] if self.etiqueta_analitica.id else [(6,0,[])],
			}
			obj_linea = self.env['account.move.line'].search([('id','=',tt)])[0].write(data)
			return True

		t = self._context['active_ids']
		if len(t)>1:
			raise osv.except_osv('Alerta!', "Solo debe seleccionar 1 Asiento Contable.")
		m = self.env['account.move'].search([('id','=',t[0])])[0]
		if m.state != 'draft':
			raise osv.except_osv('Alerta!', "Solo se puede agregar si el Asiento Contable esta en borrador.")


		comprobante = self.comprobante_manual if self.is_pago == False else self.comprobante_auto.name
		data = {
			'name':self.glosa,
			'partner_id': self.empresa.id,
			'nro_comprobante': comprobante if comprobante else '',
			'account_id':self.account_id.id,
			'date_maturity': self.date_vencimiento,
			'debit': self.debit,
			'credit':self.credit,
			'analytic_account_id': self.analytic_id.id,
			'amount_currency': self.import_divisa,
			'currency_id': self.currency_id.id,
			'tax_code_id':self.impuesto.id,
			'tax_amount':self.importe_impuesto,
			'tc':self.type_change,
			'type_document_it':self.type_doc_id.id,
			'rendicion_id':self.rendicion_id.id,
			'move_id':m.id,
			'product_id': self.product_id.id,
			'product_uom_id':self.uom_id.id,
			'quantity':self.cantidad,		
		}
		j = self.env['account.move.line'].create(data)
		if self.etiqueta_analitica.id:
			j.write({'analytic_tag_ids': [(6,0,[self.etiqueta_analitica.id])]})
		else:
			j.write({'analytic_tag_ids': [(6,0,[])]})

		m.write({'line_ids': [(4,j.id)]})

		return True











class account_move_pdf(osv.TransientModel):
	_name = 'account.move.pdf'


	@api.multi
	def do_rebuild(self):
		
		if 'active_ids' in self.env.context:
			obj_move = self.env['account.move'].search([('id','=',self.env.context['active_ids'][0])])[0]

			self.reporteador(obj_move)
			
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			import os

			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			vals = {
				'output_name': 'AsientoContable.pdf',
				'output_file': open(direccion + "AsientoContable.pdf", "rb").read().encode("base64"),	
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
	def cabezera(self,c,wReal,hReal,obj_move,titulo):

		c.setFont("Calibri-Bold", 10)
		c.setFillColor(black)
		c.drawCentredString((wReal/2)+20,hReal, self.env["res.company"].search([])[0].name.upper())
		c.drawCentredString((wReal/2)+20,hReal-12, "ASIENTO CONTABLE: "+ obj_move.name + " - " + obj_move.journal_id.name )

		c.setFont("Calibri-Bold", 8)

		c.drawString( 10,hReal-48, 'Empresa:')
		c.drawString( 400,hReal-36, 'Referencia:')
		c.drawString( 400,hReal-48, 'Fecha:')


		c.setFont("Calibri", 8)
		c.drawString( 10+90,hReal-48, obj_move.partner_id.name if obj_move.partner_id.name else '')
		c.drawString( 400+60,hReal-36, obj_move.ref if obj_move.ref else '')
		c.drawString( 400+60,hReal-48, obj_move.date if obj_move.date else '')


		style = getSampleStyleSheet()["Normal"]
		style.leading = 8
		style.alignment= 1
		paragraph1 = Paragraph(
		    "<font size=8><b>Nombre</b></font>",
		    style
		)
		paragraph2 = Paragraph(
		    "<font size=8><b>Empresa</b></font>",
		    style
		)
		paragraph3 = Paragraph(
		    "<font size=8><b>Comprobante</b></font>",
		    style
		)
		paragraph4 = Paragraph(
		    "<font size=8><b>Cuenta</b></font>",
		    style
		)
		paragraph5 = Paragraph(
		    "<font size=8><b>Fecha V.</b></font>",
		    style
		)
		paragraph6 = Paragraph(
		    "<font size=8><b>Debe</b></font>",
		    style
		)
		paragraph7 = Paragraph(
		    "<font size=8><b>Haber</b></font>",
		    style
		)
		paragraph8 = Paragraph(
		    "<font size=8><b>Cta. Analítica</b></font>",
		    style
		)
		paragraph9 = Paragraph(
		    "<font size=8><b>Importe Divisa</b></font>",
		    style
		)
		paragraph10 = Paragraph(
		    "<font size=8><b>Divisa</b></font>",
		    style
		)
		paragraph11 = Paragraph(
		    "<font size=8><b>TC SUNAT</b></font>",
		    style
		)
		paragraph12 = Paragraph(
		    "<font size=8><b>TD</b></font>",
		    style
		)

		paragraph13 = Paragraph(
		    "<font size=8><b>Cuenta</b></font>",
		    style
		)
		paragraph14 = Paragraph(
		    "<font size=8><b>Descripción</b></font>",
		    style
		)
		paragraph15 = Paragraph(
		    "<font size=8><b>Debe</b></font>",
		    style
		)
		paragraph16 = Paragraph(
		    "<font size=8><b>Haber</b></font>",
		    style
		)

		if titulo == 1:
			data= [[ paragraph1 , paragraph2 , paragraph3 , paragraph4, paragraph5 , paragraph6 , paragraph7 ,paragraph12]]
			t=Table(data,colWidths=( 80,120, 80, 90, 50,60,60,25), rowHeights=(9))
			t.setStyle(TableStyle([
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri-Bold'),
				('FONTSIZE',(0,0),(-1,-1),4),
				('BACKGROUND', (0, 0), (-1, -1), colors.gray)
			]))
		elif titulo == 2:
			data= [[ paragraph8 ,paragraph9,paragraph10,paragraph11]]
			t=Table(data,colWidths=(100,100,50,60), rowHeights=(9))
			t.setStyle(TableStyle([
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri-Bold'),
				('FONTSIZE',(0,0),(-1,-1),4),
				('BACKGROUND', (0, 0), (-1, -1), colors.gray)
			]))
		else:
			data= [[ paragraph13 ,paragraph14,paragraph15,paragraph16]]
			t=Table(data,colWidths=(70,130,60,60), rowHeights=(9))
			t.setStyle(TableStyle([
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri-Bold'),
				('FONTSIZE',(0,0),(-1,-1),4),
				('BACKGROUND', (0, 0), (-1, -1), colors.gray)
			]))


		t.wrapOn(c,20,500)
		t.drawOn(c,20,hReal-85)

	@api.multi
	def x_aument(self,a):
		a[0] = a[0]+1

	@api.multi
	def reporteador(self,obj_move):

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')


		pdfmetrics.registerFont(TTFont('Calibri', 'Calibri.ttf'))
		pdfmetrics.registerFont(TTFont('Calibri-Bold', 'CalibriBold.ttf'))

		width ,height  = A4  # 595 , 842
		wReal = width- 30
		hReal = height - 40

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas( direccion + "AsientoContable.pdf", pagesize= A4 )
		inicio = 0
		pos_inicial = hReal-83
		libro = None
		voucher = None
		total = 0
		debeTotal = 0
		haberTotal = 0
		pagina = 1
		textPos = 0
		
		self.cabezera(c,wReal,hReal,obj_move,1)


		posicion_indice = 1

		for i in obj_move.line_ids:
			c.setFont("Calibri", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina,1,obj_move)
			
			c.drawString( 10 ,pos_inicial, str(posicion_indice) )
			c.drawString( 22 ,pos_inicial, self.particionar_text( i.name,70) )
			c.drawString( 102 ,pos_inicial, self.particionar_text( i.partner_id.name if i.partner_id.id else '',100) )
			c.drawString( 222 ,pos_inicial,self.particionar_text( i.nro_comprobante if i.nro_comprobante else '',70) )
			c.drawString( 302 ,pos_inicial,self.particionar_text( (i.account_id.code + ' - ' + i.account_id.name) if i.account_id.id else '',75) )
			c.drawString( 392 ,pos_inicial,self.particionar_text( i.date_maturity if i.date_maturity else '',40) )
			c.drawRightString( 498 ,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.debit)))
			c.drawRightString( 558 ,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.credit)))
			c.drawString( 562 ,pos_inicial,self.particionar_text( i.type_document_it.code if i.type_document_it.id else '',20) )

			c.line( 20, pos_inicial-2, 585 ,pos_inicial-2)

			tamanios_x = [80,120, 80, 90, 50,60,60,25]

			acum_tx = 20
			for i in tamanios_x:
				c.line( acum_tx, pos_inicial-2, acum_tx ,pos_inicial+12)
				acum_tx += i
			c.line( acum_tx, pos_inicial-2, acum_tx ,pos_inicial+12)

			posicion_indice += 1



		posicion_indice= 1



		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,36,pagina,2,obj_move)



		style = getSampleStyleSheet()["Normal"]
		style.leading = 8
		style.alignment= 1
		paragraph1 = Paragraph(
		    "<font size=8><b>Nombre</b></font>",
		    style
		)
		paragraph2 = Paragraph(
		    "<font size=8><b>Empresa</b></font>",
		    style
		)
		paragraph3 = Paragraph(
		    "<font size=8><b>Comprobante</b></font>",
		    style
		)
		paragraph4 = Paragraph(
		    "<font size=8><b>Cuenta</b></font>",
		    style
		)
		paragraph5 = Paragraph(
		    "<font size=8><b>Fecha V.</b></font>",
		    style
		)
		paragraph6 = Paragraph(
		    "<font size=8><b>Debe</b></font>",
		    style
		)
		paragraph7 = Paragraph(
		    "<font size=8><b>Haber</b></font>",
		    style
		)
		paragraph8 = Paragraph(
		    "<font size=8><b>Cta. Analítica</b></font>",
		    style
		)
		paragraph9 = Paragraph(
		    "<font size=8><b>Importe Divisa</b></font>",
		    style
		)
		paragraph10 = Paragraph(
		    "<font size=8><b>Divisa</b></font>",
		    style
		)
		paragraph11 = Paragraph(
		    "<font size=8><b>TC SUNAT</b></font>",
		    style
		)
		paragraph12 = Paragraph(
		    "<font size=8><b>TD</b></font>",
		    style
		)

		data= [[ paragraph8 ,paragraph9,paragraph10,paragraph11]]
		t=Table(data,colWidths=(100,100,50,60), rowHeights=(9))
		t.setStyle(TableStyle([
			('GRID',(0,0),(-1,-1), 1, colors.black),
			('ALIGN',(0,0),(-1,-1),'LEFT'),
			('VALIGN',(0,0),(-1,-1),'MIDDLE'),
			('TEXTFONT', (0, 0), (-1, -1), 'Calibri-Bold'),
			('FONTSIZE',(0,0),(-1,-1),4),
			('BACKGROUND', (0, 0), (-1, -1), colors.gray)
		]))

		t.wrapOn(c,20,pos_inicial)
		t.drawOn(c,20,pos_inicial)


		for i in obj_move.line_ids:
			c.setFont("Calibri", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina,2,obj_move)
			
			c.drawString( 10 ,pos_inicial, str(posicion_indice) )
			c.drawString( 22 ,pos_inicial,self.particionar_text( i.analytic_account_id.name if i.analytic_account_id.id else '', 43) )
			c.drawRightString( 218 ,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.amount_currency)))
			c.drawString( 222 ,pos_inicial,self.particionar_text( i.currency_id.name if i.currency_id.id else '',24) )
			c.drawRightString( 328 ,pos_inicial, "%0.3f" % i.tc)
			
			c.line( 20, pos_inicial-2, 330 ,pos_inicial-2)


			tamanios_x = [100,100,50,60]

			acum_tx = 20
			for i in tamanios_x:
				c.line( acum_tx, pos_inicial-2, acum_tx ,pos_inicial+12)
				acum_tx += i
			c.line( acum_tx, pos_inicial-2, acum_tx ,pos_inicial+12)

			posicion_indice += 1
		
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina,2,obj_move)






		c.drawString( 10 ,pos_inicial, 'HECHO POR:' )
		c.drawString( 60 ,pos_inicial, obj_move.create_uid.name if obj_move.create_uid.id else self.env.uid.name )


		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,50,pagina,3,obj_move)

		c.line( 125-47, pos_inicial+10, 125+47 ,pos_inicial+10)
		c.line( 290-47, pos_inicial+10, 290+47 ,pos_inicial+10)
		c.line( 165+290-47, pos_inicial+10, 165+290+47 ,pos_inicial+10)
		c.drawCentredString( 125 ,pos_inicial, 'HECHO POR:' )
		c.drawCentredString( 165+290 ,pos_inicial, 'REVISADO:' )
		c.drawCentredString( 290 ,pos_inicial, 'APROBADO:' )

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
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,titulo,obj_move):
		if posactual <40:
			c.showPage()
			self.cabezera(c,wReal,hReal,obj_move,titulo)

			c.setFont("Calibri-Bold", 8)
			#c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-83
		else:
			return pagina,posactual-valor