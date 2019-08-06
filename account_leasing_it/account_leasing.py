# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

class AccountLeasing(models.Model):
    _name = 'account.leasing'
    _rec_name = 'nro_contrato'

    nro_contrato = fields.Char('Nro. Contrato')
    activo_id = fields.Many2one('account.asset.asset','Activo')
    activo_category_id = fields.Many2one('account.asset.category','Categoria')
    fecha_contrato = fields.Date('Fecha Contrato',default=datetime.now())
    fecha_calculo = fields.Date('Fecha Calculo',default=datetime.now())
    partner_id = fields.Many2one('res.partner','Proveedor')

    @api.one
    @api.depends('leasing_line')
    def calcular_cuotas(self):
        self.nro_cuotas = len(self.leasing_line)

    @api.one
    @api.depends('leasing_line','fecha_calculo')
    def calcular_deuda(self):
        hoy = datetime.strptime(self.fecha_calculo,"%Y-%m-%d")
        resta = 0
        for i in self.leasing_line:
            if datetime.strptime(i.fecha,"%Y-%m-%d") <= hoy:
                resta += i.total
        self.saldo = self.total_arrendamiento - resta

    nro_cuotas = fields.Integer('Nro. Cuotas',compute='calcular_cuotas')
    total_arrendamiento = fields.Float('Monto Total Arrendamiento')
    saldo = fields.Float('Saldo',compute='calcular_deuda')
    currency_id = fields.Many2one('res.currency','Moneda')
    tc = fields.Float('TC',digits=(12,3))
    state = fields.Selection([('draft','Borrador'),('validated','Validado')],default='draft')
    leasing_line = fields.One2many('account.leasing.line','leasing_id')
    factura_line = fields.One2many('factura.line','leasing_id')
    leasing_asiento_line = fields.One2many('leasing.asiento.line','leasing_id')

    @api.onchange('activo_category_id')
    def onchange_activo(self):
        res = {}
        activos_ids = self.env['account.asset.asset'].search([('category_id','=',self.activo_category_id.id)]).ids
        res['domain'] = {'activo_id':[('id','in',activos_ids)]}
        return res

    @api.model
    def create(self,vals):
        activo = self.env['account.leasing'].search([('activo_id','=',vals['activo_id'])])
        if activo:
            raise UserError('No se puede crear dos registros con el mismo activo')
        t = super(AccountLeasing,self).create(vals)
        return t

    @api.one
    def validate(self):
        currency = self.env['res.currency'].browse(self.currency_id.id)
        if currency.name == "USD":
            hoy = datetime.strptime(self.fecha_contrato,"%Y-%m-%d")
            tc = self.env['res.currency.rate'].search([('name','=',hoy)])
            if not tc:
                raise UserError('No existe tipo de cambio para la fecha actual')
            else:
                tc = 1/tc.rate
            self.tc = tc
        self.state = 'validated'

    @api.one
    def cancel(self):
        self.state = 'draft'

    @api.multi
    def importation(self):
        wizard = self.env['leasing.wizard']
        return wizard.get_wizard()

    @api.multi
    def eliminar_lineas(self):
        for i in self.leasing_line:
            if i.invoice_1 == False and i.invoice_2 == False and i.move == False:
                self.env['account.leasing.line'].browse(i.id).unlink()
            else:
                raise UserError("La cuota Nro. "+str(i.nro_cuota)+" tiene Asientos Contables y Facturas relacionadas para eliminarlo primero debe eliminar dichos registros")
        return {
                    'res_id':self.id,
                    'view_type':'form',
                    'view_mode':'form',
                    'res_model':'account.leasing',
                    'views':[[self.env.ref('account_leasing_it.account_leasing_form_view').id,'form']],
                    'type':'ir.actions.act_window',
                }

    @api.multi
    def unlink(self):
        if not self.leasing_line:
            return super(AccountLeasing,self).unlink()
        else:
            raise UserError("No es posible eliminar un Leasing con lineas de cuotas, elimine primero todas sus cuotas")

class AccountLeasingLine(models.Model):
    _name = 'account.leasing.line'

    leasing_id = fields.Many2one('account.leasing')

    nro_cuota = fields.Integer('Nro.')
    fecha = fields.Date('Fecha')
    saldo = fields.Float('Saldo')
    capital = fields.Float('Capital')
    gastos = fields.Float('Gastos')
    seguro = fields.Float('Seguro')
    intereses = fields.Float('Intereses')
    subtotal = fields.Float('Subtotal')
    comision = fields.Float('Comision')
    igv = fields.Float('IGV')
    total = fields.Float('Total')
    mora = fields.Float()
    factura_cuota = fields.Char()
    tc_cuota = fields.Float(digits=(12,3))
    factura_mora = fields.Char()
    tc_mora = fields.Float(digits=(12,3))
    invoice_1 = fields.Boolean(default=False)
    invoice_2 = fields.Boolean(default=False)
    move = fields.Boolean(default=False) 

    @api.multi
    def generar_wizard(self):
        hoy = datetime.strptime(self.fecha,"%Y-%m-%d")
        tc = self.env['res.currency.rate'].search([('name','=',hoy)])
        tc_cuota = 0
        if not tc:
            raise UserError('No existe tipo de cambio para la fecha del prestamo')
        else:
            tc_cuota = 1/tc.rate
        wizard = self.env['leasing.generation']
        return wizard.get_wizard(tc_cuota,self.leasing_id.id,self.id)

    @api.multi
    def delete_leasing_line(self):
        if self.invoice_1 == False and self.invoice_2 == False and self.move == False:
            leasing = self.leasing_id.id
            self.env['account.leasing.line'].browse(self.id).unlink()
            return {
                'res_id':leasing,
                'view_type':'form',
                'view_mode':'form',
                'res_model':'account.leasing',
                'views':[[self.env.ref('account_leasing_it.account_leasing_form_view').id,'form']],
                'type':'ir.actions.act_window',
            }
        else:
            raise UserError("Esta cuota tiene Asientos Contables y Facturas relacionadas para eliminarlo primero debe eliminar dichos registros")

class FacturaLine(models.Model):
    _name = 'factura.line'

    leasing_id = fields.Many2one('account.leasing')

    nro_cuota = fields.Char('Nro. Cuota')
    libro = fields.Many2one('account.journal','Libro')
    factura = fields.Many2one('account.invoice','Factura')
    nro_comprobante = fields.Char('Nro. Comprobante')
    fecha_emision = fields.Date('Fecha Emision')
    fecha_contable = fields.Date('Fecha Contable')

    @api.multi
    def delete_invoice(self):
        leasing = self.leasing_id.id
        self.env['account.invoice'].browse(self.factura.id).unlink()
        return {
            'res_id':leasing,
            'view_type':'form',
            'view_mode':'form',
            'res_model':'account.leasing',
            'views':[[self.env.ref('account_leasing_it.account_leasing_form_view').id,'form']],
            'type':'ir.actions.act_window',
        }

class LeasingAsientoLine(models.Model):
    _name = 'leasing.asiento.line'

    leasing_id = fields.Many2one('account.leasing')

    libro = fields.Many2one('account.journal','Libro')
    fecha_contable = fields.Date('Fecha Contable')
    asiento = fields.Many2one('account.move','Asiento')
    nro_cuota = fields.Char('Nro. Cuota')

    @api.multi
    def delete_move(self):
        leasing = self.leasing_id.id
        self.env['account.move'].browse(self.asiento.id).button_cancel()
        self.env['account.move'].browse(self.asiento.id).unlink()
        return {
            'res_id':leasing,
            'view_type':'form',
            'view_mode':'form',
            'res_model':'account.leasing',
            'views':[[self.env.ref('account_leasing_it.account_leasing_form_view').id,'form']],
            'type':'ir.actions.act_window',
        }