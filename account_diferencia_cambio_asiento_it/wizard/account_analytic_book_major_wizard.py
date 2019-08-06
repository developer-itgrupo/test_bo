# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
from datetime import *
from odoo.exceptions import UserError, ValidationError

class view_diferencia_cambio_wizard(osv.TransientModel):
	_name='view.diferencia.cambio.wizard'

	period_id = fields.Many2one('account.period','Periodo',required=True)


	@api.multi
	def ver_informe(self):
		self.env.cr.execute("""
			CREATE OR REPLACE view view_diferencia_cambio_it as (


select row_number() OVER () AS id,
left(a4.code,1) as tipo,
cuenta,
sum(debe) as debe,
sum(haber) as haber,
case when left(a4.code,1)='A' then sum(debe-haber) else sum(haber-debe) end as saldomn,

case when left(a4.code,1)='A' then sum(amount_currency) else -sum(amount_currency) end as saldome,

case when left(a4.code,1)='A' then (select compra from exchange_diff_config_line where period_id=""" +str(self.period_id.id)+ """) else (select venta from exchange_diff_config_line where period_id=""" +str(self.period_id.id)+ """) end as TC,

case when left(a4.code,1)='A'
then (select compra from exchange_diff_config_line where period_id=""" +str(self.period_id.id)+ """) * sum(amount_currency) else
(select venta from exchange_diff_config_line where period_id=""" +str(self.period_id.id)+ """)* (-sum(amount_currency))
end as saldomn_act,


case when left(a4.code,1)='A'
then ((select compra from exchange_diff_config_line where period_id=""" +str(self.period_id.id)+ """) * sum(amount_currency))-sum(debe-haber) else
((select venta from exchange_diff_config_line where period_id=""" +str(self.period_id.id)+ """)* (-sum(amount_currency)))- sum(haber-debe)
end
as diferencia,



case when left(a4.code,1)='P' then 

    case when ((select compra from exchange_diff_config_line where period_id=""" +str(self.period_id.id)+ """) * sum(amount_currency))>sum(debe-haber) 
    then (select c2.code as cta_resultado from exchange_diff_config c1 left join account_account c2 on c2.id=c1.earn_account_id)--ganancia 
    else (select c2.code as cta_resultado from exchange_diff_config c1 left join account_account c2 on c2.id=c1.lose_account_id)--perdida 
    end  	
    
else

    case when ((select compra from exchange_diff_config_line where period_id=""" +str(self.period_id.id)+ """) * (-sum(amount_currency)))>sum(haber-debe) 
    then (select c2.code as cta_resultado from exchange_diff_config c1 left join account_account c2 on c2.id=c1.lose_account_id)--perdida 
    else (select c2.code as cta_resultado from exchange_diff_config c1 left join account_account c2 on c2.id=c1.earn_account_id)--ganancia  
    end	  

end
as resultado, """ +str(self.period_id.id)+ """  as period_id
from get_libro_diario(periodo_num('""" + '00/' + self.period_id.code.split('/')[1] + """'),periodo_num('""" + self.period_id.code +"""')) a1
left join account_move_line a2 on a2.id=a1.aml_id
left join account_account a3 on a3.code=a1.cuenta
left join account_account_type_it a4 on a4.id=a3.type_it
where a3.currency_id is not null and a3.internal_type not in ('payable','receivable') and (a3.analisis_documento=false or a3.analisis_documento is null)
group by a4.code,a1.cuenta
order by a1.cuenta
)
	""")

		return {
				'type': 'ir.actions.act_window',
				'res_model': 'view.diferencia.cambio.it',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}
		

	@api.multi
	def crear_asiento(self):

		self.env.cr.execute("""
			CREATE OR REPLACE view view_diferencia_cambio_it as (


select row_number() OVER () AS id,
left(a4.code,1) as tipo,
cuenta,
sum(debe) as debe,
sum(haber) as haber,
case when left(a4.code,1)='A' then sum(debe-haber) else sum(haber-debe) end as saldomn,

case when left(a4.code,1)='A' then sum(amount_currency) else -sum(amount_currency) end as saldome,

case when left(a4.code,1)='A' then (select compra from exchange_diff_config_line where period_id=""" +str(self.period_id.id)+ """) else (select venta from exchange_diff_config_line where period_id=""" +str(self.period_id.id)+ """) end as TC,

case when left(a4.code,1)='A'
then (select compra from exchange_diff_config_line where period_id=""" +str(self.period_id.id)+ """) * sum(amount_currency) else
(select venta from exchange_diff_config_line where period_id=""" +str(self.period_id.id)+ """)* (-sum(amount_currency))
end as saldomn_act,


case when left(a4.code,1)='A'
then ((select compra from exchange_diff_config_line where period_id=""" +str(self.period_id.id)+ """) * sum(amount_currency))-sum(debe-haber) else
((select venta from exchange_diff_config_line where period_id=""" +str(self.period_id.id)+ """)* (-sum(amount_currency)))- sum(haber-debe)
end
as diferencia,



case when left(a4.code,1)='P' then 

    case when ((select compra from exchange_diff_config_line where period_id=""" +str(self.period_id.id)+ """) * sum(amount_currency))>sum(debe-haber) 
    then (select c2.code as cta_resultado from exchange_diff_config c1 left join account_account c2 on c2.id=c1.earn_account_id)--ganancia 
    else (select c2.code as cta_resultado from exchange_diff_config c1 left join account_account c2 on c2.id=c1.lose_account_id)--perdida 
    end  	
    
else

    case when ((select compra from exchange_diff_config_line where period_id=""" +str(self.period_id.id)+ """) * (-sum(amount_currency)))>sum(haber-debe) 
    then (select c2.code as cta_resultado from exchange_diff_config c1 left join account_account c2 on c2.id=c1.lose_account_id)--perdida 
    else (select c2.code as cta_resultado from exchange_diff_config c1 left join account_account c2 on c2.id=c1.earn_account_id)--ganancia  
    end	  

end
as resultado, """ +str(self.period_id.id)+ """  as period_id
from get_libro_diario(periodo_num('""" + '00/' + self.period_id.code.split('/')[1] + """'),periodo_num('""" + self.period_id.code +"""')) a1
left join account_move_line a2 on a2.id=a1.aml_id
left join account_account a3 on a3.code=a1.cuenta
left join account_account_type_it a4 on a4.id=a3.type_it
where a3.currency_id is not null and a3.internal_type not in ('payable','receivable') and (a3.analisis_documento=false or a3.analisis_documento is null)
group by a4.code,a1.cuenta
order by a1.cuenta
)
	""")


		param = self.env['main.parameter'].search([])[0]
		cabezado = {
			'journal_id':param.diario_destino.id,
			'date':self.period_id.date_stop,
			'ref':'COSTO VENTAS '+ self.period_id.code,
			'fecha_contable':self.period_id.date_stop,
			'ple_diariomayor':'1',
		}
		asiento = self.env['account.move'].create(cabezado)


		self.env.cr.execute("""

				select cuenta, ABS(SUM(CASE WHEN a1.resultado like '77%' then ROUND(diferencia,2) else 0 end)) as debit, ABS(SUM(CASE WHEN a1.resultado like '67%' then ROUND(diferencia,2) else 0 end)) as credit from
				view_diferencia_cambio_it a1
				group by a1.cuenta

			""")
		detalle = self.env.cr.fetchall()

		if len(detalle) == 0:
			raise UserError('No hay detalle para generar el asiento.')

		for i in detalle:
			cuenta_f = self.env['account.account'].search([('code','=',i[0])])
			linea = {
				'name':'ASIENTO DE DIFERENCIA DE CAMBIO '+self.period_id.code,
				'account_id':cuenta_f.id,
				'debit':i[1],
				'credit':i[2],
				'move_id':asiento.id,
			}

			try:
				self.env['account.move.line'].create(linea)
			except:
				raise UserError('No existe el TC para este periodo.')
			

		self.env.cr.execute("""

				select resultado, ABS(SUM(CASE WHEN a1.resultado like '67%' then ROUND(diferencia,2) else 0 end)) as debit, ABS(SUM(CASE WHEN a1.resultado like '77%' then ROUND(diferencia,2) else 0 end)) as credit from
				view_diferencia_cambio_it a1
				group by a1.resultado

			""")
		detalle = self.env.cr.fetchall()

		if len(detalle) == 0:
			raise UserError('No hay detalle para generar el asiento.')

		for i in detalle:
			cuenta_f = self.env['account.account'].search([('code','=',i[0])])
			linea = {
				'name':'ASIENTO DE DIFERENCIA DE CAMBIO '+self.period_id.code,
				'account_id':cuenta_f.id,
				'debit':i[1],
				'credit':i[2],
				'move_id':asiento.id,
			}
			try:
				self.env['account.move.line'].create(linea)
			except:
				raise UserError('No existe el TC para este periodo.')
			


		return {
				'type': 'ir.actions.act_window',
				'res_model': 'account.move',
				'view_mode': 'form',
				'view_type': 'form',
				'views': [(False, 'form')],
				'res_id':asiento.id,
			}		




	@api.multi
	def crear_asiento_parcial(self):
		lineas = self.env['view.diferencia.cambio.it'].browse(self.env.context['active_id'])

		param = self.env['main.parameter'].search([])[0]
		cabezado = {
			'journal_id':param.diario_destino.id,
			'date':lineas[0].period_id.date_stop,
			'ref':'COSTO VENTAS '+ lineas[0].period_id.code,
			'fecha_contable':lineas[0].period_id.date_stop,
			'ple_diariomayor':'1',
		}
		asiento = self.env['account.move'].create(cabezado)

		maslineas = [0,0,0,0]
		for i in lineas:
			maslineas.append(i.id)

		self.env.cr.execute("""

				select cuenta, ABS(SUM(CASE WHEN a1.resultado like '77%' then ROUND(diferencia,2) else 0 end)) as debit, ABS(SUM(CASE WHEN a1.resultado like '67%' then ROUND(diferencia,2) else 0 end)) as credit from
				view_diferencia_cambio_it a1
				where a1.id in """ + str(tuple(maslineas)) + """
				group by a1.cuenta

			""")
		detalle = self.env.cr.fetchall()

		if len(detalle) == 0:
			raise UserError('No hay detalle para generar el asiento.')

		for i in detalle:
			cuenta_f = self.env['account.account'].search([('code','=',i[0])])
			linea = {
				'name':'ASIENTO DE DIFERENCIA DE CAMBIO '+lineas[0].period_id.code,
				'account_id':cuenta_f.id,
				'debit':i[1],
				'credit':i[2],
				'move_id':asiento.id,
			}
			try:
				self.env['account.move.line'].create(linea)
			except:
				raise UserError('No existe el TC para este periodo.')

		self.env.cr.execute("""
				select resultado, ABS(SUM(CASE WHEN a1.resultado like '67%' then ROUND(diferencia,2) else 0 end)) as debit, ABS(SUM(CASE WHEN a1.resultado like '77%' then ROUND(diferencia,2) else 0 end)) as credit from
				view_diferencia_cambio_it a1
				where a1.id in """ + str(tuple(maslineas)) + """
				group by a1.resultado
			""")
		detalle = self.env.cr.fetchall()

		if len(detalle) == 0:
			raise UserError('No hay detalle para generar el asiento.')

		for i in detalle:
			cuenta_f = self.env['account.account'].search([('code','=',i[0])])
			linea = {
				'name':'ASIENTO DE DIFERENCIA DE CAMBIO '+lineas[0].period_id.code,
				'account_id':cuenta_f.id,
				'debit':i[1],
				'credit':i[2],
				'move_id':asiento.id,
			}
			try:
				self.env['account.move.line'].create(linea)
			except:
				raise UserError('No existe el TC para este periodo.')

		return {
				'type': 'ir.actions.act_window',
				'res_model': 'account.move',
				'view_mode': 'form',
				'view_type': 'form',
				'views': [(False, 'form')],
				'res_id':asiento.id,
			}		