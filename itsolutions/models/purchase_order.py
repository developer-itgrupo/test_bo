# coding=utf-8

from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_method = fields.Selection([
        ('purchase', 'Segun cantidades pedidas'),
        ('receive', 'Segun cantidades recibidas'),
    ], string="Control de facturas de compra",
        help="On ordered quantities: control bills based on ordered quantities.\n"
             "On received quantities: control bills based on received quantity.", default="receive")
