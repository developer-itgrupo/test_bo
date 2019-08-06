# -*- encoding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api, _
import codecs
import pprint
from datetime import *
from odoo.exceptions import UserError, ValidationError

class analisis_cuenta_wizard(models.TransientModel):
	_name='analisis.cuenta.wizard'

	def get_fiscalyear(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		id_year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1).id
		if not id_year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			return id_year

	fiscalyear_id = fields.Many2one	('account.fiscalyear',u'Año',required=True,default=lambda self: self.get_fiscalyear(),readonly=True)
	period_ini =fields.Many2one('account.period','Periodo Inicial',required=True)
	period_fin =fields.Many2one('account.period','Periodo Final',required=True)
	type_show = fields.Selection([('pantalla','Pantalla'),('excel','Excel')], 'Mostrar en', required=True)

	@api.model
	def get_wizard(self):
		return self.env['automatic.fiscalyear'].get_wizard('Analisis Cuenta',self.id,'analisis.cuenta.wizard','analisis_cuentas_it.view_analisis_cuenta_wizard_form','default_period_ini','default_period_fin')
				
	@api.onchange('fiscalyear_id')
	def onchange_fiscalyear(self):
		if self.fiscalyear_id:
			return {'domain':{'period_ini':[('fiscalyear_id','=',self.fiscalyear_id.id )],'period_fin':[('fiscalyear_id','=',self.fiscalyear_id.id )]}}
		else:
			return {'domain':{'period_ini':[],'period_fin':[]}}
	

	@api.multi
	def do_rebuild(self):		
		self.env.cr.execute(""" 

			DROP VIEW IF EXISTS analisis_cuenta;
			create or replace view analisis_cuenta as (

				select row_number() OVER () AS id,* from
				(

						select """+str(self.period_ini.id)+ """ as periodo_inicial, """+str(self.period_fin.id)+ """ as periodo_final,a3.group_balance,a3.group_function,a3.group_nature,a3.name as rubro,
						cuenta,suma_debe as debe,suma_haber as haber,suma_debe-suma_haber as saldo, aml_ids from ( 

							select cuenta,sum(debe) as suma_debe,sum(haber) as suma_haber, array_agg(aml_id) as aml_ids from get_libro_diario( periodo_num('""" +str(self.period_ini.code)+ """'), periodo_num('""" +str(self.period_fin.code)+ """') ) group by cuenta order by cuenta

						)
						a1 left join account_account a2 on a2.code=a1.cuenta left join account_account_type_it a3 on a3.id=a2.type_it

				) T

			)
			""")


		move_obj = self.env['analisis.cuenta']
		lstidsmove= move_obj.search([])		
		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')		

		if self.type_show == 'pantalla':

			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']			
			return {
				'name':'Analisis Cuenta',
				'domain' : [],
				'type': 'ir.actions.act_window',
				'res_model': 'analisis.cuenta',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		else:
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook( direccion + 'tempo_cuentacorriente.xlsx')
			worksheet = workbook.add_worksheet("Cuenta Corriente")
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
			title.set_font_size(18)
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)
			numberdos.set_border(style=1)
			numbertres.set_border(style=1)			
			x= 5				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')


			worksheet.merge_range(0,0,0,7,u"Análisis Cuenta",title)

			worksheet.write(1,0, u"Análisis de Cuenta:", bold)
			
			worksheet.write(1,1, self.period_ini.name, normal)
			
			worksheet.write(1,2, self.period_fin.name, normal)
			
			worksheet.write(2,0, "Fecha:",bold)
			
			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			import datetime
			worksheet.write(2,1, str(datetime.datetime.today())[:10], normal)
			
			worksheet.write(4,0, "Grupo Balance",boldbord)
			
			worksheet.write(4,1, u"Grupo Función",boldbord)
			worksheet.write(4,2, u"Grupo Natural",boldbord)
			worksheet.write(4,3, u"Rubro",boldbord)

			worksheet.write(4,4, u"Cuenta",boldbord)
			worksheet.write(4,5, "Debe",boldbord)

			worksheet.write(4,6, "Haber",boldbord)
			worksheet.write(4,7, u"Saldo",boldbord)


			for line in lstidsmove:
				worksheet.write(x,0,line.group_balance if line.group_balance else '' ,bord )
				worksheet.write(x,1,line.group_function if line.group_function  else '',bord )
				worksheet.write(x,2,line.group_nature if line.group_nature  else '',bord)
				worksheet.write(x,3,line.rubro if line.rubro else '',bord)
				worksheet.write(x,4,line.cuenta if line.cuenta else '',bord)
				worksheet.write(x,5,line.debe ,numberdos)
				worksheet.write(x,6,line.haber ,numberdos)
				worksheet.write(x,7,line.saldo ,numberdos)

				x = x +1
	
			tam_col = [16.14,7,22.2,13.5,38,3.5,15,15,15,15,15,15,15,15,15,15]
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

			workbook.close()
			
			f = open(direccion + 'tempo_cuentacorriente.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'AnalisisCuenta.xlsx',
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

		