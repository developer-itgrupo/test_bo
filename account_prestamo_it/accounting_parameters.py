# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

class MainParameter(models.Model):
    _inherit = 'main.parameter'

    account_amortizacion_capital_id = fields.Many2one('account.account','Cuenta Amortizacion Capital')
    account_interes_id = fields.Many2one('account.account','Cuenta Interes')
    account_itf_id = fields.Many2one('account.account','Cuenta de ITF')
    account_mora_id = fields.Many2one('account.account','Cuenta de Mora')
    journal_asiento_devengo_id = fields.Many2one('account.journal','Diario para Asiento Devengo')
    catalog_comprobante_pago_id = fields.Many2one('einvoice.catalog.01','Tipo de Comprobante de Pago')
    account_cargo_devengo_id = fields.Many2one('account.account','Cuenta Cargo Devengo')
    account_abono_devengo_id = fields.Many2one('account.account','Cuenta Abono Devengo')