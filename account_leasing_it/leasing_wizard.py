# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
import base64

class LeasingWizard(models.Model):
	_name = 'leasing.wizard'

	file_fees = fields.Binary('Archivo Importacion',required=True)
	file_name = fields.Char("Nombre del Archivo")
	separator = fields.Char("Separador",default="|",size=1)

	@api.multi
	def get_wizard(self):
		return {
            'name':_('Importacion Cronograma'),
            'res_id':self.id,
            'view_type':'form',
            'view_mode':'form',
            'res_model':'leasing.wizard',
            'views':[[self.env.ref('account_leasing_it.leasing_wizard_view').id,'form']],
            'type':'ir.actions.act_window',
            'target':'new'
        }

	@api.multi
	def csv_import(self):
		data = base64.b64decode(self.file_fees)
		data = data.strip().split("\n")
		for c,line in enumerate(data,1):
			line = line.split(self.separator)
			if len(line) != 11:
				raise UserError('El archivo solo debe tener 11 columnas por linea, la linea '+str(c)+' no cumple este requisito')
		for c,line in enumerate(data,1):
			line = line.split(self.separator)
			try:
				fecha = datetime.strptime(line[1],"%Y-%m-%d")
			except:
				raise UserError("El formato de fecha debe ser el siguiente 'yyyy-mm-dd' en la linea "+str(c))
			vals = {
					'nro_cuota':int(line[0]),
					'fecha':fecha,
					'saldo':float(line[2]),
					'capital':float(line[3]),
					'gastos':float(line[4]),
					'seguro':float(line[5]),
					'intereses':float(line[6]),
					'subtotal':float(line[7]),
					'comision':float(line[8]),
					'igv':float(line[9]),
					'total':float(line[10]),
					'leasing_id':self._context['active_id']
				}
			try:
				self.env['account.leasing.line'].create(vals)
			except:
				raise UserError('Hay un error en la linea '+str(c))
			#self.env['account.prestamo'].browse(self._context['active_id']).prestamo_line.refresh()
		return {}