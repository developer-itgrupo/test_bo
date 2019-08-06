# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
import base64

class CuotaWizard(models.Model):
	_name = 'cuota.wizard'

	file_fees = fields.Binary('Archivo Importacion',required=True)
	file_name = fields.Char()
	separator = fields.Char("Separador",default="|",size=1)

	@api.multi
	def get_wizard(self):
		return {
            'name':_('Importacion Cuotas'),
            'res_id':self.id,
            'view_type':'form',
            'view_mode':'form',
            'res_model':'cuota.wizard',
            'views':[[self.env.ref('account_prestamo_it.cuota_wizard_view').id,'form']],
            'type':'ir.actions.act_window',
            'target':'new'
        }

	@api.multi
	def csv_import(self):
		data = base64.b64decode(self.file_fees)
		data = data.strip().split("\n")
		for c,line in enumerate(data,1):
			line = line.split(self.separator)
			if len(line) != 7:
				raise UserError('El archivo solo debe tener 7 columnas por linea, la linea '+str(c)+' no cumple este requisito')
		for c,line in enumerate(data,1):
			line = line.split(self.separator)
			try:
				fecha = datetime.strptime(line[1],"%Y-%m-%d")
			except:
				raise UserError("El formato de fecha debe ser el siguiente 'yyyy-mm-dd' en la linea "+str(c))
			vals = {
					'nro_cuota':int(line[0]),
					'fecha_vencimiento':fecha,
					'saldo_capital':float(line[2]),
					'amortizacion_capital':float(line[3]),
					'interes':float(line[4]),
					'itf':float(line[5]),
					'monto_cuota':float(line[6]),
					'prestamo_id':self._context['active_id']
				}
			try:
				self.env['account.prestamo.line'].create(vals)
			except:
				raise UserError("Hay un error en la linea "+str(c))
			#self.env['account.prestamo'].browse(self._context['active_id']).prestamo_line.refresh()
		return {}