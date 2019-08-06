# -*- coding: utf-8 -*-
# Copyright 2009 Pexego Sistemas Informáticos. All Rights Reserved
# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import date
from odoo import _, api, exceptions, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import *

_logger = logging.getLogger(__name__)


class WizardRenumber(models.TransientModel):
    _name = "wizard.renumber"
    _description = "Account renumber wizard"

    def get_period(self):
        fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
        year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
        if not year:
            raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
        if fiscalyear == 0:
            raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
        else:
            periodos = self.env['account.period'].search([('fiscalyear_id','=',year.id)])
            periodos = filter(lambda period: not period.special and datetime.strptime(period.date_start,"%Y-%m-%d").month == datetime.now().month,periodos)
            periodos = periodos[0].id if len(periodos) > 0 else 0
            return periodos

    periodo = fields.Many2one('account.period','Periodo',default=lambda self:self.get_period())
    journal_id = fields.Many2one('account.journal',"Diario",required=True)
    
    @api.onchange('periodo')
    def onchange_fiscalyear(self):
        fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
        year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
        if not year:
            raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
        if fiscalyear == 0:
            raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
        else:
            return {'domain':{'periodo':[('fiscalyear_id','=',year.id )]}}

    @api.multi
    def renumber(self):

        sequence = self.journal_id.sequence_id

        self.env.cr.execute(""" 

        update account_move set name =  '"""+str(self.periodo.code.split('/')[0])+"""' || '-' || LPAD(T.CORRELATIVO::text,""" +str(sequence.padding)+ """,'0')  from (
SELECT row_number() OVER () AS CORRELATIVO,* FROM (
SELECT  ID,DATE,FECHA_CONTABLE,NAME,REF,JOURNAL_ID FROM  ACCOUNT_MOVE 
WHERE FECHA_CONTABLE BETWEEN '""" +str(self.periodo.date_start)+ """' AND '""" +str(self.periodo.date_stop)+ """'
AND JOURNAL_ID=""" +str(self.journal_id.id)+ """
ORDER BY FECHA_CONTABLE, ref ,LEFT(NAME,2)
)TT  ) T where T.id = account_move.id

            """)

        self.env.cr.execute("""
            select max(CORRELATIVO)+1 from (
                SELECT row_number() OVER () AS CORRELATIVO,* FROM (
SELECT  ID,DATE,FECHA_CONTABLE,NAME,REF,JOURNAL_ID FROM  ACCOUNT_MOVE 
WHERE FECHA_CONTABLE BETWEEN '""" +str(self.periodo.date_start)+ """' AND '""" +str(self.periodo.date_stop)+ """'
AND JOURNAL_ID=""" +str(self.journal_id.id)+ """
ORDER BY FECHA_CONTABLE,LEFT(NAME,2)
)TT ) X
         """)

        res = self.env.cr.fetchall()

        default = 1
        for i in res:
            default = i[0]


        if sequence.use_date_range:
            date_range = self.env["ir.sequence.date_range"].search(
                [("sequence_id", "=", sequence.id),
                 ("date_from", "=", self.periodo.date_start),
                 ("date_to", ">=", self.periodo.date_stop)]
            )
            if len(date_range)>1:
                raise exceptions.MissingError( _('Existe dos intervalos de fecha que se cruzan en el diario ' + self.journal_id.name))
            else:
                date_range[0].number_next_actual = default
                date_range[0].number_next = default

        else:
            sequence.number_next_actual = default


        self.env.cr.execute("""

update account_invoice set move_name =  T.NAME  from (
SELECT row_number() OVER () AS CORRELATIVO,* FROM (
SELECT  ID,DATE,FECHA_CONTABLE,NAME,REF,JOURNAL_ID FROM  ACCOUNT_MOVE 
WHERE FECHA_CONTABLE BETWEEN '""" +str(self.periodo.date_start)+ """' AND '""" +str(self.periodo.date_stop)+ """'
AND JOURNAL_ID=""" +str(self.journal_id.id)+ """
ORDER BY FECHA_CONTABLE,LEFT(NAME,2)
)TT  ) T where T.id = account_invoice.move_id


            """)




        self.env.cr.execute("""

update account_payment set move_name =  T.NAME,payment_reference = T.NAME  from (

SELECT row_number() OVER () AS CORRELATIVO,* FROM (
SELECT  ap.ID,am.NAME FROM  ACCOUNT_MOVE am
INNER JOIN  ACCOUNT_MOVE_LINE aml on aml.move_id = am.id
INNER JOIN account_payment ap on ap.id = aml.payment_id
WHERE am.FECHA_CONTABLE BETWEEN '""" +str(self.periodo.date_start)+ """' AND '""" +str(self.periodo.date_stop)+ """'
AND am.JOURNAL_ID=""" +str(self.journal_id.id)+ """
ORDER BY am.FECHA_CONTABLE,LEFT(am.NAME,2)
)TT  ) T where T.id = account_payment.id


            """)



        self.env.cr.execute("""

update account_bank_statement_line set move_name =  T.NAME  from (
SELECT row_number() OVER () AS CORRELATIVO,* FROM (
SELECT  statement_line_id as ID,DATE,FECHA_CONTABLE,NAME,REF,JOURNAL_ID FROM  ACCOUNT_MOVE 
WHERE FECHA_CONTABLE BETWEEN '""" +str(self.periodo.date_start)+ """' AND '""" +str(self.periodo.date_stop)+ """'
AND JOURNAL_ID=""" +str(self.journal_id.id)+ """
 and statement_line_id is not null
ORDER BY FECHA_CONTABLE,LEFT(NAME,2)
)TT  ) T where T.id = account_bank_statement_line.id


            """)

        lineas = []


        #self.env.cr.execute("""
            
                
        #    SELECT  ID,DATE,FECHA_CONTABLE,NAME,REF,JOURNAL_ID FROM  ACCOUNT_MOVE 
        #    WHERE FECHA_CONTABLE BETWEEN '""" +str(self.periodo.date_start)+ """' AND '""" +str(self.periodo.date_stop)+ """'
        #    AND JOURNAL_ID=""" +str(self.journal_id.id)+ """
        #        ORDER BY FECHA_CONTABLE,LEFT(NAME,2)

        # """)

        #for i in self.env.cr.fetchall():
        #    lineas.append(i[0])


        #return {
        #    'type': 'ir.actions.act_window',
        #    'name': _("Renumbered account moves"),
        #    'res_model': 'account.move',
        #    'domain': [("id", "in", lineas)],
        #    'view_type': 'form',
        #    'view_mode': 'tree',
        #    'context': self.env.context,
        #    'target': 'current',
        #}

        contextn = dict(self._context or {})
        contextn['message']="Generado Exitosamente"
        return {
                'name':'Finalizado',
                'type':'ir.actions.act_window',
                'view_type':'form',
                'view_mode':'form',
                'res_model':'sh.message.wizard',
                'views': [(False,'form')],
                'target':'new',
                'context':contextn,
        }
