# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

class AccountPrestamo(models.Model):
    _name = 'account.prestamo'
    _rec_name = 'nro_prestamo'

    nro_prestamo = fields.Char('Nro. Prestamo')
    fecha = fields.Date('Fecha',default=datetime.now())
    fecha_calculo = fields.Date('Fecha Calculo',default=datetime.now())
    partner_id = fields.Many2one('res.partner','Entidad')
    currency_id = fields.Many2one('res.currency','Moneda')
    monto = fields.Float('Monto')
    intereses = fields.Float('Intereses')

    @api.one
    @api.depends('monto','intereses')
    def calcular_deuda(self):
        self.total_deuda = self.monto + self.intereses

    @api.one
    @api.depends('total_deuda','prestamo_line','fecha_calculo')
    def calcular_saldo(self):
        self.saldo = self.total_deuda
        hoy = datetime.strptime(self.fecha_calculo,"%Y-%m-%d")
        resta = 0
        for i in self.prestamo_line:
            if datetime.strptime(i.fecha_vencimiento,"%Y-%m-%d") <= hoy:
                resta += i.monto_cuota
        self.saldo = self.saldo - resta

    total_deuda = fields.Float('Total Deuda',compute='calcular_deuda')
    saldo = fields.Float('Saldo',compute='calcular_saldo')
    state = fields.Selection([('draft','Borrador'),('validated','Validado')],default='draft')
    tc = fields.Float('TC',digits=(12,3))
    prestamo_line = fields.One2many('account.prestamo.line','prestamo_id')
    asiento_line = fields.One2many('asiento.line','prestamo_id')

    @api.one
    def validate(self):
        currency = self.env['res.currency'].browse(self.currency_id.id)
        if currency.name == "USD":
            hoy = datetime.strptime(self.fecha,"%Y-%m-%d")
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
        wizard = self.env['cuota.wizard']
        return wizard.get_wizard()

    @api.multi
    def eliminar_lineas(self):
        for i in self.prestamo_line:
            if i.move_1 == False and i.move_2 == False:
                self.env['account.prestamo.line'].browse(i.id).unlink()
            else:
                raise UserError("La cuota Nro. "+str(i.nro_cuota)+" tiene Asientos Contables y Facturas relacionadas para eliminarlo primero debe eliminar dichos registros")
        return {
                    'res_id':self.id,
                    'view_type':'form',
                    'view_mode':'form',
                    'res_model':'account.leasing',
                    'views':[[self.env.ref('account_prestamo_it.account_prestamo_form_view').id,'form']],
                    'type':'ir.actions.act_window',
                }

    @api.multi
    def unlink(self):
        if not self.prestamo_line:
            return super(AccountPrestamo,self).unlink()
        else:
            raise UserError("No es posible eliminar un Prestamo con lineas de cuotas, elimine primero todas sus cuotas")

class AccountPrestamoLine(models.Model):
    _name = 'account.prestamo.line'

    prestamo_id = fields.Many2one('account.prestamo')

    nro_cuota = fields.Integer('Nro. Cuota')
    fecha_vencimiento = fields.Date('Fecha Vencimiento')
    saldo_capital = fields.Float('Saldo Capital')
    amortizacion_capital = fields.Float('Amortizacion Capital')
    interes = fields.Float('Interes')
    itf = fields.Float('ITF')
    monto_cuota = fields.Float('Monto Cuota')
    move_1 = fields.Boolean(default=False)
    move_2 = fields.Boolean(default=False)

    @api.multi
    def generar_wizard(self):
        hoy = datetime.strptime(self.fecha_vencimiento,"%Y-%m-%d")
        tc = self.env['res.currency.rate'].search([('name','=',hoy)])
        tc_cuota = 0
        if not tc:
            raise UserError('No existe tipo de cambio para la fecha del prestamo')
        else:
            tc_cuota = 1/tc.rate
        wizard = self.env['account.generation']
        return wizard.get_wizard(self.fecha_vencimiento,tc_cuota,self.prestamo_id.nro_prestamo,self.prestamo_id.id,self.id)

    @api.multi
    def delete_prestamo_line(self):
        prestamo_id = self.prestamo_id.id
        if self.move_1 == False and self.move_2 == False:
            self.env['account.prestamo.line'].browse(self.id).unlink()
            return {
                'res_id':prestamo_id,
                'view_type':'form',
                'view_mode':'form',
                'res_model':'account.prestamo',
                'views':[[self.env.ref('account_prestamo_it.account_prestamo_form_view').id,'form']],
                'type':'ir.actions.act_window'
            }
        else:
            raise UserError("Esta cuota tiene Asientos Contables relacionados para eliminarlo primero debe eliminar dichos asientos")


class AsientoLine(models.Model):
    _name = 'asiento.line'

    prestamo_id = fields.Many2one('account.prestamo')

    libro = fields.Many2one('account.journal','Libro')
    fecha_contable = fields.Date('Fecha Contable')
    asiento = fields.Many2one('account.move','Asiento')
    nro_cuota = fields.Char('Nro. Cuota')

    @api.multi
    def delete_move(self):
        prestamo = self.prestamo_id.id
        self.env['account.move'].browse(self.asiento.id).button_cancel()
        self.env['account.move'].browse(self.asiento.id).unlink()
        return {
            'res_id':prestamo,
            'view_type':'form',
            'view_mode':'form',
            'res_model':'account.prestamo',
            'views':[[self.env.ref('account_prestamo_it.account_prestamo_form_view').id,'form']],
            'type':'ir.actions.act_window',
        }