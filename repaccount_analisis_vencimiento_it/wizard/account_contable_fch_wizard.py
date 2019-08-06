# -*- encoding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

class account_payable_analisis_vencimiento_wizard(osv.TransientModel):
	_name='account.payable.analisis.vencimiento.wizard'

	date = fields.Date('Fecha',default=fields.Date.today())


	@api.multi
	def do_rebuild(self):

		self.env.cr.execute("""
			DROP VIEW IF EXISTS account_payable_contable_vencimiento;
			create or replace view account_payable_contable_vencimiento as (


select 
id, 
fecha_emision, 
fecha_ven,
plazo,
empresa,
tipo,
nro_comprobante ,
case when divisa is not null then divisa else 'PEN' end as moneda,
importe_me,
code as cuenta,

CASE WHEN atraso <= 0 OR atraso is null then saldo else 0 end  as por_vencer,
CASE WHEN atraso > 0  and atraso < 16  then saldo else 0 end  as hasta_15,
CASE WHEN atraso > 15  and atraso < 31  then saldo else 0 end  as hasta_30,
CASE WHEN atraso > 30  and atraso < 61  then saldo else 0 end  as hasta_60,
CASE WHEN atraso > 60  and atraso < 91  then saldo else 0 end  as hasta_90,
CASE WHEN atraso > 90  and atraso < 181  then saldo else 0 end  as hasta_180,
CASE WHEN atraso > 180  then saldo else 0 end  as mas_de_180



from
(
	select 
aml.id as id,
ap.code as periodo,
lib.name as libro,
am.name as voucher,
am.date as fecha_emision,
aml.date_maturity as fecha_ven,
jj.value as plazo,
rp.name as empresa,
aa.code,
itd.code as tipo,
aml.nro_comprobante as nro_comprobante,
abs(T.saldo) as saldo,
rc.name as divisa,
abs(T.saldo_me) as importe_me,
'"""+ str(self.date) +"""'::date - aml.date_maturity as atraso,
am.state as estado


from (
select concat(account_move_line.partner_id,account_id,type_document_it,nro_comprobante) as identifica,min(account_move_line.id),sum(debit)as debe,sum(credit) as haber, sum(debit)-sum(credit) as saldo, sum(amount_currency) as saldo_me from account_move_line
inner join account_move ami on ami.id = account_move_line.move_id
inner join account_period api on api.date_start <= ami.date and api.date_stop >= ami.date  and ami.fecha_special = api.special
left join account_account on account_account.id=account_move_line.account_id
left join account_account_type aat on aat.id = account_account.user_type_id
where (aat.type='payable' and reconcile=TRUE) 


group by identifica
having sum(debit)-sum(credit) != 0 
) as T
inner join account_move_line aml on aml.id = T.min
inner join account_move am on am.id = aml.move_id
inner join account_period ap on ap.date_start <= am.date and ap.date_stop >= am.date  and am.fecha_special = ap.special
left join res_partner rp on rp.id = aml.partner_id
left join einvoice_catalog_01 itd on itd.id = aml.type_document_it
left join res_currency rc on rc.id = aml.currency_id
left join account_account aa on aa.id = aml.account_id
left join account_journal lib on lib.id=am.journal_id
left join account_invoice ft on ft.move_id=am.id
left join account_payment_term hh on hh.id=ft.payment_term_id
left join ir_translation jj on jj.res_id=hh.id and jj.name='account.payment.term,name'

where am.state='posted'
order by empresa, code, nro_comprobante
) T

						) """)


		move_obj = self.env['account.payable.contable.vencimiento']
		filtro = []

		lstidsmove= move_obj.search(filtro)

		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')
	
		if True:

			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook( direccion + 'tempo_vencimientopayable.xlsx')
			worksheet = workbook.add_worksheet("Analisis Vencimiento")
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


			title = workbook.add_format({'bold': True})
			title.set_align('center')
			title.set_align('vcenter')
			title.set_text_wrap()
			title.set_font_size(20)
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)
			bord.set_text_wrap()
			numberdos.set_border(style=1)
			numbertres.set_border(style=1)			
			x= 5				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')


			worksheet.merge_range(0,0,0,15,u"Análisis de Vencimiento Cuentas por Pagar",title)

			worksheet.write(1,0, "Fecha:", bold)
			
			worksheet.write(1,1, self.date, normal)
							
			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			
			worksheet.write(4,0, "F. Emi.",boldbord)
			
			worksheet.write(4,1, "F. Ven.",boldbord)
			worksheet.write(4,2, "Plazo",boldbord)
			worksheet.write(4,3, "Empresa",boldbord)
			worksheet.write(4,4, "TD",boldbord)				
			worksheet.write(4,5, u"Número",boldbord)

			worksheet.write(4,6, u"Moneda",boldbord)
			worksheet.write(4,7, u"Importe ME",boldbord)
			worksheet.write(4,8, "Cuenta",boldbord)

			worksheet.write(4,9, "Por Vencer",boldbord)
			worksheet.write(4,10, u"Hasta 15",boldbord)
			worksheet.write(4,11, u"Hasta 30",boldbord)
			worksheet.write(4,12, u"Hasta 60",boldbord)
			worksheet.write(4,13, u"Hasta 90",boldbord)
			worksheet.write(4,14, u"Hasta 180",boldbord)
			worksheet.write(4,15, u"Mas de 180",boldbord)


			for line in lstidsmove:
				worksheet.write(x,0,line.fecha_emision if line.fecha_emision else '' ,bord )
				worksheet.write(x,1,line.fecha_ven if line.fecha_ven  else '',bord )
				worksheet.write(x,2,line.plazo if line.plazo  else '',bord)
				worksheet.write(x,3,line.empresa if line.empresa  else '',bord)
				worksheet.write(x,4,line.tipo if line.tipo  else '',bord)
				worksheet.write(x,5,line.nro_comprobante if line.nro_comprobante else '',bord)
				worksheet.write(x,6,line.moneda if line.moneda else '',bord)
				worksheet.write(x,7,line.importe_me if line.importe_me else 0,numberdos)
				worksheet.write(x,8,line.cuenta if line.cuenta else '',bord)
				worksheet.write(x,9,line.por_vencer ,numberdos)
				worksheet.write(x,10,line.hasta_15 ,numberdos)
				worksheet.write(x,11,line.hasta_30 ,numberdos)
				worksheet.write(x,12,line.hasta_60 ,numberdos)
				worksheet.write(x,13,line.hasta_90 ,numberdos)
				worksheet.write(x,14,line.hasta_180 ,numberdos)
				worksheet.write(x,15,line.mas_de_180 ,numberdos)

				x = x +1


			tam_col = [11,11,10,45,10,16,16,16,16]

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
			workbook.close()
			
			f = open(direccion + 'tempo_vencimientopayable.xlsx', 'rb')
			
			
			vals = {
				'output_name': 'AnalisisVencimientoPorPagar.xlsx',
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

	


class account_receivable_analisis_vencimiento_wizard(osv.TransientModel):
	_name='account.receivable.analisis.vencimiento.wizard'

	date = fields.Date('Fecha',default=fields.Date.today())


	@api.multi
	def do_rebuild(self):

		self.env.cr.execute("""
			DROP VIEW IF EXISTS account_receivable_contable_vencimiento;
			create or replace view account_receivable_contable_vencimiento as (


select 
id, 
fecha_emision, 
fecha_ven,
plazo,
empresa,
tipo,
nro_comprobante ,
case when divisa is not null then divisa else 'PEN' end as moneda,
importe_me,
code as cuenta,

CASE WHEN atraso <= 0 OR atraso is null then saldo else 0 end  as por_vencer,
CASE WHEN atraso > 0  and atraso < 16  then saldo else 0 end  as hasta_15,
CASE WHEN atraso > 15  and atraso < 31  then saldo else 0 end  as hasta_30,
CASE WHEN atraso > 30  and atraso < 61  then saldo else 0 end  as hasta_60,
CASE WHEN atraso > 60  and atraso < 91  then saldo else 0 end  as hasta_90,
CASE WHEN atraso > 90  and atraso < 181  then saldo else 0 end  as hasta_180,
CASE WHEN atraso > 180  then saldo else 0 end  as mas_de_180



from
(
	select 
aml.id as id,
ap.code as periodo,
lib.name as libro,
am.name as voucher,
am.date as fecha_emision,
aml.date_maturity as fecha_ven,
jj.value as plazo,
rp.name as empresa,
aa.code,
itd.code as tipo,
aml.nro_comprobante as nro_comprobante,
abs(T.saldo) as saldo,
abs(T.saldo_me) as importe_me,
rc.name as divisa,
'"""+ str(self.date) +"""'::date - aml.date_maturity as atraso,
am.state as estado


from (
select concat(account_move_line.partner_id,account_id,type_document_it,nro_comprobante) as identifica,min(account_move_line.id),sum(debit)as debe,sum(credit) as haber, sum(debit)-sum(credit) as saldo, sum(amount_currency) as saldo_me from account_move_line
inner join account_move ami on ami.id = account_move_line.move_id
inner join account_period api on api.date_start <= ami.date and api.date_stop >= ami.date  and ami.fecha_special = api.special
left join account_account on account_account.id=account_move_line.account_id
left join account_account_type aat on aat.id = account_account.user_type_id
where (aat.type='receivable' and reconcile=TRUE) 


group by identifica
having sum(debit)-sum(credit) != 0 
) as T
inner join account_move_line aml on aml.id = T.min
inner join account_move am on am.id = aml.move_id
inner join account_period ap on ap.date_start <= am.date and ap.date_stop >= am.date  and am.fecha_special = ap.special
left join res_partner rp on rp.id = aml.partner_id
left join einvoice_catalog_01 itd on itd.id = aml.type_document_it
left join res_currency rc on rc.id = aml.currency_id
left join account_account aa on aa.id = aml.account_id
left join account_journal lib on lib.id=am.journal_id
left join account_invoice ft on ft.move_id=am.id
left join account_payment_term hh on hh.id=ft.payment_term_id
left join ir_translation jj on jj.res_id=hh.id and jj.name='account.payment.term,name'

where am.state='posted'
order by empresa, code, nro_comprobante
) T

						) """)


		move_obj = self.env['account.receivable.contable.vencimiento']
		filtro = []

		lstidsmove= move_obj.search(filtro)

		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')
	
		if True:

			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook( direccion + 'tempo_vencimientoreceivable.xlsx')
			worksheet = workbook.add_worksheet("Analisis Vencimiento")
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


			title = workbook.add_format({'bold': True})
			title.set_align('center')
			title.set_align('vcenter')
			title.set_text_wrap()
			title.set_font_size(20)
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)
			bord.set_text_wrap()
			numberdos.set_border(style=1)
			numbertres.set_border(style=1)			
			x= 5				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')


			worksheet.merge_range(0,0,0,15,u"Análisis de Vencimiento Receivable",title)

			worksheet.write(1,0, "Fecha:", bold)
			
			worksheet.write(1,1, self.date, normal)
							
			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			
			worksheet.write(4,0, "F. Emi.",boldbord)
			
			worksheet.write(4,1, "F. Ven.",boldbord)
			worksheet.write(4,2, "Plazo",boldbord)
			worksheet.write(4,3, "Empresa",boldbord)
			worksheet.write(4,4, "TD",boldbord)				
			worksheet.write(4,5, u"Número",boldbord)

			worksheet.write(4,6, u"Moneda",boldbord)
			worksheet.write(4,7, "Importe ME",boldbord)
			worksheet.write(4,8, "Cuenta",boldbord)

			worksheet.write(4,9, "Por Vencer",boldbord)
			worksheet.write(4,10, u"De 1 a 15",boldbord)
			worksheet.write(4,11, u"De 16 a 30",boldbord)
			worksheet.write(4,12, u"De 31 a 60",boldbord)
			worksheet.write(4,13, u"De 61 a 90",boldbord)
			worksheet.write(4,14, u"De 91 a 180",boldbord)
			worksheet.write(4,15, u"Mas de 180",boldbord)


			for line in lstidsmove:
				worksheet.write(x,0,line.fecha_emision if line.fecha_emision else '' ,bord )
				worksheet.write(x,1,line.fecha_ven if line.fecha_ven  else '',bord )
				worksheet.write(x,2,line.plazo if line.plazo  else '',bord)
				worksheet.write(x,3,line.empresa if line.empresa  else '',bord)
				worksheet.write(x,4,line.tipo if line.tipo  else '',bord)
				worksheet.write(x,5,line.nro_comprobante if line.nro_comprobante else '',bord)
				worksheet.write(x,6,line.moneda if line.moneda else '',bord)
				worksheet.write(x,7,line.importe_me if line.importe_me else 0,numberdos)
				worksheet.write(x,8,line.cuenta if line.cuenta else '',bord)
				worksheet.write(x,9,line.por_vencer ,numberdos)
				worksheet.write(x,10,line.hasta_15 ,numberdos)
				worksheet.write(x,11,line.hasta_30 ,numberdos)
				worksheet.write(x,12,line.hasta_60 ,numberdos)
				worksheet.write(x,13,line.hasta_90 ,numberdos)
				worksheet.write(x,14,line.hasta_180 ,numberdos)
				worksheet.write(x,15,line.mas_de_180 ,numberdos)

				x = x +1


			tam_col = [11,11,10,45,10,16,16,16,16]
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
			workbook.close()
			
			f = open(direccion + 'tempo_vencimientoreceivable.xlsx', 'rb')
			
			
			vals = {
				'output_name': 'AnalisisVencimientoPorCobrar.xlsx',
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

	