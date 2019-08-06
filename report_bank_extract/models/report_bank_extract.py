# -*- encoding: utf-8 -*-

from odoo.osv import osv
import base64
from odoo import models, fields, api, exceptions, _
from datetime import datetime
from datetime import date
import sys
import os
import re
from xlsxwriter.workbook import Workbook
from xlsxwriter.utility import xl_range


class account_bank_statement(models.Model):
    _inherit='account.bank.statement'

    @api.multi
    def generate_excel(self):

        tipeFile= ["extracto_bancario", "cajas_registradoras"]
        title_report_list = ["Extracto Bancario", "Cajas registradoras"]
        size_ref=0
        # nombre de archivo
        if re.match("(.*)CAJA(.*)", self.name):
            name_file = tipeFile[1] + \
                datetime.now().strftime("%Y%m%d%H%M%S") + '.xlsx'
            title_report=title_report_list[1]
            size_ref=40
        else:
            name_file = tipeFile[0] + \
                datetime.now().strftime("%Y%m%d%H%M%S") + '.xlsx'
            title_report=title_report_list[0]
            size_ref=20
        direccion = self.env['main.parameter'].search([])[0].dir_create_file

        # nombre de la direccion
        direccion += name_file
        workbook = Workbook(
            direccion, {'in_memory': True, 'strings_to_numbers': True})

        workbook.formats[0].set_font_size(10)
        workbook.formats[0].set_font_name("Arial")
        worksheet = workbook.add_worksheet(title_report)
        worksheet.set_zoom(80)
        worksheet.set_row(1,60)
        worksheet.set_column(1, 1, 15)  # ancho de B y C
        worksheet.set_column(2, 5, 40)  # ancho de B y C
        worksheet.set_column(3, 4, 50)  # ancho de B y C
        worksheet.set_column(6, 6, 18)
          ########################### Cabecera  ##################################

        merge_format_left_label = workbook.add_format({
            'bold': 1,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
        })
        merge_format_left_text = workbook.add_format({
            'bold': 0,
            'border': 0,
            'align': 'left',
            'valign': 'vcenter',
        })
        merge_format_title = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'underline': 0,
            'valign': 'top',
            'font_size': 14,
            'font_name': 'Arial'})
        merge_format_right = workbook.add_format({
            'align': 'right',
            'valign': 'vcenter',
            'right': 1
        })
        merge_format_center_header = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 12,
            'font_name': 'Arial',
        })
        merge_format_center_text = workbook.add_format({
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 10,
            'font_name': 'Arial',
        })

        merge_format_center_text_wrap = workbook.add_format({
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 10,
            'font_name': 'Arial',
        })
        merge_format_bottom_center = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 12,
            'font_name': 'Arial',
        })
        formatMoneyWithBorder = workbook.add_format(
             {'valign': 'vcenter', 'align': 'right', 'num_format': '"%s" #,##0.00' % self.currency_id.symbol})

        formatMoney = workbook.add_format(
            {'num_format': '#,##0.00', 'border': 1, 'valign': 'vcenter', 'align': 'right'})

        # agregando logo al documento
        #worksheet.insert_image('B2:D2', 'company_logo.jpg', {
        #                      'x_offset': 25, 'y_offset': 5, 'y_scale': 0.95, 'x_scale': 0.85})
        # Borde celdas de imagen
        #worksheet.merge_range('B2:C2', "", merge_format_title)
        # coloca Titulo
        # worksheet.merge_range('D2:N2', title_report, merge_format_title)
        # Inf - Fecha
        merge_format_bottom_center.set_text_wrap()
        worksheet.merge_range('B2:G2', title_report+"\n"+self.name, merge_format_bottom_center)
        
        # Cabezera
        worksheet.write('B4', "Diario:", merge_format_left_label)
        worksheet.write('B5', "Fecha:", merge_format_left_label)
        worksheet.write('F4', "Saldo Inicial:", merge_format_left_label)
        worksheet.write('F5', "Balance Final:", merge_format_left_label)

        worksheet.write('C4', self.journal_id[0].name, merge_format_left_text)
        worksheet.write('C5', self.date , merge_format_left_text)
        worksheet.write_number('G4', self.balance_start , formatMoneyWithBorder)
        worksheet.write_number('G5', self.balance_end_real, formatMoneyWithBorder)

        # worksheet.set_column(4, 6, 30)  # ancho de B y C
        x= 7
        y= 1
        i=0

        worksheet.write("B7", "Fecha", merge_format_center_header)
        worksheet.write("C7", "Etiqueta",merge_format_center_header)
        worksheet.write("D7", "Partner", merge_format_center_header)
        worksheet.write("E7", "Referencia", merge_format_center_header)
        worksheet.write("F7", "Medio de Pago", merge_format_center_header)
        worksheet.write("G7", "Cantidad", merge_format_center_header)

        for item in self.line_ids:
            worksheet.set_row(x+i,size_ref)
            if(item['date']):
                worksheet.write( x+i, y, item['date'], merge_format_center_text)
            if(item['name']):
                worksheet.write( x+i, y+1, item['name'], merge_format_center_text)
            if item.partner_id.name:
                worksheet.write( x+i, y+2, item.partner_id.name, merge_format_center_text)
            if  item['ref']:
                worksheet.write( x+i, y+3, item['ref'], merge_format_center_text)
            if item.medio_pago.name:
                merge_format_center_text.set_text_wrap()
                worksheet.write( x+i, y+4, item.medio_pago.name, merge_format_center_text)
            if item['amount']:
                worksheet.write_number( x+i, y+5, item['amount'],formatMoneyWithBorder)
            i=i+1


        workbook.close()
        # os.remove('company_logo.jpg')
        f=open(direccion, 'rb')
        vals={
            'output_name': 'Reporte_' + name_file,
            'output_file': base64.encodestring(''.join(f.readlines())),
            }
        sfs_id=self.env['export.file.save'].create(vals)

        return {
        "type": "ir.actions.act_window",
        "res_model": "export.file.save",
        "views": [[False, "form"]],
        "res_id": sfs_id.id,
        "target": "new",
        }