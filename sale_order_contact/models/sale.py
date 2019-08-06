# -*- encoding: utf-8 -*-

from odoo import models, fields, api

class sale_order(models.Model):
    _inherit = 'sale.order'

    partner_order_id = fields.Many2one('res.partner', 'Ordering Contact', domain=[('is_company', '=', False)])

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id_(self):
        if self.partner_id:
            #vals = super(sale_order, self).onchange_partner_id()
            #partner = self.env['res.partner'].search([('id', '=', self.partner_id)])
            #for child in self.partner_id.child_ids:
            #    if child.type == 'contact':
            #        print vals
            #        print child
            #        print child.id
            #        vals['value']['partner_order_id'] = child.id
            #        return vals
            #if self.partner_id.child_ids:
            #    vals['value']['partner_order_id'] = self.partner_id.child_ids[0].id
            #return vals
            if self.partner_id.child_ids:
                self.partner_order_id = self.partner_id.child_ids[0].id
