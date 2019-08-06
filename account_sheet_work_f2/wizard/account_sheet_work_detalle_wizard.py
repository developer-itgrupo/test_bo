# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api, _
import codecs
from datetime import *
from odoo.exceptions import UserError, ValidationError

class account_sheet_work_f2_wizard(osv.TransientModel):
	_name='account.sheet.work.f2.wizard'

	period = fields.Many2one('account.period','Periodo',required=True)
	wizrd_level_sheet = fields.Selection((('1','Cuentas de Balance'),
									('2','Cuentas de Registro')						
									),'Nivel',required=True)

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


	type_show = fields.Selection([('pantalla','Pantalla'),('excel','Excel')],'Mostrar',required=True)

	@api.model
	def get_wizard(self):
		return self.env['automatic.fiscalyear'].get_wizard('Hoja de Trabajo F2',self.id,'account.sheet.work.f2.wizard','account_sheet_work_f2.view_account_sheet_work_f2_wizard_form','dummy','default_period')

	@api.onchange('fiscalyear_id')
	def onchange_fiscalyear(self):
		if self.fiscalyear_id:
			return {'domain':{'period':[('fiscalyear_id','=',self.fiscalyear_id.id )]}}
		else:
			return {'domain':{'period':[]}}

	@api.multi
	def do_rebuild(self):
		period = self.period
		
		has_currency = False
		filtro = []
		
		currency = False
		
		
		
		if self.wizrd_level_sheet == '1':
			self.env.cr.execute("""

			DROP VIEW IF EXISTS account_sheet_work_f2_visual cascade;
			DROP TABLE IF EXISTS tmp_pre_hoja_balance_f2_v2 cascade;
			create TABLE tmp_pre_hoja_balance_f2_v2 as (

			select id,cuenta,descripcion,totaldebe as debeinicial,totalhaber as haberinicial, debe as debe, haber as haber, coalesce(debe,0) + coalesce(totaldebe,0) as debesa, coalesce(haber,0) + coalesce(totalhaber,0)  as habersa, finaldeudor as saldodeudor, finalacreedor as saldoacredor, activo, pasivo, perdidasnat, ganancianat, perdidasfun, gananciafun from get_reporte_hoja_balance("""+ str(currency)+ """,periodo_num('""" + period.code + """'),periodo_num('""" + period.code +"""'))

			);
			CREATE OR REPLACE view account_sheet_work_f2_visual as (

				select * from tmp_pre_hoja_balance_f2_v2
				union all 
				select  
				1000001 as id,
				Null::varchar as cuenta,
				'Total' as descripcion,
				sum(debeinicial) as debeinicial,
				sum(haberinicial) as haberinicial,
				sum(debe) as debe,
				sum(haber) as haber,
				sum(debesa) as debesa,
				sum(habersa) as habersa,
				sum(saldodeudor) as saldodeudor,
				sum(saldoacredor) as saldoacredor,
				sum(activo) as activo,
				sum(pasivo) as pasivo,
				sum(perdidasnat) as perdidasnat,
				sum(ganancianat) as ganancianat,
				sum(perdidasfun) as perdidasfun,
				sum(gananciafun) as gananciafun
				from 
				tmp_pre_hoja_balance_f2_v2

				union all 

				select  
				1000002 as id,
				Null::varchar as cuenta,
				'Resultado del Periodo' as descripcion,
				0 as debeinicial,
				0 as haberinicial,
				0 as debe,
				0 as haber,
				0 as debesa,
				0 as habersa,
				0 as saldodedudor,
				0 as saldoacredor,
								
				CASE WHEN sum(activo) > sum(pasivo) THEN  0 ELSE sum(pasivo)- sum(activo) END as activo,
				CASE WHEN sum(pasivo) > sum(activo) THEN  0 ELSE sum(activo)- sum(pasivo) END as pasivo,
				CASE WHEN sum(perdidasnat) > sum(ganancianat) THEN 0 ELSE sum(ganancianat)- sum(perdidasnat) END as perdidasnat,
				CASE WHEN sum(ganancianat) > sum(perdidasnat) THEN 0 ELSE sum(perdidasnat)- sum(ganancianat) END as ganancianat,
				CASE WHEN sum(perdidasfun) > sum(gananciafun) THEN 0 ELSE sum(gananciafun)- sum(perdidasfun) END as perdidasfun,
				CASE WHEN sum(gananciafun) > sum(perdidasfun) THEN 0 ELSE sum(perdidasfun)- sum(gananciafun) END as gananciafun
				from 
				tmp_pre_hoja_balance_f2_v2

				union all

				select 1000003 as id,
				Null::varchar as cuenta,
				'Sumas Iguales' as descripcion,
				sum(debeinicial) as debeinicial,
				sum(haberinicial) as haberinicial,
				sum(debe) as debe,
				sum(haber) as haber,
				sum(debesa) as debesa,
				sum(habersa) as habersa,
				sum(saldodeudor) as saldodeudor,
				sum(saldoacredor) as saldoacredor,
				sum(activo) as activo,
				sum(pasivo) as pasivo,
				sum(perdidasnat) as perdidasnat,
				sum(ganancianat) as ganancianat,
				sum(perdidasfun) as perdidasfun,
				sum(gananciafun) as gananciafun

				from (
				select  
				1000001 as id,
				Null::varchar as cuenta,
				'Total' as descripcion,
				sum(debeinicial) as debeinicial,
				sum(haberinicial) as haberinicial,
				sum(debe) as debe,
				sum(haber) as haber,
				sum(debesa) as debesa,
				sum(habersa) as habersa,
				sum(saldodeudor) as saldodeudor,
				sum(saldoacredor) as saldoacredor,
				sum(activo) as activo,
				sum(pasivo) as pasivo,
				sum(perdidasnat) as perdidasnat,
				sum(ganancianat) as ganancianat,
				sum(perdidasfun) as perdidasfun,
				sum(gananciafun) as gananciafun
				from 
				tmp_pre_hoja_balance_f2_v2

				union all 

				select  
				1000002 as id,
				Null::varchar as cuenta,
				'Resultado del Periodo' as descripcion,
				0 as debeinicial,
				0 as haberinicial,
				0 as debe,
				0 as haber,
				0 as debesa,
				0 as habersa,
				0 as saldodedudor,
				0 as saldoacredor,
								
				CASE WHEN sum(activo) > sum(pasivo) THEN  0 ELSE sum(pasivo)- sum(activo) END as activo,
				CASE WHEN sum(pasivo) > sum(activo) THEN  0 ELSE sum(activo)- sum(pasivo) END as pasivo,
				CASE WHEN sum(perdidasnat) > sum(ganancianat) THEN 0 ELSE sum(ganancianat)- sum(perdidasnat) END as perdidasnat,
				CASE WHEN sum(ganancianat) > sum(perdidasnat) THEN 0 ELSE sum(perdidasnat)- sum(ganancianat) END as ganancianat,
				CASE WHEN sum(perdidasfun) > sum(gananciafun) THEN 0 ELSE sum(gananciafun)- sum(perdidasfun) END as perdidasfun,
				CASE WHEN sum(gananciafun) > sum(perdidasfun) THEN 0 ELSE sum(perdidasfun)- sum(gananciafun) END as gananciafun
				from 
				tmp_pre_hoja_balance_f2_v2
				) AS T

			)""")	
		else:
			self.env.cr.execute("""

			DROP VIEW IF EXISTS account_sheet_work_f2_visual cascade;
			DROP TABLE IF EXISTS tmp_pre_hoja_registro_f2 cascade;
			create TABLE tmp_pre_hoja_registro_f2 as (

			select id,cuenta,descripcion,totaldebe as debeinicial,totalhaber as haberinicial, debe as debe, haber as haber,  coalesce(debe,0) + coalesce(totaldebe,0) as debesa, coalesce(haber,0) + coalesce(totalhaber,0)  as habersa, finaldeudor as saldodeudor, finalacreedor as saldoacredor, activo, pasivo, perdidasnat, ganancianat, perdidasfun, gananciafun from get_reporte_hoja_registro("""+ str(currency)+ """,periodo_num('""" + period.code + """'),periodo_num('""" + period.code +"""'))

			);
			CREATE OR REPLACE view account_sheet_work_f2_visual as (

				select * from tmp_pre_hoja_registro_f2
				union all 
				select  
				1000001 as id,
				Null::varchar as cuenta,
				'Total' as descripcion,
				sum(debeinicial) as debeinicial,
				sum(haberinicial) as haberinicial,
				sum(debe) as debe,
				sum(haber) as haber,
				sum(debesa) as debesa,
				sum(habersa) as habersa,
				sum(saldodeudor) as saldodeudor,
				sum(saldoacredor) as saldoacredor,
				sum(activo) as activo,
				sum(pasivo) as pasivo,
				sum(perdidasnat) as perdidasnat,
				sum(ganancianat) as ganancianat,
				sum(perdidasfun) as perdidasfun,
				sum(gananciafun) as gananciafun
				from 
				tmp_pre_hoja_registro_f2

				union all 

				select  
				1000002 as id,
				Null::varchar as cuenta,
				'Resultado del Periodo' as descripcion,
				0 as debeinicial,
				0 as haberinicial,
				0 as debe,
				0 as haber,
				0 as debesa,
				0 as habersa,
				0 as saldodedudor,
				0 as saldoacredor,
								
				CASE WHEN sum(activo) > sum(pasivo) THEN  0 ELSE sum(pasivo)- sum(activo) END as activo,
				CASE WHEN sum(pasivo) > sum(activo) THEN  0 ELSE sum(activo)- sum(pasivo) END as pasivo,
				CASE WHEN sum(perdidasnat) > sum(ganancianat) THEN 0 ELSE sum(ganancianat)- sum(perdidasnat) END as perdidasnat,
				CASE WHEN sum(ganancianat) > sum(perdidasnat) THEN 0 ELSE sum(perdidasnat)- sum(ganancianat) END as ganancianat,
				CASE WHEN sum(perdidasfun) > sum(gananciafun) THEN 0 ELSE sum(gananciafun)- sum(perdidasfun) END as perdidasfun,
				CASE WHEN sum(gananciafun) > sum(perdidasfun) THEN 0 ELSE sum(perdidasfun)- sum(gananciafun) END as gananciafun
				from 
				tmp_pre_hoja_registro_f2

				union all

				select 1000003 as id,
				Null::varchar as cuenta,
				'Sumas Iguales' as descripcion,
				sum(debeinicial) as debeinicial,
				sum(haberinicial) as haberinicial,
				sum(debe) as debe,
				sum(haber) as haber,
				sum(debesa) as debesa,
				sum(habersa) as habersa,
				sum(saldodeudor) as saldodeudor,
				sum(saldoacredor) as saldoacredor,
				sum(activo) as activo,
				sum(pasivo) as pasivo,
				sum(perdidasnat) as perdidasnat,
				sum(ganancianat) as ganancianat,
				sum(perdidasfun) as perdidasfun,
				sum(gananciafun) as gananciafun

				from (
				select  
				1000001 as id,
				Null::varchar as cuenta,
				'Total' as descripcion,
				sum(debeinicial) as debeinicial,
				sum(haberinicial) as haberinicial,
				sum(debe) as debe,
				sum(haber) as haber,
				sum(debesa) as debesa,
				sum(habersa) as habersa,
				sum(saldodeudor) as saldodeudor,
				sum(saldoacredor) as saldoacredor,
				sum(activo) as activo,
				sum(pasivo) as pasivo,
				sum(perdidasnat) as perdidasnat,
				sum(ganancianat) as ganancianat,
				sum(perdidasfun) as perdidasfun,
				sum(gananciafun) as gananciafun
				from 
				tmp_pre_hoja_registro_f2

				union all 

				select  
				1000002 as id,
				Null::varchar as cuenta,
				'Resultado del Periodo' as descripcion,
				0 as debeinicial,
				0 as haberinicial,
				0 as debe,
				0 as haber,
				0 as debesa,
				0 as habersa,
				0 as saldodedudor,
				0 as saldoacredor,
								
				CASE WHEN sum(activo) > sum(pasivo) THEN  0 ELSE sum(pasivo)- sum(activo) END as activo,
				CASE WHEN sum(pasivo) > sum(activo) THEN  0 ELSE sum(activo)- sum(pasivo) END as pasivo,
				CASE WHEN sum(perdidasnat) > sum(ganancianat) THEN 0 ELSE sum(ganancianat)- sum(perdidasnat) END as perdidasnat,
				CASE WHEN sum(ganancianat) > sum(perdidasnat) THEN 0 ELSE sum(perdidasnat)- sum(ganancianat) END as ganancianat,
				CASE WHEN sum(perdidasfun) > sum(gananciafun) THEN 0 ELSE sum(gananciafun)- sum(perdidasfun) END as perdidasfun,
				CASE WHEN sum(gananciafun) > sum(perdidasfun) THEN 0 ELSE sum(perdidasfun)- sum(gananciafun) END as gananciafun
				from 
				tmp_pre_hoja_registro_f2
				) AS T

			)""")


		if self.type_show == 'pantalla':

			
			return {
				'type': 'ir.actions.act_window',
				'res_model': 'account.sheet.work.f2.visual',
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

			workbook = Workbook(direccion +'tempo_hojatrabajo.xlsx')
			worksheet = workbook.add_worksheet("Hoja Trabajo")

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

			worksheet.write(0,0, u"Año Fiscal:", bold)
			worksheet.write(0,1, self.fiscalyear_id.name, normal)
			worksheet.write(1,0, u"Periodo:", bold)
			worksheet.write(1,1, self.period.name, normal)
			worksheet.write(0,3, u"Nivel:", bold)
			worksheet.write(0,4, 'Cuentas de Balance' if self.wizrd_level_sheet == 1 else "Cuentas de Registro", normal)
			
			worksheet.write(3,0, "Cuenta",boldbord)
			worksheet.write(3,1, u"Descripción",boldbord)
			worksheet.write(3,2, "SI Debe",boldbord)
			worksheet.write(3,3, "SI Haber",boldbord)
			worksheet.write(3,4, "Debe",boldbord)
			worksheet.write(3,5, "Haber",boldbord)
			worksheet.write(3,6, u"Saldo Deudo",boldbord)
			worksheet.write(3,7, "Saldo Acreedor",boldbord)
			worksheet.write(3,8, "Activo",boldbord)
			worksheet.write(3,9, "Pasivo",boldbord)
			worksheet.write(3,10, "Perdidas Nat.",boldbord)
			worksheet.write(3,11, "Ganancia Nat.",boldbord)
			worksheet.write(3,12, "Perdidas Fun.",boldbord)
			worksheet.write(3,13, u"Ganancia Fun.",boldbord)

			for i in self.env['account.sheet.work.f2.visual'].search(filtro):
				worksheet.write(x,0, i.cuenta if i.cuenta else '',bord)
				worksheet.write(x,1, i.descripcion ,bord)
				worksheet.write(x,2, i.debeinicial ,numberdos)
				worksheet.write(x,3, i.haberinicial ,numberdos)
				worksheet.write(x,4, i.debe ,numberdos)
				worksheet.write(x,5, i.haber ,numberdos)

				worksheet.write(x,6, i.saldodeudor ,numberdos)
				worksheet.write(x,7, i.saldoacredor ,numberdos)
				worksheet.write(x,8, i.activo ,numberdos)
				worksheet.write(x,9, i.pasivo ,numberdos)
				worksheet.write(x,10, i.perdidasnat ,numberdos)
				worksheet.write(x,11, i.ganancianat ,numberdos)
				worksheet.write(x,12, i.perdidasfun ,numberdos)
				worksheet.write(x,13, i.gananciafun ,numberdos)

				x = x+1


			tam_col = [18,25,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14]


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
			
			f = open(direccion + 'tempo_hojatrabajo.xlsx', 'rb')
			
			
			vals = {
				'output_name': 'HojaTrabajo.xlsx',
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

