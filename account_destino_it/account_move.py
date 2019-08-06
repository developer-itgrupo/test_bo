# -*- coding: utf-8 -*-

from openerp import models, fields, api , exceptions , _

class account_analitica_destino(models.Model):
	_name = 'account.analitica.destino'
	_auto = False
	
	cta_destino_debe = fields.Char('Cuenta Destino Debe')
	cta_destino_haber = fields.Char('Cuenta Destino Haber')
	debe = fields.Float('Debe', digits=(12,2))
	haber = fields.Float('Haber', digits=(12,2))
	origen = fields.Char('Origen')


class account_analytic_destino(models.Model):
	_name = 'account.analytic.destino'
	_auto = False

	am_id = fields.Many2one('account.move','Asiento Contable')
	cuenta = fields.Many2one('account.account','Cuenta')
	debe = fields.Float('Debe', digits=(12,2))
	haber = fields.Float('Haber', digits=(12,2))

	@api.model_cr    
	def init(self):
		self.env.cr.execute("""
			DROP VIEW IF EXISTS account_analytic_destino;
create or replace view account_analytic_destino as (


select row_number() OVER() as id,*
from(
select am_id,cuenta, period, 
CASE WHEN debe-haber>0 THEN debe-haber else 0 END as debe,
CASE WHEN -debe+haber>0 THEN -debe+haber else 0 END as haber from 
(
select 
account_move.id as am_id,
aa3.id as cuenta,
account_period.id as period,
case when sum(account_move_line.debit) - sum(account_move_line.credit) > 0 then sum(account_move_line.debit) - sum(account_move_line.credit)
else 0 end as debe,
case when sum(account_move_line.debit) - sum(account_move_line.credit) > 0 then 0
else -sum(account_move_line.debit) + sum(account_move_line.credit) end as haber
from account_move
inner join account_period on account_period.date_start <= account_move.fecha_contable and account_period.date_stop >= account_move.fecha_contable
inner join account_journal on account_move.journal_id = account_journal.id
inner join account_move_line on account_move_line.move_id = account_move.id   ----154
inner join account_account aa1 on aa1.id = account_move_line.account_id
inner join account_account_type aat on aat.id = aa1.user_type_id
left join account_analytic_account on account_analytic_account.id = account_move_line.analytic_account_id
inner join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
inner join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)
where account_move.state = 'posted' and account_journal.type <> 'sale' and account_journal.type <> 'sale_refund'
and aa2.id is not null and aa3.id is not null and account_analytic_account.id is null 
and aat.type != 'view'
group by account_period.id,account_move.id, aa3.id

union all


select 
am.id as am_id,
aa3.id as cuenta,
ap.id as period,

case when aal.amount > 0 then 0
else -1*aal.amount end as debe,

case when aal.amount > 0 then aal.amount
else 0 end as haber

from account_analytic_line aal
inner join account_account aa1 on aa1.id = aal.general_account_id
inner join account_move_line aml on aml.id = aal.move_id
inner join account_move am on am.id = aml.move_id
left join account_analytic_account on account_analytic_account.id = aal.account_id
inner join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
inner join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)
inner join account_period ap on ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable
where aa1.check_moorage = True


union all


select 
am.id as am_id,
aa2.id as cuenta,
ap.id as period,

case when aal.amount > 0 then aal.amount
else 0 end as debe,

case when aal.amount > 0 then 0
else -1*aal.amount end as haber


from account_analytic_line aal
inner join account_account aa1 on aa1.id = aal.general_account_id
inner join account_move_line aml on aml.id = aal.move_id
inner join account_move am on am.id = aml.move_id
left join account_analytic_account on account_analytic_account.id = aal.account_id
inner join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
inner join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)
inner join account_period ap on ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable
where aa1.check_moorage = True


union all
select 
account_move.id as am_id,
aa2.id as cuenta,
account_period.id as period,
case when sum(account_move_line.debit) - sum(account_move_line.credit) > 0 then 0
else -sum(account_move_line.debit) + sum(account_move_line.credit) end as debe,
case when sum(account_move_line.debit) - sum(account_move_line.credit) > 0 then sum(account_move_line.debit) - sum(account_move_line.credit)
else 0 end as haber

from account_move
inner join account_period on account_period.date_start <= account_move.fecha_contable and account_period.date_stop >= account_move.fecha_contable
inner join account_journal on account_move.journal_id = account_journal.id
inner join account_move_line on account_move_line.move_id = account_move.id   ----154
inner join account_account aa1 on aa1.id = account_move_line.account_id
inner join account_account_type aat on aat.id = aa1.user_type_id
left join account_analytic_account on account_analytic_account.id = account_move_line.analytic_account_id
inner join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
inner join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)
where account_move.state = 'posted' and account_journal.type <> 'sale' and account_journal.type <> 'sale_refund'
and aa2.id is not null and aa3.id is not null and account_analytic_account.id is null 
and aat.type != 'view'
group by account_period.id,account_move.id, aa2.id

order by period,am_id,haber,debe
) AS M

order by period,am_id,haber,debe
) AS T
)""")

class account_move(models.Model):
	_inherit = 'account.move'
	

	analytic_lines_id = fields.One2many('account.analytic.destino', 'am_id', 'Destino', copy=False)

	@api.one
	def button_cancel(self):
		for i in self.line_ids:
			t = self.env['account.analytic.line'].search([('move_id','=',i.id)])
			for j in t:
				j.unlink()

		return super(account_move,self).button_cancel()
		
	@api.multi
	def ver_destinos(self):
		self.env.cr.execute(""" 
			DROP VIEW IF EXISTS account_analitica_destino;
create or replace view account_analitica_destino as (
select 
row_number() OVER() as id,
am_debe as cta_destino_debe,
am_haber as cta_destino_haber,
debe::numeric(24,2),
haber::numeric(24,2),
cuenta as origen
from (

select 
a1.move_id,
a2.code as cuenta,
case when a3.code is null then a7.code else a3.code end as am_debe,
case when a4.code is null then a8.code else a4.code end as am_haber,
case when a3.code is not null then a1.debit else (case when a5.amount < 0 then -a5.amount else 0 end) end as debe,
case when a4.code is not null then a1.credit else (case when a5.amount > 0 then a5.amount else 0 end) end as haber   
from account_move_line a1
left join account_account a2 on a2.id=a1.account_id
left join account_account a3 on a3.id=a2.account_analytic_account_moorage_debit_id
left join account_account a4 on a4.id=a2.account_analytic_account_moorage_id
left join account_analytic_line a5 on a5.move_id=a1.id
left join account_analytic_account a6 on a6.id=a5.account_id
left join account_account a7 on a7.id=a6.account_account_moorage_id
left join account_account a8 on a8.id=a6.account_account_moorage_credit_id
where a1.move_id=""" +str(self.id)+ """ 
order by debit desc,a2.code)tt
where (am_debe||am_haber) is not null
) """)
		
		return {
					'name': 'Destinos',
					'view_type': 'form',
					'view_mode': 'tree',
					'res_model': 'account.analitica.destino',
					'type': 'ir.actions.act_window',
					'target': 'new',
		}