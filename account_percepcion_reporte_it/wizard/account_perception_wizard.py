# -*- encoding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint
from datetime import *
from odoo.exceptions import UserError, ValidationError

class account_perception_p_wizard(osv.TransientModel):
	_name='account.perception.p.wizard'

	tipo = fields.Selection([('excel','Excel'),('txt','Txt')], 'Mostrar',required=True)
	

	@api.multi
	def do_rebuild(self):		
		parametros = (self.env['main.parameter'].search([])[0]).account_perception_tipo_documento.code

		filtro = [('id','in', self.env.context['active_ids']),('tipo_doc','=','00')]

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		if self.tipo == 'txt':

			Str_csv = self.env['account.perception.report'].search(filtro).mapped(lambda r: self.csv_convert(r,'|'))
			rpta = ""
		
			for i in Str_csv:
				rpta += i.encode('iso-8859-1','ignore') + "\r\n"

			#code = '0601'
			#periodo = period_ini.code
			#periodo = periodo.split('/')
			#name = periodo[1]+periodo[0]
			user = self.env['res.users'].browse(self.env.uid)

			if user.company_id.id == False:
				raise osv.except_osv('Alerta','El usuario actual no tiene una compañia asignada. Contacte a su administrador.')
			if user.company_id.partner_id.id == False:
				raise osv.except_osv('Alerta','La compañia del usuario no tiene una empresa asignada. Contacte a su administrador.')
			if user.company_id.partner_id.nro_documento == False:
				raise osv.except_osv('Alerta','La compañia del usuario no tiene un numero de documento. Contacte a su administrador.')

			ruc = user.company_id.partner_id.nro_documento

			#obj_analizar = self.env['account.perception.report'].search(filtro)[0]
			
			obj_analizar = self.env['account.perception.report'].search(filtro)
			if len(obj_analizar) >0:
				obj_analizar = obj_analizar[0]
			else:
				raise osv.except_osv('alerta','No existen comprobantes de percepcion para el periodo seleccionado')
			
			
			
			t_t = obj_analizar.periodo
			
			file_name = '0621' + ruc + (t_t[3:8] + t_t[:2]) +'P.txt'	


			vals = {
				'output_name': file_name,
				'output_file': base64.encodestring(rpta),	
				'respetar':1,	
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

			workbook = Workbook(direccion +'tempo_peception.xlsx')
			worksheet = workbook.add_worksheet("Perception P")

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
			
			numberdosbold = workbook.add_format({'num_format':'0.00','bold': True})
			bord = workbook.add_format()
			bord.set_border(style=1)
			numberdos.set_border(style=1)
			numbertres.set_border(style=1)          
			x= 4
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.write(0,0, u"Percepción", bold)
			
			worksheet.write(3,0, "Libro",boldbord)
			worksheet.write(3,1, "Voucher",boldbord)
			worksheet.write(3,2, "RUC",boldbord)
			worksheet.write(3,3, "Serie",boldbord)
			worksheet.write(3,4, u"Número",boldbord)
			worksheet.write(3,5, "Fecha",boldbord)
			worksheet.write(3,6, u"Percepción",boldbord)
			worksheet.write(3,7, "Tipo Doc P.",boldbord)
			worksheet.write(3,8, "Serie P.",boldbord)
			worksheet.write(3,9, "Numero P.",boldbord)
			worksheet.write(3,10, "Fecha P.",boldbord)
			worksheet.write(3,11, u"Monto",boldbord)
			


			for i in self.env['account.perception.report'].search(filtro):

				worksheet.write(x,0, i.libro if i.libro else '' ,bord)
				worksheet.write(x,1, i.voucher if i.voucher else '' ,bord)
				worksheet.write(x,2, i.ruc if i.ruc else '' ,bord)
				worksheet.write(x,3, i.serie if i.serie else '' ,bord)
				worksheet.write(x,4, i.numero if i.numero else '' ,bord)
				worksheet.write(x,5, i.fecha if i.fecha else '' ,bord)
				worksheet.write(x,6, i.percepcion ,numberdos)
				worksheet.write(x,7, i.tipo_doc_2 if i.tipo_doc_2 else '' ,bord)
				worksheet.write(x,8, i.serie_2 if i.serie_2 else '' ,bord)
				worksheet.write(x,9, i.numero_2 if i.numero_2 else '' ,bord)
				worksheet.write(x,10, i.fecha_2 if i.fecha_2 else '' ,bord)
				worksheet.write(x,11, i.monto ,numberdos)
				x +=1
					

			tam_col = [20,20,20,20,20,20,14,20,20,20,20,14,20,20,20,20,20,20,20,14,20,20,20,20,20,20,20,14,20,20,20]


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
			
			f = open(direccion + 'tempo_peception.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'PercepcionP.xlsx',
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
	def csv_verif_integer(self,data):
		if data:
			return "%0.2f"%(data)
		else:
			return '0.00'

	@api.multi
	def csv_verif(self,data):
		if data:
			return data
		else:
			return ''

	@api.multi
	def csv_convert(self,data,separador):

		tmp = self.csv_verif(data.ruc)

		#tmp += separador+ self.csv_verif(data.tipo_doc)
		tmp += separador+ self.csv_verif(data.serie)
		tmp += separador+ self.csv_verif(data.numero)

		fecha_corregida = ''
		if data.fecha:
			fecha_parsiada = data.fecha.split('-')
			fecha_corregida = fecha_parsiada[2] + '/' +  fecha_parsiada[1] + '/'+ fecha_parsiada[0]

		tmp += separador+ self.csv_verif( fecha_corregida)

		tmp += separador+ self.csv_verif_integer(data.percepcion)

		tmp += separador+ self.csv_verif(data.tipo_doc_2)
		tmp += separador+ self.csv_verif(data.serie_2)
		tmp += separador+ self.csv_verif(data.numero_2)


		fecha_corregida = ''
		if data.fecha_2:
			fecha_parsiada = data.fecha_2.split('-')
			fecha_corregida = fecha_parsiada[2] + '/' +  fecha_parsiada[1] + '/'+ fecha_parsiada[0]
		tmp += separador+ self.csv_verif( fecha_corregida)

		tmp += separador+ self.csv_verif_integer(data.monto)

		tmp += separador
		return unicode(tmp)




class account_perception_pi_wizard(osv.TransientModel):
	_name='account.perception.pi.wizard'

	tipo = fields.Selection([('excel','Excel'),('txt','Txt')], 'Mostrar',required=True)
	

	@api.multi
	def do_rebuild(self):


		parametros = (self.env['main.parameter'].search([])[0]).account_perception_tipo_documento.code

		
		filtro = [('id','in', self.env.context['active_ids']),('tipo_doc','!=','00')]

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		if self.tipo == 'txt':
		
			Str_csv = self.env['account.perception.report'].search(filtro).mapped(lambda r: self.csv_convert(r,'|'))
			rpta = ""
			#rpta = self.cabezera_csv('|') + "\n"
			for i in Str_csv:
				rpta += i.encode('iso-8859-1','ignore') + "\r\n"

			#code = '0601'
			#periodo = period_ini.code
			#periodo = periodo.split('/')
			#name = periodo[1]+periodo[0]
			user = self.env['res.users'].browse(self.env.uid)

			if user.company_id.id == False:
				raise osv.except_osv('Alerta','El usuario actual no tiene una compañia asignada. Contacte a su administrador.')
			if user.company_id.partner_id.id == False:
				raise osv.except_osv('Alerta','La compañia del usuario no tiene una empresa asignada. Contacte a su administrador.')
			if user.company_id.partner_id.nro_documento == False:
				raise osv.except_osv('Alerta','La compañia del usuario no tiene un numero de documento. Contacte a su administrador.')

			ruc = user.company_id.partner_id.nro_documento

			obj_analizar = self.env['account.perception.report'].search(filtro)[0]
			t_t = obj_analizar.periodo
			
			file_name = '0621' + ruc + (t_t[3:8] + t_t[:2]) +'PI.txt'	


			vals = {
				'output_name': file_name,
				'output_file': base64.encodestring(rpta),
				'respetar':1,		
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

			workbook = Workbook(direccion +'tempo_peception.xlsx')
			worksheet = workbook.add_worksheet("Perception PI")

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
			
			numberdosbold = workbook.add_format({'num_format':'0.00','bold': True})
			bord = workbook.add_format()
			bord.set_border(style=1)
			numberdos.set_border(style=1)
			numbertres.set_border(style=1)          
			x= 4
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.write(0,0, u"Percepción", bold)
			
			worksheet.write(3,0, "Libro",boldbord)
			worksheet.write(3,1, "Voucher",boldbord)
			worksheet.write(3,2, "RUC",boldbord)
			worksheet.write(3,3, "Tipo Doc.",boldbord)
			worksheet.write(3,4, "Serie",boldbord)
			worksheet.write(3,5, u"Número",boldbord)
			worksheet.write(3,6, "Fecha",boldbord)
			worksheet.write(3,7, u"Percepción",boldbord)
			

			for i in self.env['account.perception.report'].search(filtro):

				worksheet.write(x,0, i.libro if i.libro else '' ,bord)
				worksheet.write(x,1, i.voucher if i.voucher else '' ,bord)
				worksheet.write(x,2, i.ruc if i.ruc else '' ,bord)
				worksheet.write(x,3, i.tipo_doc if i.tipo_doc else '' ,bord)
				worksheet.write(x,4, i.serie if i.serie else '' ,bord)
				worksheet.write(x,5, i.numero if i.numero else '' ,bord)
				worksheet.write(x,6, i.fecha if i.fecha else '' ,bord)
				worksheet.write(x,7, i.percepcion ,numberdos)

				x +=1
					

			tam_col = [20,20,20,20,20,20,14,20,20,20,20,14,20,20,20,20,20,20,20,14,20,20,20,20,20,20,20,14,20,20,20]


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
			
			f = open(direccion + 'tempo_peception.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'PercepcionPI.xlsx',
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
	def csv_verif_integer(self,data):
		if data:
			return "%0.2f"%(data)
		else:
			return '0.00'

	@api.multi
	def csv_verif(self,data):
		if data:
			return data
		else:
			return ''

	@api.multi
	def csv_convert(self,data,separador):
		tmp = self.csv_verif(data.ruc)
		tmp += separador+ self.csv_verif(data.tipo_doc)
		tmp += separador+ self.csv_verif(data.serie)
		tmp += separador+ self.csv_verif(data.numero)
	
		fecha_corregida = ''

		if data.fecha:
			fecha_parsiada = data.fecha.split('-')
			fecha_corregida = fecha_parsiada[2] + '/' +  fecha_parsiada[1] + '/'+ fecha_parsiada[0]
		tmp += separador+ self.csv_verif( fecha_corregida)
		tmp += separador+ self.csv_verif_integer(data.percepcion)
		tmp += separador
		return unicode(tmp)




class account_perception_report_wizard(osv.TransientModel):
	_name='account.perception.report.wizard'

	def get_fiscalyear(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		id_year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1).id
		if not id_year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			return id_year

	fiscal_id = fields.Many2one('account.fiscalyear','Año Fiscal',required=True,default=lambda self: self.get_fiscalyear(),readonly=True)
	period_ini =fields.Many2one('account.period','Periodo Inicio',required=True)
	period_fin =fields.Many2one('account.period','Periodo Fin',required=True)
	tipo = fields.Selection( [('1', 'Solo Percepciones'),
								   ('2','Detalle de Percepciones')],
								   'Mostrar', required=True)

	@api.model
	def get_wizard(self):
		return self.env['automatic.fiscalyear'].get_wizard('Percepciones',self.id,'account.perception.report.wizard','account_percepcion_reporte_it.view_account_perception_report_wizard_form','default_period_ini','default_period_fin')

	@api.onchange('fiscal_id')
	def onchange_fiscalyear(self):
		if self.fiscal_id.id:
			return {'domain':{'period_ini':[('fiscalyear_id','=',self.fiscal_id.id )], 'period_fin':[('fiscalyear_id','=',self.fiscal_id.id )]}}
		else:
			return {'domain':{'period_ini':[], 'period_fin':[]}}

	@api.multi
	def do_rebuild(self):
		inicial_a = int(self.period_ini.code.split('/')[0])
		inicial_b = int(self.period_ini.code.split('/')[1])
		final_a = int(self.period_fin.code.split('/')[0])
		final_b = int(self.period_fin.code.split('/')[1])

		tmp = []
		while str(inicial_b) + ('0'+str(inicial_a) if inicial_a <10 else str(inicial_a)) <= str(final_b) + ('0'+str(final_a) if final_a <10 else str(final_a)) :
			tmp.append( ('0'+str(inicial_a) if inicial_a <10 else str(inicial_a)) + '/' + str(inicial_b))
			if inicial_a ==13:
				inicial_a = 0
				inicial_b +=1
			else:
				inicial_a +=1


		filtro = [('periodo_p','in', tmp )]

		if self.tipo == '2':
			return {
				"name": "Percepciones",
				"domain": filtro,
				"type": "ir.actions.act_window",
				"res_model": "account.perception.report",
				"views": [[False, "tree"]],
			}
		else:
			return {
				"name": "Percepciones",
				"domain": filtro,
				"type": "ir.actions.act_window",
				"res_model": "account.perception.reducida.report",
				"views": [[False, "tree"]],
			}
