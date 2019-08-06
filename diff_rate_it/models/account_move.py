# -*- coding: utf-8 -*-

import time
from collections import OrderedDict
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, float_compare
from odoo.tools.safe_eval import safe_eval
import odoo.addons.decimal_precision as dp
from lxml import etree


class main_parameter(models.Model):
    _inherit = 'main.parameter'

    diferencia_cambio = fields.Boolean('Generar Diferencia de Cambio')


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"


    def _compute_partial_lines(self):
        if self._context.get('skip_full_reconcile_check'):
            #when running the manual reconciliation wizard, don't check the partials separately for full
            #reconciliation or exchange rate because it is handled manually after the whole processing
            return self
        #check if the reconcilation is full
        #first, gather all journal items involved in the reconciliation just created
        partial_rec_set = OrderedDict.fromkeys([x for x in self])
        aml_set = aml_to_balance = self.env['account.move.line']
        total_debit = 0
        total_credit = 0
        total_amount_currency = 0
        #make sure that all partial reconciliations share the same secondary currency otherwise it's not
        #possible to compute the exchange difference entry and it has to be done manually.
        currency = list(partial_rec_set)[0].currency_id
        maxdate = None

        for partial_rec in partial_rec_set:
            if partial_rec.currency_id != currency:
                #no exchange rate entry will be created
                currency = None
            for aml in [partial_rec.debit_move_id, partial_rec.credit_move_id]:
                if aml not in aml_set:
                    if aml.amount_residual or aml.amount_residual_currency:
                        aml_to_balance |= aml
                    maxdate = max(aml.date, maxdate)
                    total_debit += aml.debit
                    total_credit += aml.credit
                    aml_set |= aml
                    if aml.currency_id and aml.currency_id == currency:
                        total_amount_currency += aml.amount_currency
                    elif partial_rec.currency_id and partial_rec.currency_id == currency:
                        #if the aml has no secondary currency but is reconciled with other journal item(s) in secondary currency, the amount
                        #currency is recorded on the partial rec and in order to check if the reconciliation is total, we need to convert the
                        #aml.balance in that foreign currency
                        total_amount_currency += aml.company_id.currency_id.with_context(date=aml.date).compute(aml.balance, partial_rec.currency_id)
                for x in aml.matched_debit_ids | aml.matched_credit_ids:
                    partial_rec_set[x] = None
        partial_rec_ids = [x.id for x in partial_rec_set.keys()]
        aml_ids = aml_set.ids
        #then, if the total debit and credit are equal, or the total amount in currency is 0, the reconciliation is full
        digits_rounding_precision = aml_set[0].company_id.currency_id.rounding

        if (currency and float_is_zero(total_amount_currency, precision_rounding=currency.rounding)) or float_compare(total_debit, total_credit, precision_rounding=digits_rounding_precision) == 0:
            exchange_move_id = False
            exchange_partial_rec_id = False
            param = self.env['main.parameter'].search([])[0]
            if currency and aml_to_balance and param.diferencia_cambio:
                ####    Lineas comentadas para eliminar la diferencia de cambio     ###
                exchange_move = (self.env['account.move'].create(self.env['account.full.reconcile']._prepare_exchange_diff_move(move_date=maxdate, company=aml_to_balance[0].company_id)))
                #eventually create a journal entry to book the difference due to foreign currency's exchange rate that fluctuates
                rate_diff_amls, rate_diff_partial_recs = partial_rec._fix_multiple_exchange_rates_diff(aml_to_balance, total_debit - total_credit, total_amount_currency, currency, exchange_move)
                aml_ids += rate_diff_amls.ids
                partial_rec_ids += rate_diff_partial_recs.ids
                exchange_move.post()
                invoice_pers = None

                for partial_recT in partial_rec_set:
                    for amlT in [partial_recT.debit_move_id, partial_recT.credit_move_id]:
                        factura = self.env['account.invoice'].search([('move_id','=',amlT.move_id.id)])
                        if len(factura)>0:
                            invoice_pers = factura[0]
  
                for i in exchange_move.line_ids:
                    if invoice_pers and invoice_pers.id:
                        i.type_document_it = invoice_pers.it_type_document.id
                        i.nro_comprobante = invoice_pers.reference
                exchange_move_id = exchange_move.id
                exchange_partial_rec_id = rate_diff_partial_recs[-1:].id
            #mark the reference of the full reconciliation on the partial ones and on the entries
            self.env['account.full.reconcile'].with_context(check_move_validity=False).create({
                'partial_reconcile_ids': [(4, p_id) for p_id in partial_rec_ids],
                'reconciled_line_ids': [(4, a_id) for a_id in aml_ids],
                'exchange_move_id': exchange_move_id,
                'exchange_partial_rec_id': exchange_partial_rec_id,
            })
