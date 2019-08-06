# -*- coding: utf-8 -*-

import time
from collections import OrderedDict
from odoo import api, fields, models, _, exceptions
from odoo.osv import expression
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, float_compare
from odoo.tools.safe_eval import safe_eval
import odoo.addons.decimal_precision as dp
from lxml import etree




class res_partner(models.Model):
    _inherit = "res.partner"


    @api.one
    @api.constrains('nro_documento','type_document_partner_it')
    def constrains_suplier_invoice_number(self):
        if self.nro_documento:
            if self.type_document_partner_it:
                filtro = []
                filtro.append( ('id','!=',self.id) )
                if self.type_document_partner_it:
                    filtro.append( ('type_document_partner_it','=',self.type_document_partner_it.id) )
                filtro.append( ('nro_documento','=', self.nro_documento) )
                
                m = self.env['res.partner'].with_context(active_test=False).search( filtro )
                if len(m) > 0:
                    raise exceptions.Warning(_("Número de Documento Duplicado ("+str(self.type_document_partner_it.code)+" - "+str(self.nro_documento)+")."))

                t = self.env['main.parameter'].search([])[0]
                if self.type_document_partner_it.id == t.sunat_type_document_ruc_id.id:
                    if t.l_ruc!= len(self.nro_documento):
                        raise exceptions.Warning(_("Número Invalido RUC"))                      

                if self.type_document_partner_it.id == t.sunat_type_document_dni_id.id:
                    if t.l_dni!= len(self.nro_documento):
                        raise exceptions.Warning(_("Número Invalido DNI"))

