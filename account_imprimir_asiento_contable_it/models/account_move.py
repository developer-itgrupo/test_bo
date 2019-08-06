# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class AccountImpAsientoContable(models.Model):
    _name = "account.imp.asiento.contable"
    _auto = False
    _order = 'fila'
    fila = fields.Integer("fila")
    periodo = fields.Char("periodo")
    diario = fields.Char("diario")
    fecha = fields.Date("fecha")
    voucher = fields.Char("voucher")
    tipo_doc = fields.Char("tipo_doc")
    nro_comprobante = fields.Char("nro_comprobante")
    ruc_dni = fields.Char("ruc_dni")
    partner = fields.Char("partner")
    cuenta = fields.Text("cuenta")
    cuentaa = fields.Text("analitica")
    cargo = fields.Float("cargo", digits=(12, 2))
    abono = fields.Float("abono", digits=(12, 2))
    orden = fields.Integer("orden")
    ide_voucher = fields.Integer("ide_voucher")
    ide_linea = fields.Integer("ide_linea")
    glosa = fields.Char("glosa")


class account_move_pdf(models.Model):
    _inherit = 'account.move'

    @api.multi
    def do_rebuild(self):

        if len(self.ids) > 1:
            raise UserError(
                'Seleccione solo un registro')

        # for account_move_id in self.browse(self.ids):
        query_vista = """  
            DROP VIEW IF EXISTS account_imp_asiento_contable;
            create or replace view account_imp_asiento_contable as (
                select row_number() OVER () AS id,
                *
                 from
                (
            select row_number() over(order by orden,ide_linea asc) as fila,* from (

            select 
            extract(month from a1.fecha_contable)||'-'||extract(year from a1.fecha_contable) as periodo,
            a2.name as diario,a1.date as fecha,
            a1.name as voucher,
            a4.code as tipo_doc,
            a3.nro_comprobante,
            a5.nro_documento as ruc_dni,
            a5.name as partner,
            a6.code || '-' || a6.name as cuenta,
            a3.debit as cargo,
            a3.credit as abono,
            1 as orden,
            a1.id as ide_voucher,
            a3.id as ide_linea,
            aaa.name as cuentaa,
            case when char_length(trim(a9.name))>0 then a9.name else a1.narration end as glosa

            from account_move a1
            left join account_journal a2 on a2.id=a1.journal_id
            left join account_move_line a3 on a3.move_id=a1.id
            left join einvoice_catalog_01 a4 on a4.id=a3.type_document_it
            left join res_partner a5 on a5.id=a3.partner_id
            left join account_account a6 on a6.id=a3.account_id
            left join account_invoice a9 on a9.move_id=a1.id
            left join account_analytic_account aaa on aaa.id = a3.analytic_account_id

            --  ESTO VA A VARIAR EN FUNCION DE EL ID DEL ASIENTO CONTABLE DESDE DONDE SE PIDE IMPRIMIR--
            where a1.id=%d 
            -- /--

            union all

            select 
            extract(month from a1.fecha_contable)||'-'||extract(year from a1.fecha_contable) as periodo,
            a2.name as diario,a1.date as fecha,
            a1.name as voucher,
            a4.code as tipo_doc,
            a3.nro_comprobante,
            a5.nro_documento as ruc_dni,
            a5.name as partner,
            a7.code || '-' || a7.name as cuenta,
            a3.debit as cargo,
            a3.credit as abono,
            2 as orden,
            a1.id as ide_voucher,
            a3.id as ide_linea,
            aaa.name as cuentaa,
            case when char_length(trim(a9.name))>0 then a9.name else a1.narration end as glosa
            

            
            from account_move a1
            left join account_journal a2 on a2.id=a1.journal_id
            left join account_move_line a3 on a3.move_id=a1.id
            left join einvoice_catalog_01 a4 on a4.id=a3.type_document_it
            left join res_partner a5 on a5.id=a3.partner_id
            left join account_account a6 on a6.id=a3.account_id
            left join account_account a7 on a7.id=a6.account_analytic_account_moorage_debit_id
            left join account_account a8 on a8.id=a6.account_analytic_account_moorage_id
            left join account_invoice a9 on a9.move_id=a1.id
            left join account_analytic_account aaa on aaa.id = a3.analytic_account_id

            --  ESTO VA A VARIAR EN FUNCION DE EL ID DEL ASIENTO CONTABLE DESDE DONDE SE PIDE IMPRIMIR--
            where a1.id=%d 
            -- /--

            and left(a7.code,1)='9'

            union all


            select 
            extract(month from a1.fecha_contable)||'-'||extract(year from a1.fecha_contable) as periodo,
            a2.name as diario,a1.date as fecha,
            a1.name as voucher,
            a4.code as tipo_doc,
            a3.nro_comprobante,
            a5.nro_documento as ruc_dni,
            a5.name as partner,
            a8.code || '-' || a8.name as cuenta,
            a3.credit as cargo,
            a3.debit as abono,
            3 as orden,
            a1.id as ide_voucher,
            a3.id as ide_linea,
            aaa.name as cuentaa,
            case when char_length(trim(a9.name))>0 then a9.name else a1.narration end as glosa

            
            from account_move a1
            left join account_journal a2 on a2.id=a1.journal_id
            left join account_move_line a3 on a3.move_id=a1.id
            left join einvoice_catalog_01 a4 on a4.id=a3.type_document_it
            left join res_partner a5 on a5.id=a3.partner_id
            left join account_account a6 on a6.id=a3.account_id
            --left join account_account a7 on a7.id=a6.account_analytic_account_moorage_debit_id
            left join account_account a8 on a8.id=a6.account_analytic_account_moorage_id
            left join account_invoice a9 on a9.move_id=a1.id
            left join account_analytic_account aaa on aaa.id = a3.analytic_account_id
            --  ESTO VA A VARIAR EN FUNCION DE EL ID DEL ASIENTO CONTABLE DESDE DONDE SE PIDE IMPRIMIR--
            where a1.id=%d 
            -- /--
            and (left(a8.code,2)='78' or left(a8.code,2)='79') )tt
            order by orden,ide_linea asc  ) T 
            )""" % (self.ids[0], self.ids[0], self.ids[0])

        self.env.cr.execute(query_vista)
        return self.env['report'].get_action(self.env['account.imp.asiento.contable'].search([]), 'account_imprimir_asiento_contable_it.report_asientocontable')
