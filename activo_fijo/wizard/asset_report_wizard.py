# -*- encoding: utf-8 -*-
from odoo.osv import osv
import base64
from odoo import models, fields, api
import codecs
import pprint
from odoo.exceptions import UserError, ValidationError

class account_asset_report_wizard(models.TransientModel):
	_name='account.asset.report.wizard'
	
	period_id = fields.Many2one('account.period','Periodo Inicial',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')], 'Mostrar en', required=True)
	cuentas = fields.Many2many('account.account','account_bank_report_rel','id_bank_origen','id_account_destino', string='Cuentas', required=True)
	fiscalyear_id = fields.Many2one('account.fiscalyear','Año Fiscal',required=True)
	estado = fields.Selection([('uso','En uso'),('baja','En baja')], 'Estado')


	@api.onchange('fiscalyear_id')
	def _onchange_fiscalyear(self):
		if self.fiscalyear_id.id:
			peri =self.env['account.period'].search([('fiscalyear_id','=',self.fiscalyear_id.id)])

			return {'domain': {'period_id': [('id', 'in', peri.ids)]}}
		return {}


	@api.onchange('period_id')
	def _onchange_period(self):
		if self.period_id.id:
			fis_id =self.period_id.fiscalyear_id.id
			self.fiscalyear_id = fis_id

	@api.multi
	def do_rebuild(self):

		date_start = self.period_id.date_start
		date_stop = self.period_id.date_stop
		if self.type_show == 'excel':
			query = """ select aa.code, 
aa.name, 
aa.parent_id, 
--ai.number, 
  CASE
    WHEN ai.number IS NOT NULL THEN ai.number
    ELSE aa.nro_comprobante 
  END AS nro_compr,
ai.partner_id, 
ac.id, 
aa.date, 
aa.date_start, 
aa.f_baja,
aa.value,
(SELECT amount FROM account_asset_depreciation_line dpl WHERE dpl.asset_id = aa.id and dpl.depreciation_date = '""" +str(date_stop)+"""') as dp_amount,
(SELECT sum(amount) FROM account_asset_depreciation_line dpl WHERE dpl.asset_id = aa.id and dpl.depreciation_date <='""" +str(date_stop)+"""') as dp_acum,
cc.code as account_asset,
cc1.code as account_depreciation,
cc2.code as account_depreciation_expense,
cc3.code as account_baja,
an.code as account_analytic
--sum(ad.amount)
from account_asset_asset as aa
join account_asset_category ac on ac.id = aa.category_id
join account_account cc on cc.id = ac.account_asset_id
join account_account cc1 on cc1.id = ac.account_depreciation_id
join account_account cc2 on cc2.id = ac.account_depreciation_expense_id

left join account_invoice  ai on aa.invoice_id = ai.id
left join account_account cc3 on cc3.id = ac.account_retire
left join account_analytic_account an on an.id = ac.account_analytic_id
left join account_asset_depreciation_line ad on ad.id = ac.account_analytic_id
"""
			self.env.cr.execute(query)
			obj =self.env.cr.fetchall()
			import io
			from xlsxwriter.workbook import Workbook
			from xlsxwriter.utility import xl_rowcol_to_cell

			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook( direccion + 'reporte_activo.xlsx')
			worksheet = workbook.add_worksheet("Activos Fijos")
			bold = workbook.add_format({'bold': True})

			bold_title = workbook.add_format({'bold': True,'align': 'center','valign': 'vcenter'})
			bold_title.set_font_size(14)
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
			x= 8				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.write(7,0, "Codigo",boldbord)
			worksheet.write(7,1, u"Activo",boldbord)
			worksheet.write(7,2, u"Padre",boldbord)

			worksheet.write(7,3, u"Nro. Comprobante",boldbord)
			worksheet.write(7,4, u"Proveedor",boldbord)
			worksheet.write(7,5, u"Categoria",boldbord)
			worksheet.write(7,6, u"Fecha Compra",boldbord)
			worksheet.write(7,7, u"Fecha Uso",boldbord)

			#worksheet.merge_range(6,5,6,7, 'Moneda Nacional')

			worksheet.write(7,8, u"Fecha Baja",boldbord)

			worksheet.write(7,9, u"Valor",boldbord)
			worksheet.write(7,10, u"Depreciación Periodo",boldbord)
			worksheet.write(7,11, u"Depreciación Acumulada",boldbord)
			worksheet.write(7,12, u"Valor Neto",boldbord)
			worksheet.write(7,13, u"Cuenta Activo",boldbord)
			worksheet.write(7,14, u"Cuenta Depreciación",boldbord)
			worksheet.write(7,15, u"Cuenta Gasto",boldbord)
			worksheet.write(7,16, u"Cuenta Baja",boldbord)
			worksheet.write(7,17, u"Cuenta Analitica",boldbord)
			for line in obj:
				rest = line[11] or 0.00
				rest2 = line[9] - rest
				worksheet.write(x,0,line[0] or '' ,bord )
				worksheet.write(x,1,line[1] or '' ,bord )
				worksheet.write(x,2,line[2] or '' ,bord )
				worksheet.write(x,3,line[3] or '' ,bord )
				worksheet.write(x,4,line[4] or '' ,bord )
				worksheet.write(x,5,line[5] or '' ,bord )
				worksheet.write(x,6,line[6] or '' ,bord )
				worksheet.write(x,7,line[7] or '' ,bord )
				worksheet.write(x,8,line[8] or '' ,bord )
				worksheet.write(x,9,line[9] or '' ,bord )
				worksheet.write(x,10,line[10] or '' ,bord )
				worksheet.write(x,11,rest or '' ,bord )
				worksheet.write(x,12,rest2 or '' ,bord )
				worksheet.write(x,13,line[12] or '' ,bord )
				worksheet.write(x,14,line[13] or '' ,bord )
				worksheet.write(x,15,line[14] or '' ,bord )
				worksheet.write(x,16,line[15] or '' ,bord )
				worksheet.write(x,17,line[16] or '' ,bord )
				x = x +1

			workbook.close()
			
			f = open(direccion + 'reporte_activo.xlsx', 'rb')
			
			
			vals = {
				'output_name': 'reporte_activo.xlsx',
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
			self.env.cr.execute('TRUNCATE account_report_asset;')
			query = """select aa.code, 
aa.name, 
aa.parent_id, 
--ai.number, 
  CASE
    WHEN ai.number IS NOT NULL THEN ai.number
    ELSE aa.nro_comprobante 
  END AS nro_compr,
ai.partner_id, 
ac.id, 
aa.date, 
aa.date_start, 
aa.f_baja,
aa.value,
(SELECT amount FROM account_asset_depreciation_line dpl WHERE dpl.asset_id = aa.id and dpl.depreciation_date = '""" +str(date_stop)+"""') as dp_amount,
(SELECT sum(amount) FROM account_asset_depreciation_line dpl WHERE dpl.asset_id = aa.id and dpl.depreciation_date <='""" +str(date_stop)+"""') as dp_acum,
ac.account_asset_id as account_asset,
ac.account_depreciation_id as account_depreciation,
ac.account_depreciation_expense_id as account_depreciation_expense,
ac.account_retire as account_baja,
ac.account_analytic_id as account_analytic
--sum(ad.amount)
from account_asset_asset as aa
join account_asset_category ac on ac.id = aa.category_id
join account_account cc on cc.id = ac.account_asset_id
join account_account cc1 on cc1.id = ac.account_depreciation_id
join account_account cc2 on cc2.id = ac.account_depreciation_expense_id

left join account_invoice  ai on aa.invoice_id = ai.id
left join account_account cc3 on cc3.id = ac.account_retire
left join account_analytic_account an on an.id = ac.account_analytic_id
left join account_asset_depreciation_line ad on ad.id = ac.account_analytic_id

		"""
		if self.estado == 'uso':
			complemento = """ WHERE aa.is_baja = False OR aa.is_baja IS NULL """
			query = query + complemento
		if self.estado =='baja':
			complemento = """ WHERE aa.is_baja = True"""
			query = query + complemento
		self.env.cr.execute(query)
		obj =self.env.cr.fetchall()
		for element in obj:
			#import pdb; pdb.set_trace()
			rest = element[11] or 0.00
			value = {
				'codigo':element[0],
				'activo': element[1],
				'padre': element[2],
				'nro_compro': element[3],
				'proveedor': element[4],
				'categoria': element[5],
				'fecha_compra':  element[6],
				'fecha_uso':  element[7],
				'fecha_baja': element[8],
				'valor':  element[9],
				'depreciacion_periodo': element[10],
				'depreciacion_acumulada': rest,
				'valor_neto': element[9]-rest,
				'cuenta_activo': element[12],
				'cuenta_depreciacion':element[13],
				'cuenta_gasto':element[14],
				'cuenta_baja':element[15],
				'cuenta_analitica':element[16],
			}
			self.env['account.report.asset'].create(value)
		#import pdb; pdb.set_trace()
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']			
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'account.report.asset',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
		}
