# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs

class ht_sunat_txt_wizard(models.TransientModel):
	_name='ht.sunat.txt.wizard'

	form_pdt = fields.Char('Formulario PDT',size=40,required=False)
	ejercicio = fields.Many2one('account.fiscalyear',string='Ejercicio',required=True)
	tipo = fields.Selection( (('pantalla','Pantalla'),('txt','Txt')), 'Mostrar', required=True)



	@api.multi
	def do_rebuild(self):
		self.env.cr.execute(""" 

			DROP VIEW IF EXISTS ht_sunat;
			create or replace view ht_sunat as (


select row_number() OVER() as id,* from (
select CASE WHEN CTX.cuenta is not null THEN CTX.cuenta ELSE trans.cuenta END as cuenta, coalesce(CTX.totaldebe,0) as debe_si, coalesce(CTX.totalhaber,0) as haber_si, coalesce(CTX.debe,0) as debe, coalesce(CTX.haber,0) as haber, coalesce(trans.debit,0) as debe_trans,coalesce(trans.credit,0) as haber_trans
from (
select X.shiname as cuenta,
sum(X.totaldebe) as totaldebe ,sum(X.totalhaber) as totalhaber,
sum(X.debe) as debe,sum(X.haber) as haber
from (select  M.*,T.* ,aa.code_sunat as shiname,
CASE WHEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + M.debe - M.haber >0 THEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + M.debe - M.haber ELSE 0 END as finaldeudor,
CASE WHEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + M.debe - M.haber <0 THEN -1 * (coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + M.debe - M.haber) ELSE 0 END as finalacreedor
from get_hoja_trabajo_simple_registro(false, (""" + str(self.ejercicio.name) +"""::varchar ||'01')::integer,(""" + str(self.ejercicio.name) +"""::varchar ||'12')::integer) AS M
inner join account_account aa on aa.code = M.cuenta
FULL join (select aa.code_sunat as cuentaF,
CASE WHEN sum(O1.saldodeudor) - sum(O1.saldoacredor) > 0 THEN sum(O1.saldodeudor) - sum(O1.saldoacredor) ELSE 0 END as totaldebe,
CASE WHEN sum(O1.saldoacredor) - sum(O1.saldodeudor) > 0 THEN sum(O1.saldoacredor) - sum(O1.saldodeudor) ELSE 0 END as totalhaber   from get_hoja_trabajo_simple_registro(false, (""" + str(self.ejercicio.name) +"""::varchar ||'01')::integer,(""" + str(self.ejercicio.name) +"""::varchar ||'12')::integer) as O1
inner join account_account aa on aa.code = O1.cuenta
group by aa.code_sunat
order by aa.code_sunat) AS T on T.cuentaF = aa.code_sunat
) AS X
group by X.shiname ) AS CTX
FULL JOIN  ( select sht.debit, sht.credit, sht.account as cuenta  from ht_sunat_transference sht ) AS trans
on trans.cuenta = CTX.cuenta
order by CASE WHEN CTX.cuenta is not null THEN CTX.cuenta ELSE trans.cuenta END ) AS T where cuenta is not null
		)""")


		if self.tipo == 'pantalla':
			return {
				'name':'B. Comprobación',
			    "type": "ir.actions.act_window",
			    "res_model": "ht.sunat",
			    'view_mode': 'tree',
                'view_type': 'form',
			}

		if self.tipo == 'txt':

			self.env.cr.execute("""
				
				select * from (
				select  CASE WHEN CTX.cuenta is not null THEN CTX.cuenta ELSE trans.cuenta END as cuenta, coalesce(CTX.totaldebe,0) as debe_si, coalesce(CTX.totalhaber,0) as haber_si, coalesce(CTX.debe,0) as debe, coalesce(CTX.haber,0) as haber, coalesce(trans.debit,0) as debe_trans,coalesce(trans.credit,0) as haber_trans
from (
select X.shiname as cuenta,
sum(X.totaldebe) as totaldebe ,sum(X.totalhaber) as totalhaber,
sum(X.debe) as debe,sum(X.haber) as haber
from (select  M.*,T.* ,aa.code_sunat as shiname,
CASE WHEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + M.debe - M.haber >0 THEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + M.debe - M.haber ELSE 0 END as finaldeudor,
CASE WHEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + M.debe - M.haber <0 THEN -1 * (coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + M.debe - M.haber) ELSE 0 END as finalacreedor
from get_hoja_trabajo_simple_registro(false, (""" + str(self.ejercicio.name) +"""::varchar ||'01')::integer,(""" + str(self.ejercicio.name) +"""::varchar ||'12')::integer) AS M
inner join account_account aa on aa.code = M.cuenta
FULL join (select aa.code_sunat as cuentaF,
CASE WHEN sum(O1.saldodeudor) - sum(O1.saldoacredor) > 0 THEN sum(O1.saldodeudor) - sum(O1.saldoacredor) ELSE 0 END as totaldebe,
CASE WHEN sum(O1.saldoacredor) - sum(O1.saldodeudor) > 0 THEN sum(O1.saldoacredor) - sum(O1.saldodeudor) ELSE 0 END as totalhaber   from get_hoja_trabajo_simple_registro(false, (""" + str(self.ejercicio.name) +"""::varchar ||'01')::integer,(""" + str(self.ejercicio.name) +"""::varchar ||'12')::integer) as O1
inner join account_account aa on aa.code = O1.cuenta
group by aa.code_sunat
order by aa.code_sunat) AS T on T.cuentaF = aa.code_sunat
) AS X
group by X.shiname ) AS CTX
FULL JOIN  ( select sht.debit, sht.credit, sht.account as cuenta  from ht_sunat_transference sht ) AS trans
on trans.cuenta = CTX.cuenta
order by CASE WHEN CTX.cuenta is not null THEN CTX.cuenta ELSE trans.cuenta END ) AS T where cuenta is not null
			""")

			tra = self.env.cr.fetchall()
			
			
			import sys
			sys.setdefaultencoding('iso-8859-1')
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			rpta = ""
			for i in tra:
				rpta += i[0] + '|'+ "%0.2f" %i[1]+ '|'+ "%0.2f" %i[2]+ '|'+ "%0.2f" %i[3]+ '|'+ "%0.2f" %i[4]+ '|'+ "%0.2f" %i[5]+ '|'+ "%0.2f" %i[6] + "\n"

			xui = self.env['res.company'].search([])[0].partner_id.type_number
			vals = {
				'output_name': str(self.form_pdt) + str(xui) + str(self.ejercicio.name) + '.txt',
				'output_file': base64.encodestring(" " if rpta=="" else rpta),		
			}
			sfs_id = self.env['export.file.save'].create(vals)
			result = {}
			view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
			view_id = view_ref and view_ref[1] or False
			result = act_obj.read( [view_id] )
			print sfs_id
			return {
			    "type": "ir.actions.act_window",
			    "res_model": "export.file.save",
			    "views": [[False, "form"]],
			    "res_id": sfs_id.id,
			    "target": "new",
			}
		


	@api.multi
	def do_rebuilds(self):
		self.env.cr.execute(""" 

			DROP VIEW IF EXISTS ht_sunat;
			create or replace view ht_sunat as (

select row_number() OVER() as id,* from (
select CASE WHEN CTX.cuenta is not null THEN CTX.cuenta ELSE trans.cuenta END as cuenta, coalesce(CTX.totaldebe,0) as debe_si, coalesce(CTX.totalhaber,0) as haber_si, coalesce(CTX.debe,0) as debe, coalesce(CTX.haber,0) as haber, coalesce(trans.debit,0) as debe_trans,coalesce(trans.credit,0) as haber_trans
from (
select X.shiname as cuenta,
sum(X.totaldebe) as totaldebe ,sum(X.totalhaber) as totalhaber,
sum(X.debe) as debe,sum(X.haber) as haber
from (select  M.*,T.* ,aa.code_sunat as shiname,
CASE WHEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + M.debe - M.haber >0 THEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + M.debe - M.haber ELSE 0 END as finaldeudor,
CASE WHEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + M.debe - M.haber <0 THEN -1 * (coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + M.debe - M.haber) ELSE 0 END as finalacreedor
from get_hoja_trabajo_simple_registro(false, (""" + str(self.ejercicio.name) +"""::varchar ||'01')::integer,(""" + str(self.ejercicio.name) +"""::varchar ||'12')::integer) AS M
inner join account_account aa on aa.code = M.cuenta
FULL join (select aa.code_sunat as cuentaF,
CASE WHEN sum(O1.saldodeudor) - sum(O1.saldoacredor) > 0 THEN sum(O1.saldodeudor) - sum(O1.saldoacredor) ELSE 0 END as totaldebe,
CASE WHEN sum(O1.saldoacredor) - sum(O1.saldodeudor) > 0 THEN sum(O1.saldoacredor) - sum(O1.saldodeudor) ELSE 0 END as totalhaber   from get_hoja_trabajo_simple_registro(false, (""" + str(self.ejercicio.name) +"""::varchar ||'01')::integer,(""" + str(self.ejercicio.name) +"""::varchar ||'12')::integer) as O1
inner join account_account aa on aa.code = O1.cuenta
group by aa.code_sunat
order by aa.code_sunat) AS T on T.cuentaF = aa.code_sunat
) AS X
group by X.shiname ) AS CTX
FULL JOIN  ( select sht.debit, sht.credit, sht.account as cuenta  from ht_sunat_transference sht ) AS trans
on trans.cuenta = CTX.cuenta
order by CASE WHEN CTX.cuenta is not null THEN CTX.cuenta ELSE trans.cuenta END ) AS T where cuenta is not null


		)""")


		if self.tipo == 'pantalla':
			return {
				'name':'B. Comprobación',
			    "type": "ir.actions.act_window",
			    "res_model": "ht.sunat",
			    'view_mode': 'tree',
                'view_type': 'form',
			}

		if self.tipo == 'txt':

			self.env.cr.execute("""
				select * from (
				select  CASE WHEN CTX.cuenta is not null THEN CTX.cuenta ELSE trans.cuenta END as cuenta, coalesce(CTX.totaldebe,0) as debe_si, coalesce(CTX.totalhaber,0) as haber_si, coalesce(CTX.debe,0) as debe, coalesce(CTX.haber,0) as haber, coalesce(trans.debit,0) as debe_trans,coalesce(trans.credit,0) as haber_trans
from (
select X.shiname as cuenta,
sum(X.totaldebe) as totaldebe ,sum(X.totalhaber) as totalhaber,
sum(X.debe) as debe,sum(X.haber) as haber
from (select  M.*,T.* ,aa.code_sunat as shiname,
CASE WHEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + M.debe - M.haber >0 THEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + M.debe - M.haber ELSE 0 END as finaldeudor,
CASE WHEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + M.debe - M.haber <0 THEN -1 * (coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + M.debe - M.haber) ELSE 0 END as finalacreedor
from get_hoja_trabajo_simple_registro(false, (""" + str(self.ejercicio.name) +"""::varchar ||'01')::integer,(""" + str(self.ejercicio.name) +"""::varchar ||'12')::integer) AS M
inner join account_account aa on aa.code = M.cuenta
FULL join (select aa.code_sunat as cuentaF,
CASE WHEN sum(O1.saldodeudor) - sum(O1.saldoacredor) > 0 THEN sum(O1.saldodeudor) - sum(O1.saldoacredor) ELSE 0 END as totaldebe,
CASE WHEN sum(O1.saldoacredor) - sum(O1.saldodeudor) > 0 THEN sum(O1.saldoacredor) - sum(O1.saldodeudor) ELSE 0 END as totalhaber   from get_hoja_trabajo_simple_registro(false, (""" + str(self.ejercicio.name) +"""::varchar ||'01')::integer,(""" + str(self.ejercicio.name) +"""::varchar ||'12')::integer) as O1
inner join account_account aa on aa.code = O1.cuenta
group by aa.code_sunat
order by aa.code_sunat) AS T on T.cuentaF = aa.code_sunat
) AS X
group by X.shiname ) AS CTX
FULL JOIN  ( select sht.debit, sht.credit, sht.account as cuenta  from ht_sunat_transference sht ) AS trans
on trans.cuenta = CTX.cuenta
order by CASE WHEN CTX.cuenta is not null THEN CTX.cuenta ELSE trans.cuenta END ) AS T where cuenta is not null
			""")

			tra = self.env.cr.fetchall()
			
			
			import sys
			sys.setdefaultencoding('iso-8859-1')
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			rpta = ""
			for i in tra:
				rpta += i[0] + '|'+ "%0.2f" %i[1]+ '|'+ "%0.2f" %i[2]+ '|'+ "%0.2f" %i[3]+ '|'+ "%0.2f" %i[4]+ '|'+ "%0.2f" %i[5]+ '|'+ "%0.2f" %i[6] + "\n"

			xui = self.env['res.company'].search([])[0].partner_id.type_number
			vals = {
				'output_name': str(self.form_pdt) + str(xui) + str(self.ejercicio.name) + '.txt',
				'output_file': base64.encodestring(" " if rpta=="" else rpta),		
			}
			sfs_id = self.env['export.file.save'].create(vals)
			result = {}
			view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
			view_id = view_ref and view_ref[1] or False
			result = act_obj.read( [view_id] )
			print sfs_id
			return {
			    "type": "ir.actions.act_window",
			    "res_model": "export.file.save",
			    "views": [[False, "form"]],
			    "res_id": sfs_id.id,
			    "target": "new",
			}
		