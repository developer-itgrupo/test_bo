# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

class MainParameter(models.Model):
    _inherit = 'main.parameter'

    account_capital_id = fields.Many2one('account.account','Cuenta Capital')
    account_gastos_id = fields.Many2one('account.account','Cuenta Gastos')
    account_comision_id = fields.Many2one('account.account','Cuenta Comision')
    account_seguro_id = fields.Many2one('account.account','Seguro')
    account_intereses_id = fields.Many2one('account.account','Intereses')
    account_cargo_devengamiento_id = fields.Many2one('account.account','Cuenta Cargo Devengamiento')
    account_abono_devengamiento_id = fields.Many2one('account.account','Cuenta Abono Devengamiento')
    account_cargo_interes_monetario_id = fields.Many2one('account.account','Cuenta Cargo Interes Monetario')
    journal_asiento_compra_id = fields.Many2one('account.journal','Diario Asiento de Devengo')
    catalog_comprobante_cuotas_id = fields.Many2one('einvoice.catalog.01','Tipo de Comprobante Cuotas')
    
    tax_capital = fields.Many2one('account.tax','Impuesto Capital')
    tax_gastos = fields.Many2one('account.tax','Impuesto Gastos')
    tax_comision = fields.Many2one('account.tax','Impuesto Comision')
    tax_seguro = fields.Many2one('account.tax','Impuesto Seguro')
    tax_intereses = fields.Many2one('account.tax','Impuesto Intereses')
    tax_cargo_devengamiento = fields.Many2one('account.tax','Impuesto Cargo Devengamiento')
    tax_abono_devengamiento = fields.Many2one('account.tax','Impuesto Abono Devengamiento')
    tax_interes_monetario = fields.Many2one('account.tax','Impuesto Interes Monetario')