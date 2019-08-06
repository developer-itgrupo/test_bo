# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
import base64
from openerp.osv import osv
from openerp import netsvc
from datetime import *
from odoo.exceptions import UserError, ValidationError



class account_analisis_meses(models.Model):
	_name = 'account.analisis.meses'
	_auto = False

	cuenta = fields.Char('Cuenta')
	descrip = fields.Char('Nomenclatura')
	apertura = fields.Float('Apertura',digits=(12,2))
	enero = fields.Float('Enero',digits=(12,2))
	febrero = fields.Float('Febrero',digits=(12,2))
	marzo = fields.Float('Marzo',digits=(12,2))
	abril = fields.Float('Abril',digits=(12,2))
	mayo = fields.Float('Mayo',digits=(12,2))
	junio = fields.Float('Junio',digits=(12,2))
	julio = fields.Float('Julio',digits=(12,2))
	agosto = fields.Float('Agosto',digits=(12,2))
	setiembre = fields.Float('Septiembre',digits=(12,2))
	octubre = fields.Float('Octubre',digits=(12,2))
	noviembre = fields.Float('Noviembre',digits=(12,2))
	diciembre = fields.Float('Diciembre',digits=(12,2))
	total = fields.Float('Total',digits=(12,2))

	_order = 'cuenta'

class account_analisis_meses_wizard(models.Model):
	_name = 'account.analisis.meses.wizard'

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
	tipo = fields.Selection([('balance','Balance'),('registro','Registro')],'Tipo',required=True)
	

	@api.multi
	def do_rebuild(self):
		#fiscal_year = self.fiscalyear_id.name
		ft = self.env['account.period'].search([('code','=','00/'+ self.fiscalyear_id.name)])
		f0 = ft if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','01/'+ self.fiscalyear_id.name)])
		f1 = ft if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','02/'+ self.fiscalyear_id.name)])
		f2 = ft if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','03/'+ self.fiscalyear_id.name)])
		f3 =  ft if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','04/'+ self.fiscalyear_id.name)])
		f4 =  ft if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','05/'+ self.fiscalyear_id.name)])
		f5 =  ft if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','06/'+ self.fiscalyear_id.name)])
		f6 =  ft if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','07/'+ self.fiscalyear_id.name)])
		f7 =  ft if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','08/'+ self.fiscalyear_id.name)])
		f8 =  ft if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','09/'+ self.fiscalyear_id.name)])
		f9 =  ft if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','10/'+ self.fiscalyear_id.name)])
		f10 =  ft if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','11/'+ self.fiscalyear_id.name)])
		f11 =  ft if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','12/'+ self.fiscalyear_id.name)])
		f12 =  ft if len(ft)>0 else '0'


		#where t1.user_type_id<>35) saldos

		if self.tipo == 'registro':

			self.env.cr.execute(""" drop view if exists account_analisis_meses;
			CREATE OR REPLACE view account_analisis_meses as (
				select iden as id,cuenta,descripcion as descrip,apertura,enero,febrero,marzo,abril,mayo,junio,julio,agosto,setiembre,octubre,noviembre,diciembre, (apertura+enero+febrero+marzo+abril+mayo+junio+julio+agosto+setiembre+octubre+noviembre+diciembre) as total from (
select c1.id as iden,c1.code as cuenta,c1.name as descripcion,c1.user_type_id as tipo,
coalesce (saldo00,0) as APERTURA,
coalesce (saldo01,0) as ENERO,
coalesce (saldo02,0) as FEBRERO,
coalesce (saldo03,0) as MARZO,
coalesce (saldo04,0) as ABRIL,
coalesce (saldo05,0) as MAYO,
coalesce (saldo06,0) as JUNIO,
coalesce (saldo07,0) as JULIO,
coalesce (saldo08,0) as AGOSTO,
coalesce (saldo09,0) as SETIEMBRE,
coalesce (saldo10,0) as OCTUBRE,
coalesce (saldo11,0) as NOVIEMBRE,
coalesce (saldo12,0) as DICIEMBRE
from account_account c1
left join(select account_id,sum(debit)-sum(credit) as saldo00 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and extract(month from am.fecha_contable)='01' and coalesce(am.fecha_special,false) = true group by account_id) t0 on t0.account_id=c1.id
left join(select account_id,sum(debit)-sum(credit) as saldo01 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and extract(month from am.fecha_contable)='01' and coalesce(am.fecha_special,false) = false group by account_id) t1 on t1.account_id=c1.id
left join(select account_id,sum(debit)-sum(credit) as saldo02 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and extract(month from am.fecha_contable)='02' group by account_id) t3 on t3.account_id=c1.id
left join(select account_id,sum(debit)-sum(credit) as saldo03 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and extract(month from am.fecha_contable)='03' group by account_id) t4 on t4.account_id=c1.id
left join(select account_id,sum(debit)-sum(credit) as saldo04 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and extract(month from am.fecha_contable)='04' group by account_id) t5 on t5.account_id=c1.id
left join(select account_id,sum(debit)-sum(credit) as saldo05 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and extract(month from am.fecha_contable)='05' group by account_id) t6 on t6.account_id=c1.id
left join(select account_id,sum(debit)-sum(credit) as saldo06 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and extract(month from am.fecha_contable)='06' group by account_id) t7 on t7.account_id=c1.id
left join(select account_id,sum(debit)-sum(credit) as saldo07 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and extract(month from am.fecha_contable)='07' group by account_id) t8 on t8.account_id=c1.id
left join(select account_id,sum(debit)-sum(credit) as saldo08 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and extract(month from am.fecha_contable)='08' group by account_id) t9 on t9.account_id=c1.id
left join(select account_id,sum(debit)-sum(credit) as saldo09 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and extract(month from am.fecha_contable)='09' group by account_id) t10 on t10.account_id=c1.id
left join(select account_id,sum(debit)-sum(credit) as saldo10 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and extract(month from am.fecha_contable)='10' group by account_id) t11 on t11.account_id=c1.id
left join(select account_id,sum(debit)-sum(credit) as saldo11 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and extract(month from am.fecha_contable)='11' group by account_id) t12 on t12.account_id=c1.id
left join(select account_id,sum(debit)-sum(credit) as saldo12 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and extract(month from am.fecha_contable)='12' group by account_id) t13 on t13.account_id=c1.id
where (select type from account_account_type where id=c1.user_type_id)<>'view') saldos
where (apertura != 0 or enero != 0 or febrero!= 0 or marzo!= 0 or abril!= 0 or mayo!= 0 or junio!= 0 or julio != 0 or agosto != 0 or setiembre != 0 or octubre != 0 or noviembre != 0 or diciembre != 0  )
order by cuenta
		)     """)
		else:

			self.env.cr.execute(""" drop view if exists account_analisis_meses;
			CREATE OR REPLACE view account_analisis_meses as (
				select row_number() OVER () AS id, left(cuenta,2) as cuenta, aa.name as descrip, sum(apertura) as apertura,sum(enero)as enero,
sum(febrero) as febrero, sum(marzo) as marzo, sum(abril) as abril, sum(mayo) as mayo, sum(junio) as junio, sum(julio) as julio,
sum(agosto) as agosto, sum(setiembre) as setiembre,sum(octubre) as octubre, sum(noviembre) as noviembre, sum(diciembrE) as diciembre, sum(total) as total
 from (
				select iden as id,cuenta,descripcion,apertura,enero,febrero,marzo,abril,mayo,junio,julio,agosto,setiembre,octubre,noviembre,diciembre, (apertura+enero+febrero+marzo+abril+mayo+junio+julio+agosto+setiembre+octubre+noviembre+diciembre) as total from (
select t1.id as iden,t1.code as cuenta,t1.name as descripcion,t1.user_type_id as tipo,
coalesce (saldo00,0) as APERTURA,
coalesce (saldo01,0) as ENERO,
coalesce (saldo02,0) as FEBRERO,
coalesce (saldo03,0) as MARZO,
coalesce (saldo04,0) as ABRIL,
coalesce (saldo05,0) as MAYO,
coalesce (saldo06,0) as JUNIO,
coalesce (saldo07,0) as JULIO,
coalesce (saldo08,0) as AGOSTO,
coalesce (saldo09,0) as SETIEMBRE,
coalesce (saldo10,0) as OCTUBRE,
coalesce (saldo11,0) as NOVIEMBRE,
coalesce (saldo12,0) as DICIEMBRE

from account_account t1
left join(select account_id,sum(debit)-sum(credit) as saldo00 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and am.fecha_contable>='"""+str(f0.date_start)+"""' and coalesce(am.fecha_special,false) = true and am.fecha_contable<='"""+str(f0.date_stop)+"""' group by account_id) t0 on t0.account_id=t1.id
left join(select account_id,sum(debit)-sum(credit) as saldo01 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and am.fecha_contable>='"""+str(f1.date_start)+"""' and coalesce(am.fecha_special,false) = false and am.fecha_contable<='"""+str(f1.date_stop)+"""' group by account_id) t2 on t2.account_id=t1.id
left join(select account_id,sum(debit)-sum(credit) as saldo02 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and am.fecha_contable>='"""+str(f2.date_start)+"""' and coalesce(am.fecha_special,false) = false and am.fecha_contable<='"""+str(f2.date_stop)+"""' group by account_id) t3 on t3.account_id=t1.id
left join(select account_id,sum(debit)-sum(credit) as saldo03 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and am.fecha_contable>='"""+str(f3.date_start)+"""' and coalesce(am.fecha_special,false) = false and am.fecha_contable<='"""+str(f3.date_stop)+"""' group by account_id) t4 on t4.account_id=t1.id
left join(select account_id,sum(debit)-sum(credit) as saldo04 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and am.fecha_contable>='"""+str(f4.date_start)+"""' and coalesce(am.fecha_special,false) = false and am.fecha_contable<='"""+str(f4.date_stop)+"""' group by account_id) t5 on t5.account_id=t1.id
left join(select account_id,sum(debit)-sum(credit) as saldo05 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and am.fecha_contable>='"""+str(f5.date_start)+"""' and coalesce(am.fecha_special,false) = false and am.fecha_contable<='"""+str(f5.date_stop)+"""' group by account_id) t6 on t6.account_id=t1.id
left join(select account_id,sum(debit)-sum(credit) as saldo06 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and am.fecha_contable>='"""+str(f6.date_start)+"""' and coalesce(am.fecha_special,false) = false and am.fecha_contable<='"""+str(f6.date_stop)+"""' group by account_id) t7 on t7.account_id=t1.id
left join(select account_id,sum(debit)-sum(credit) as saldo07 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and am.fecha_contable>='"""+str(f7.date_start)+"""' and coalesce(am.fecha_special,false) = false and am.fecha_contable<='"""+str(f7.date_stop)+"""' group by account_id) t8 on t8.account_id=t1.id
left join(select account_id,sum(debit)-sum(credit) as saldo08 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and am.fecha_contable>='"""+str(f8.date_start)+"""' and coalesce(am.fecha_special,false) = false and am.fecha_contable<='"""+str(f8.date_stop)+"""' group by account_id) t9 on t9.account_id=t1.id
left join(select account_id,sum(debit)-sum(credit) as saldo09 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and am.fecha_contable>='"""+str(f9.date_start)+"""' and coalesce(am.fecha_special,false) = false and am.fecha_contable<='"""+str(f9.date_stop)+"""' group by account_id) t10 on t10.account_id=t1.id
left join(select account_id,sum(debit)-sum(credit) as saldo10 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and am.fecha_contable>='"""+str(f10.date_start)+"""' and coalesce(am.fecha_special,false) = false and am.fecha_contable<'="""+str(f10.date_stop)+"""' group by account_id) t11 on t11.account_id=t1.id
left join(select account_id,sum(debit)-sum(credit) as saldo11 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and am.fecha_contable>='"""+str(f11.date_start)+"""' and coalesce(am.fecha_special,false) = false and am.fecha_contable<='"""+str(f11.date_stop)+"""' group by account_id) t12 on t12.account_id=t1.id
left join(select account_id,sum(debit)-sum(credit) as saldo12 from account_move_line aml inner join account_move am on am.id = aml.move_id  where am.state != 'draft' and am.fecha_contable>='"""+str(f12.date_start)+"""' and coalesce(am.fecha_special,false) = false and am.fecha_contable<='"""+str(f12.date_stop)+"""' group by account_id) t13 on t13.account_id=t1.id


where (select type from account_account_type where id=t1.user_type_id)<>'view') saldos

where (apertura!=0 or enero != 0 or febrero!= 0 or marzo!= 0 or abril!= 0 or mayo!= 0 or junio!= 0 or julio != 0 or agosto != 0 or setiembre != 0 or octubre != 0 or noviembre != 0 or diciembre != 0  )
order by cuenta
)as T 
left join account_account aa on aa.code = left(T.cuenta,2)
group by left(T.cuenta,2),aa.name
		)     """)

		return {
			'type': 'ir.actions.act_window',
			'res_model': 'account.analisis.meses',
			'view_mode': 'tree',
			'view_type': 'form',			
		}

