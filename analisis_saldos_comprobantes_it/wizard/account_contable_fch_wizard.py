# -*- encoding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

class saldo_comprobante_wizard(osv.TransientModel):
	_name='saldo.comprobante.wizard'

	fecha_ini = fields.Date('Fecha Inicio',required=True)
	fecha_fin = fields.Date('Fecha Final',required=True)	
	mostrar =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('csv','CSV')], 'Mostrar en', required=True)
	check = fields.Boolean('Solo pendientes')

	empresa = fields.Many2one('res.partner','Empresa')
	cuenta = fields.Many2one('account.account','Cuenta')
	tipo = fields.Selection( [('A pagar','A pagar'),('A cobrar','A cobrar')], 'Tipo')


	@api.onchange('tipo')
	def _onchange_type_account(self):
		if self.tipo:
			if str(self.tipo) == "A pagar":
				return {'domain':{'cuenta':[('user_type_id.type','=','payable')]}}
			elif str(self.tipo) == "A cobrar":
				return {'domain':{'cuenta':[('user_type_id.type','=','receivable')]}}
		else:
			return {'domain':{'cuenta':[('user_type_id.type','in',('payable','receivable'))]}}
			
	@api.multi
	def do_rebuild(self):
		self.env.cr.execute("""  DROP VIEW IF EXISTS saldo_comprobante;
			create or replace view saldo_comprobante as (

select row_number() OVER () AS id,* from
(
	select 
am.date as fecha_emision,
rp.name as empresa,
CASE WHEN aat.type= 'payable' THEN 'A pagar'  ELSE 'A cobrar' END as tipo_cuenta,
aa.code,
itd.code as tipo,
aml.nro_comprobante as nro_comprobante,
T.debe,
T.haber,
CASE WHEN abs(T.saldo) < 0.01 then 0 else T.saldo end as saldo,
rc.name as divisa,
T.amount_currency
from (
select concat(account_move_line.partner_id,'-',account_id,'-',type_document_it,'-',TRIM(nro_comprobante) ) as identifica,min(account_move_line.id),sum(debit)as debe,sum(credit) as haber, sum(debit)-sum(credit) as saldo, sum(amount_currency) as amount_currency from account_move_line
inner join account_move ami on ami.id = account_move_line.move_id
left join account_account on account_account.id=account_move_line.account_id
left join account_account_type aat on aat.id = account_account.user_type_id
where (aat.type='receivable' or aat.type='payable' ) --and account_account.reconcile = true
and ami.fecha_contable >= '""" + str(self.fecha_ini) + """' and ami.fecha_contable <= '""" + str(self.fecha_fin) + """' and ami.state != 'draft'
group by identifica) as T
inner join account_move_line aml on aml.id = T.min
inner join account_move am on am.id = aml.move_id
left join res_partner rp on rp.id = aml.partner_id
left join einvoice_catalog_01 itd on itd.id = aml.type_document_it
left join res_currency rc on rc.id = aml.currency_id
left join account_account aa on aa.id = aml.account_id
left join account_account_type aat on aat.id = aa.user_type_id
order by  code,empresa, nro_comprobante
) T

						)""")
		filtro = []

		if self.check == True:
			filtro.append( ('saldo','!=',0) )
		if self.cuenta.id:
			filtro.append( ('code','=', self.cuenta.code ) )

		if self.empresa.id:
			filtro.append( ('empresa','=', self.empresa.name ) )

		if self.tipo:
			filtro.append( ('tipo_cuenta','=',self.tipo) )

		move_obj = self.env['saldo.comprobante']
		lstidsmove= move_obj.search(filtro)		
		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')		

		#DSC_Exportar a CSV por el numero de filas
		self.env.cr.execute("""select count(*)  from saldo_comprobante""")
		rows = self.env.cr.fetchone()
		#if self.mostrar == 'excel' and rows[0] > 1000:
		#	self.mostrar = 'csv'

		if self.mostrar == 'pantalla':

			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'saldo.comprobante',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		#DSC_
		if self.mostrar == 'csv':
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			docname = 'SaldoFecha.csv'
			#CSV
			sql_query = """	COPY (SELECT * FROM saldo_comprobante )TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
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

		
		if self.mostrar == 'excel':
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			workbook = Workbook(direccion +'saldoperiodo.xlsx')
			worksheet = workbook.add_worksheet("Analisis Saldo x Periodo")
			#Print Format
			worksheet.set_landscape() #Horizontal
			worksheet.set_paper(9) #A-4
			worksheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
			worksheet.fit_to_pages(1, 0)  # Ajustar por Columna		

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

			title = workbook.add_format({'bold': True})
			title.set_align('center')
			title.set_align('vcenter')
			title.set_text_wrap()
			title.set_font_size(20)
			worksheet.set_row(0, 30)

			x= 10				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.merge_range(0,0,0,10, u"Análisis de Saldos x Fecha", title)


			worksheet.write(2,0, u"Fecha Inicial", bold)
			worksheet.write(2,1, self.fecha_ini, normal)

			worksheet.write(3,0, u"Fecha Final", bold)
			worksheet.write(3,1, self.fecha_fin, normal)

			worksheet.write(4,0, u"Solo Pendientes", bold)
			worksheet.write(4,1, 'Si' if self.check else 'No', normal)

			worksheet.write(5,0, u"Empresa", bold)
			worksheet.write(5,1, self.empresa.name if self.empresa.name else '', normal)

			worksheet.write(6,0, u"Cuenta", bold)
			worksheet.write(6,1, self.cuenta.name if self.cuenta.name else '', normal)

			worksheet.write(7,0, u"Tipo", bold)
			worksheet.write(7,1, self.tipo if self.tipo else '', normal)


			worksheet.write(9,0, "Fecha Emisión",boldbord)
			worksheet.write(9,1, "Empresa",boldbord)
			worksheet.write(9,2, "Tipo Cuenta",boldbord)
			worksheet.write(9,3, u"Cuenta",boldbord)
			worksheet.write(9,4, "Tipo Documento",boldbord)
			worksheet.write(9,5, "Nro. Comprobante",boldbord)
			worksheet.write(9,6, "Debe",boldbord)
			worksheet.write(9,7, "Haber",boldbord)
			worksheet.write(9,8, "Saldo",boldbord)
			worksheet.write(9,9, "Divisa",boldbord)
			worksheet.write(9,10, u"Importe",boldbord)


			for line in self.env['saldo.comprobante'].search(filtro):
				worksheet.write(x,0,line.fecha_emision if line.fecha_emision  else '',bord )
				worksheet.write(x,1,line.empresa if line.empresa  else '',bord)
				worksheet.write(x,2,line.tipo_cuenta if line.tipo_cuenta  else '',bord)
				worksheet.write(x,3,line.code if line.code  else '',bord)
				worksheet.write(x,4,line.tipo if line.tipo  else '',bord)
				worksheet.write(x,5,line.nro_comprobante if line.nro_comprobante  else '',bord)
				worksheet.write(x,6,line.debe ,numberdos)
				worksheet.write(x,7,line.haber ,numberdos)
				worksheet.write(x,8,line.saldo ,numberdos)
				worksheet.write(x,9,line.divisa if  line.divisa else '',bord)
				worksheet.write(x,10,line.amount_currency ,numberdos)

				x = x +1

			tam_col = [15,45,12,10,12,13,9,9,9,11,14,10,11,14,14,10,16,16,20,36]


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
			
			f = open(direccion + 'saldoperiodo.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'SaldoFecha.xlsx',
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


		

		