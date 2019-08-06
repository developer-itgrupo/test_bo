# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
from datetime import *
from odoo.exceptions import UserError, ValidationError

class account_analytic_book_major_wizard(osv.TransientModel):
	_name='account.analytic.book.major.wizard'
	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end = fields.Many2one('account.period','Periodo Final',required=True)
	asientos =  fields.Selection([('posted','Asentados'),('draft','No Asentados'),('both','Ambos')], 'Asientos')
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('csv','CSV')], 'Mostrar en', required=True)
	cuentas = fields.Many2many('account.account','account_book_major_account_rel','id_book_origen','id_account_destino', string='Cuentas', required=True)
	
	@api.model
	def get_wizard(self):
		return self.env['automatic.fiscalyear'].get_wizard('Libro Mayor Analitico',self.id,'account.analytic.book.major.wizard','account_mayor_it.view_account_analytic_book_major_wizard_form','default_period_ini','default_period_end')

	@api.model
	def get_wizard_w(self):
		t = self.env['automatic.fiscalyear'].get_wizard('Libro Mayor Analitico',self.id,'account.analytic.book.major.wizard','account_mayor_it.view_account_analytic_book_major_wizard_form','default_period_ini','default_period_end')
		t['context'] = t['context'] if 'context' in t else {}
		t['context']['default_cuentas'] = [(6,0,self.env.context['opt'])]
		return t

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

	_defaults={
		'local': 'roca',
	}

	@api.multi
	def do_rebuild(self):
		period_ini = self.period_ini
		period_end = self.period_end
		
		filtro = []
				
		self.env.cr.execute("""
			CREATE OR REPLACE view account_analytic_book_major as (SELECT * FROM get_libro_mayor(periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""')) 
		)""")

		if self.cuentas:
			libros_list = ["Saldo Inicial"]
			for i in  self.cuentas:
				libros_list.append(i.code)
			filtro.append( ('cuenta','in',tuple(libros_list)) )

		#DSC_Exportar a CSV por el numero de filas
		self.env.cr.execute("""select count(*)  from account_analytic_book_major""")
		rows = self.env.cr.fetchone()
		#if self.type_show == 'excel' and rows[0] > 1000:
		#	self.type_show = 'csv'
		
		if self.type_show == 'pantalla':
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.analytic.book.major',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}
		
		#DSC_
		if self.type_show == 'csv':
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			docname = 'LibroMayor.csv'
			#CSV
			sql_query = """	COPY (SELECT * FROM account_analytic_book_major )TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
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
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			workbook = Workbook(direccion +'tempo_libromayor.xlsx')
			worksheet = workbook.add_worksheet("Libro Mayor")
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
			bord.set_text_wrap()
			numberdos.set_border(style=1)
			numbertres.set_border(style=1)			
			x= 4				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.write(0,0, "Libro Mayor:".upper(), bold)
			tam_col[0] = tam_letra* len("Libro Mayor:") if tam_letra* len("Libro Mayor:")> tam_col[0] else tam_col[0]

			worksheet.write(0,1, self.period_ini.name, normal)
			tam_col[1] = tam_letra* len(self.period_ini.name) if tam_letra* len(self.period_ini.name)> tam_col[1] else tam_col[1]

			worksheet.write(0,2, self.period_end.name, normal)
			tam_col[2] = tam_letra* len(self.period_end.name) if tam_letra* len(self.period_end.name)> tam_col[2] else tam_col[2]

			worksheet.write(1,0, "Fecha:".upper(),bold)
			tam_col[0] = tam_letra* len("Fecha:") if tam_letra* len("Fecha:")> tam_col[0] else tam_col[0]

			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			import datetime
			worksheet.write(1,1, str(datetime.datetime.today())[:10], normal)
			tam_col[1] = tam_letra* len(str(datetime.datetime.today())[:10]) if tam_letra* len(str(datetime.datetime.today())[:10])> tam_col[1] else tam_col[1]
			

			worksheet.write(3,0, "Periodo",boldbord)
			tam_col[0] = tam_letra* len("Periodo") if tam_letra* len("Periodo")> tam_col[0] else tam_col[0]
			worksheet.write(3,1, "Libro",boldbord)
			tam_col[1] = tam_letra* len("Libro") if tam_letra* len("Libro")> tam_col[1] else tam_col[1]
			worksheet.write(3,2, "Voucher",boldbord)
			tam_col[2] = tam_letra* len("Voucher") if tam_letra* len("Voucher")> tam_col[2] else tam_col[2]
			worksheet.write(3,3, "Cuenta",boldbord)
			tam_col[3] = tam_letra* len("Cuenta") if tam_letra* len("Cuenta")> tam_col[3] else tam_col[3]
			worksheet.write(3,4, u"Descripción",boldbord)
			tam_col[4] = tam_letra* len(u"Descripción") if tam_letra* len(u"Descripción")> tam_col[4] else tam_col[4]
			worksheet.write(3,5, "Debe",boldbord)
			tam_col[5] = tam_letra* len("Debe") if tam_letra* len("Debe")> tam_col[5] else tam_col[5]
			worksheet.write(3,6, "Haber",boldbord)
			tam_col[6] = tam_letra* len("Haber") if tam_letra* len("Haber")> tam_col[6] else tam_col[6]
			worksheet.write(3,7, "Saldo",boldbord)
			tam_col[7] = tam_letra* len("Saldo") if tam_letra* len("Saldo")> tam_col[7] else tam_col[7]
			worksheet.write(3,8, "Divisa",boldbord)
			tam_col[8] = tam_letra* len("Divisa") if tam_letra* len("Divisa")> tam_col[8] else tam_col[8]
			worksheet.write(3,9, "Tipo Cambio",boldbord)
			tam_col[9] = tam_letra* len("Tipo Cambio") if tam_letra* len("Tipo Cambio")> tam_col[9] else tam_col[9]
			worksheet.write(3,10, "Importe Divisa",boldbord)
			tam_col[10] = tam_letra* len("Importe Divisa") if tam_letra* len("Importe Divisa")> tam_col[10] else tam_col[10]
			worksheet.write(3,11, u"Conciliación",boldbord)
			tam_col[11] = tam_letra* len(u"Conciliación") if tam_letra* len(u"Conciliación")> tam_col[11] else tam_col[11]
			worksheet.write(3,12, u"Analítica",boldbord)
			tam_col[12] = tam_letra* len(u"Analítica") if tam_letra* len(u"Analítica")> tam_col[12] else tam_col[12]
			worksheet.write(3,13, u"Fecha Emisión",boldbord)
			tam_col[13] = tam_letra* len(u"Fecha Emisión") if tam_letra* len(u"Fecha Emisión")> tam_col[13] else tam_col[13]
			worksheet.write(3,14, "Fecha Vencimiento",boldbord)
			tam_col[14] = tam_letra* len("Fecha Vencimiento") if tam_letra* len("Fecha Vencimiento")> tam_col[14] else tam_col[14]
			worksheet.write(3,15, "Tipo Documento",boldbord)
			tam_col[15] = tam_letra* len("Tipo Documento") if tam_letra* len("Tipo Documento")> tam_col[15] else tam_col[15]
			worksheet.write(3,16, u"Número",boldbord)
			tam_col[16] = tam_letra* len(u"Número") if tam_letra* len(u"Número")> tam_col[16] else tam_col[16]
			worksheet.write(3,17, u"RUC",boldbord)
			tam_col[17] = tam_letra* len(u"RUC") if tam_letra* len(u"RUC")> tam_col[17] else tam_col[17]
			worksheet.write(3,18, u"Partner",boldbord)
			tam_col[18] = tam_letra* len(u"Partner") if tam_letra* len(u"Partner")> tam_col[18] else tam_col[18]
			worksheet.write(3,19, u"Glosa",boldbord)
			tam_col[19] = tam_letra* len(u"Glosa") if tam_letra* len(u"Glosa")> tam_col[19] else tam_col[19]

			cuenta_ant = "None"
			saldo_acum = 0
			for line in self.env['account.analytic.book.major'].search(filtro):
				if cuenta_ant == "None":
					cuenta_ant = line.cuenta

				if cuenta_ant != line.cuenta:
					cuenta_ant = line.cuenta
					saldo_acum = 0
				
				saldo_acum += line.debe - line.haber
				
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.libro if line.libro  else '',bord )
				worksheet.write(x,2,line.voucher if line.voucher  else '',bord)
				worksheet.write(x,3,line.cuenta if line.cuenta  else '',bord)
				worksheet.write(x,4,line.descripcion if line.descripcion  else '',bord)
				worksheet.write(x,5,line.debe ,numberdos)
				worksheet.write(x,6,line.haber ,numberdos)
				worksheet.write(x,7,saldo_acum ,numberdos)
				worksheet.write(x,8,line.divisa if  line.divisa else '',bord)
				worksheet.write(x,9,line.tipocambio ,numbertres)
				worksheet.write(x,10,line.importedivisa ,numberdos)
				worksheet.write(x,11,line.conciliacion if line.conciliacion else '',bord)
				worksheet.write(x,12,line.analitica if line.analitica else '',bord)
				worksheet.write(x,13,line.fechaemision if line.fechaemision else '',bord)
				worksheet.write(x,14,line.fechavencimiento if line.fechavencimiento else '',bord)
				worksheet.write(x,15,line.tipodocumento if line.tipodocumento else '',bord)
				worksheet.write(x,16,line.numero if line.numero  else '',bord)				
				worksheet.write(x,17,line.ruc if line.ruc  else '',bord)
				worksheet.write(x,18,line.partner.upper() if line.partner  else '',bord)
				worksheet.write(x,19,line.glosa if line.glosa else '',bord)

				tam_col[0] = tam_letra* len(line.periodo if line.periodo else '' ) if tam_letra* len(line.periodo if line.periodo else '' )> tam_col[0] else tam_col[0]
				tam_col[1] = tam_letra* len(line.libro if line.libro  else '') if tam_letra* len(line.libro if line.libro  else '')> tam_col[1] else tam_col[1]
				tam_col[2] = tam_letra* len(line.voucher if line.voucher  else '') if tam_letra* len(line.voucher if line.voucher  else '')> tam_col[2] else tam_col[2]
				tam_col[3] = tam_letra* len(line.cuenta if line.cuenta  else '') if tam_letra* len(line.cuenta if line.cuenta  else '')> tam_col[3] else tam_col[3]
				tam_col[4] = tam_letra* len(line.descripcion if line.descripcion  else '') if tam_letra* len(line.descripcion if line.descripcion  else '')> tam_col[4] else tam_col[4]
				tam_col[5] = tam_letra* len("%0.2f"%line.debe ) if tam_letra* len("%0.2f"%line.debe )> tam_col[5] else tam_col[5]
				tam_col[6] = tam_letra* len("%0.2f"%line.haber ) if tam_letra* len("%0.2f"%line.haber )> tam_col[6] else tam_col[6]
				tam_col[7] = tam_letra* len("%0.2f"%line.saldo ) if tam_letra* len("%0.2f"%line.saldo )> tam_col[7] else tam_col[7]
				tam_col[8] = tam_letra* len(line.divisa if  line.divisa else '') if tam_letra* len(line.divisa if  line.divisa else '')> tam_col[8] else tam_col[8]
				tam_col[9] = tam_letra* len("%0.3f"%line.tipocambio ) if tam_letra* len("%0.3f"%line.tipocambio )> tam_col[9] else tam_col[9]
				tam_col[10] = tam_letra* len("%0.2f"%line.importedivisa ) if tam_letra* len("%0.2f"%line.importedivisa )> tam_col[10] else tam_col[10]
				tam_col[11] = tam_letra* len(line.conciliacion if line.conciliacion else '') if tam_letra* len(line.conciliacion if line.conciliacion else '')> tam_col[11] else tam_col[11]
				tam_col[12] = tam_letra* len(line.analitica if line.analitica else '') if tam_letra* len(line.analitica if line.analitica else '')> tam_col[12] else tam_col[12]
				tam_col[13] = tam_letra* len(line.fechaemision if line.fechaemision else '') if tam_letra* len(line.fechaemision if line.fechaemision else '')> tam_col[13] else tam_col[13]
				tam_col[14] = tam_letra* len(line.fechavencimiento if line.fechavencimiento else '') if tam_letra* len(line.fechavencimiento if line.fechavencimiento else '')> tam_col[14] else tam_col[14]
				tam_col[15] = tam_letra* len(line.tipodocumento if line.tipodocumento else '') if tam_letra* len(line.tipodocumento if line.tipodocumento else '')> tam_col[15] else tam_col[15]
				tam_col[16] = tam_letra* len(line.numero if line.numero  else '') if tam_letra* len(line.numero if line.numero  else '')> tam_col[16] else tam_col[16]
				tam_col[17] = tam_letra* len(line.ruc if line.ruc  else '') if tam_letra* len(line.ruc if line.ruc  else '')> tam_col[17] else tam_col[17]
				tam_col[18] = tam_letra* len(line.partner if line.partner  else '') if tam_letra* len(line.partner if line.partner  else '')> tam_col[18] else tam_col[18]
				tam_col[19] = tam_letra* len(line.glosa if line.glosa else '') if tam_letra* len(line.glosa if line.glosa else '')> tam_col[19] else tam_col[19]

				x = x +1

			tam_col = [13,7,9,8,45,11,11,11,10,11,14,10,11,14,14,10,16,16,45,36]


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
			
			f = open(direccion + 'tempo_libromayor.xlsx', 'rb')
			
			
			vals = {
				'output_name': 'LibroMayor.xlsx',
				'output_file': base64.encodestring(''.join(f.readlines())),		
			}

			sfs_id = self.env['export.file.save'].create(vals)

			#import os
			#os.system('c:\\eSpeak2\\command_line\\espeak.exe -ves-f1 -s 170 -p 100 "Se Realizo La exportación exitosamente Y A EDWARD NO LE GUSTA XDXDXDXDDDDDDDDDDDD" ')

			return {
			    "type": "ir.actions.act_window",
			    "res_model": "export.file.save",
			    "views": [[False, "form"]],
			    "res_id": sfs_id.id,
			    "target": "new",
			}
		
