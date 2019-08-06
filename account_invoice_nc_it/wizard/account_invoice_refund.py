# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError


class AccountInvoiceRefund(models.TransientModel):
    _inherit = 'account.invoice.refund'
    # type_document_id = fields.Many2one('einvoice.catalog.01','Tipo documento')
    nro_comprobante = fields.Char(string='Nro. Comprobante')
    serie_id = fields.Many2one('it.invoice.serie','Serie')
    serie_visible = fields.Boolean('Serie visible',compute="get_serie_visible")

    @api.one
    @api.depends('filter_refund')
    def get_serie_visible(self):
        t = False
        g = self.env.context.get('active_ids',[])
        facturas = self.env['account.invoice'].browse(g)
        if len(facturas)>0:
            if facturas[0].type == 'out_invoice':
                t = True
        self.serie_visible = t


    @api.onchange('nro_comprobante')
    def _changed_comprobante(self):
        parametro = self.env['main.parameter'].search([], limit=1)
        if self.nro_comprobante and parametro and parametro.type_document_id:
            tipo_doc = parametro.type_document_id
            self.nro_comprobante = str(self.nro_comprobante).replace(' ', '')

            if self.nro_comprobante and tipo_doc.id:
                self.nro_comprobante = str(self.nro_comprobante).replace(' ', '')
                t = self.nro_comprobante.split('-')
                n_serie = 0
                n_documento = 0
                self.env.cr.execute(
                    "select coalesce(n_serie,0), coalesce(n_documento,0) from einvoice_catalog_01 where id = " + str(
                        tipo_doc.id))

                forelemn = self.env.cr.fetchall()
                for ielem in forelemn:
                    n_serie = ielem[0]
                    n_documento = ielem[1]
                if len(t) == 2:
                    parte1 = t[0]
                    if len(t[0]) < n_serie:
                        for i in range(0, n_serie - len(t[0])):
                            parte1 = '0' + parte1
                    parte2 = t[1]
                    if len(t[1]) < n_documento:
                        for i in range(0, n_documento - len(t[1])):
                            parte2 = '0' + parte2
                    self.nro_comprobante = parte1 + '-' + parte2
                elif len(t) == 1:
                    parte2 = t[0]
                    if len(t[0]) < n_documento:
                        for i in range(0, n_documento - len(t[0])):
                            parte2 = '0' + parte2
                    self.nro_comprobante = parte2
                else:
                    pass

    @api.multi
    def compute_refund(self, mode='refund'):
        inv_obj = self.env['account.invoice']
        inv_tax_obj = self.env['account.invoice.tax']
        inv_line_obj = self.env['account.invoice.line']
        context = dict(self._context or {})
        xml_id = False

        for form in self:
            created_inv = []
            date = False
            description = False
            type_document_id = False
            nro_comprobante = False
            for inv in inv_obj.browse(context.get('active_ids')):
                if inv.state in ['draft', 'proforma2', 'cancel']:
                    raise UserError(_('Cannot refund draft/proforma/cancelled invoice.'))
                if inv.reconciled and mode in ('cancel', 'modify'):
                    raise UserError(_(
                        'Cannot refund invoice which is already reconciled, invoice should be unreconciled first. You can only refund this invoice.'))

                date = form.date or False
                description = form.description or inv.name
                #type_document_id = self.env['einvoice.catalog.01'].search([('code','=','08')],limit=1)
                parametro = self.env['main.parameter'].search([],limit=1)
                if parametro and parametro.type_document_id:
                    type_document_id = parametro.type_document_id
                else:
                    raise UserError(_('Falta configurar la nota de credito nacional.'))

                nro_comprobante = form.nro_comprobante or False
                refund = inv.refund2(form.date_invoice, date, description,inv.journal_id.id,type_document_id.id,nro_comprobante)
                refund.check_currency_rate = True
                refund.currency_rate_auto = inv.currency_rate_auto

                created_inv.append(refund.id)
                if mode in ('cancel', 'modify'):
                    movelines = inv.move_id.line_ids
                    to_reconcile_ids = {}
                    to_reconcile_lines = self.env['account.move.line']
                    for line in movelines:
                        if line.account_id.id == inv.account_id.id:
                            to_reconcile_lines += line
                            to_reconcile_ids.setdefault(line.account_id.id, []).append(line.id)
                        if line.reconciled:
                            line.remove_move_reconcile()
                    refund.action_invoice_open()
                    for tmpline in refund.move_id.line_ids:
                        if tmpline.account_id.id == inv.account_id.id:
                            to_reconcile_lines += tmpline
                            to_reconcile_lines.filtered(lambda l: l.reconciled == False).reconcile()
                    if mode == 'modify':
                        invoice = inv.read(
                            ['name', 'type', 'number',
                             'comment', 'date_due', 'partner_id',
                             'payment_term_id', 'account_id', 'team_id',
                             'currency_id', 'invoice_line_ids', 'tax_line_ids',
                             'journal_id', 'date'])
                        invoice = invoice[0]
                        del invoice['id']
                        invoice_lines = inv_line_obj.browse(invoice['invoice_line_ids'])
                        invoice_lines = inv_obj.with_context(mode='modify')._refund_cleanup_lines(invoice_lines)
                        tax_lines = inv_tax_obj.browse(invoice['tax_line_ids'])
                        tax_lines = inv_obj._refund_cleanup_lines(tax_lines)

                        invoice.update({
                            'type': inv.type,
                            'date_invoice': form.date_invoice,
                            'state': 'draft',
                            'number': False,
                            'invoice_line_ids': invoice_lines,
                            'tax_line_ids': tax_lines,
                            'date': date,
                            'it_type_document': type_document_id.id,
                            'reference': nro_comprobante,
                            'serie_id': self.serie_id.id,
                            'origin': inv.origin,
                            'fiscal_position_id': inv.fiscal_position_id.id,
                        })
                        for field in ('partner_id', 'account_id', 'currency_id',
                                      'payment_term_id', 'journal_id', 'team_id'):
                            invoice[field] = invoice[field] and invoice[field][0]
                        inv_refund = inv_obj.create(invoice)
                        if inv_refund.payment_term_id.id:
                            inv_refund._onchange_payment_term_date_invoice()
                        created_inv.append(inv_refund.id)
                xml_id = (inv.type in ['out_refund', 'out_invoice']) and 'action_invoice_tree1' or \
                         (inv.type in ['in_refund', 'in_invoice']) and 'action_invoice_tree2'
                # Put the reason in the chatter
                subject = _("Invoice refund")
                body = description
                refund.message_post(body=body, subject=subject)
        if xml_id:
            result = self.env.ref('account.%s' % (xml_id)).read()[0]
            invoice_domain = safe_eval(result['domain'])
            invoice_domain.append(('id', 'in', created_inv))
            result['domain'] = invoice_domain
            return result
        return True