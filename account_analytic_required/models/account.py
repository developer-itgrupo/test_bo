# -*- coding: utf-8 -*-
# © 2011-2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import _, api, exceptions, fields, models
from odoo.tools import float_is_zero
from datetime import *
from odoo.exceptions import UserError, ValidationError

class account_account_type_it(models.Model):
    _inherit = "account.account.type.it"

    analytic_policy = fields.Selection(
        selection=[('optional', 'Optional'),
                   ('always', 'Always'),
                   ('posted', 'Posted moves'),
                   ('never', 'Never')],
        string='Policy for analytic account',
        required=True,
        default='optional',
        help="Set the policy for analytic accounts : if you select "
             "'Optional', the accountant is free to put an analytic account "
             "on an account move line with this type of account ; if you "
             "select 'Always', the accountant will get an error message if "
             "there is no analytic account ; if you select 'Posted moves', "
             "the accountant will get an error message if no analytic account "
             "is defined when the move is posted ; if you select 'Never', "
             "the accountant will get an error message if an analytic account "
             "is present.")


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.multi
    def post(self):
        res = super(AccountMove, self).post()
        for i in self.line_ids:
            msg = i._check_analytic_required_msg()
            if msg:
                raise exceptions.ValidationError(msg)
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def _get_analytic_policy(self, account):
        """ Extension point to obtain analytic policy for an account """
        return account.type_it.analytic_policy

    @api.multi
    def _check_analytic_required_msg(self):
        for move_line in self:
            
            prec = move_line.company_currency_id.rounding
            if (float_is_zero(move_line.debit, precision_rounding=prec) and
                    float_is_zero(move_line.credit, precision_rounding=prec)):
                continue
            analytic_policy = self._get_analytic_policy(move_line.account_id)

            if (analytic_policy == 'always' and
                    not move_line.analytic_account_id.id):
                return _("Analytic policy is set to 'Always' with account "
                         "%s '%s' but the analytic account is missing in "
                         "the account move line with label '%s'."
                         ) % (move_line.account_id.code,
                              move_line.account_id.name,
                              move_line.name)
            elif (analytic_policy == 'never' and
                    move_line.analytic_account_id.id):
                return _("Analytic policy is set to 'Never' with account %s "
                         "'%s' but the account move line with label '%s' "
                         "has an analytic account '%s'."
                         ) % (move_line.account_id.code,
                              move_line.account_id.name,
                              move_line.name,
                              move_line.analytic_account_id.name_get()[0][1])
            elif (analytic_policy == 'posted' and
                  not move_line.analytic_account_id.id and
                  move_line.move_id.state == 'posted'):
                return _("Analytic policy is set to 'Posted moves' with "
                         "account %s '%s' but the analytic account is missing "
                         "in the account move line with label '%s'."
                         ) % (move_line.account_id.code,
                              move_line.account_id.name,
                              move_line.name)


class analytic_view_error(models.Model):
    _name = 'analytic.view.error'
    _auto = False


    period_id       = fields.Many2one('account.period','Periodo')
    journal_id      = fields.Many2one('account.journal','Libro')
    move_id         = fields.Many2one('account.move','Voucher')
    type_id         = fields.Many2one('account.account','Cuenta Financiera')
    partner_id      = fields.Many2one('res.partner','Partner')
    debit           = fields.Float('Debe')
    credit          = fields.Float('Haber')
    amount_currency = fields.Float('Monto ME')

    @api.model_cr
    def init(self):
        self.env.cr.execute(""" 

            drop view if exists analytic_view_error;
            create or replace view analytic_view_error as (

SELECT row_number() OVER () AS id,*  FROM ( 
                select ap.id as period_id, aj.id as journal_id, am.id as move_id, aa.id as type_id, rp.id as partner_id,aml.debit , aml.credit, aml.amount_currency  from account_move am
inner join res_partner rp on rp.id = am.partner_id
inner join account_journal aj on aj.id = am.journal_id
inner join account_move_line aml on aml.move_id = am.id
inner join account_account aa on aa.id = aml.account_id
inner join account_period ap on ap.special = am.fecha_special and ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable
inner join account_account_type_it aat on aat.id = aa.type_it
where am.state = 'posted' and (aat.analytic_policy in ('always','posted') and aml.analytic_Account_id is null) 
or (aat.analytic_policy = 'never' and aml.analytic_Account_id is not null)   ) T )

         """)



class analytic_view_error_wizard(models.Model):
    _name = 'analytic.view.error.wizard'

    period_ini = fields.Many2one('account.period','Periodo Inicial')
    period_fin = fields.Many2one('account.period','Periodo Final')

    @api.model
    def get_wizard(self):
      return self.env['automatic.fiscalyear'].get_wizard('No tiene Cta. Analitica',self.id,'analytic.view.error.wizard','account_analytic_required.view_analytic_view_error_wizard_form','default_period_ini','default_period_fin')

    @api.onchange('period_ini','period_fin')
    def _change_periodo_ini(self):
      fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
      year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
      if not year:
        raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
      if fiscalyear == 0:
        raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
      else:
        return {'domain':{'period_ini':[('fiscalyear_id','=',year.id )],'period_fin':[('fiscalyear_id','=',year.id )]}}

    @api.multi
    def do_rebuild(self):
        ids_f = [-1,-1]

        self.env.cr.execute("""
                select id from 
                account_period ap
                where periodo_num(ap.code) >= periodo_num('"""+str(self.period_ini.code)+"""')
                and
                periodo_num(ap.code) <= periodo_num('"""+str(self.period_fin.code)+"""')
            """)
        for i in self.env.cr.fetchall():
            ids_f.append(i[0])

        return {
                'domain' : [('period_id','in',ids_f)],
                'type': 'ir.actions.act_window',
                'res_model': 'analytic.view.error',
                'view_mode': 'tree',
                'view_type': 'form',
                'views': [(False, 'tree')],
        }