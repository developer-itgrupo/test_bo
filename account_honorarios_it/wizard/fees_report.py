# -*- encoding: utf-8 -*-
import base64
import codecs
import pprint

from openerp.osv import osv
from openerp import models, fields, api
from datetime import datetime, date, time, timedelta

class fees_report(osv.TransientModel):
	_name = "fees.report"

	@api.multi
	def get_fees(self):
		import sys
		sys.setdefaultencoding('iso-8859-1')
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		
		filtro = [('id', 'in', self.env.context.get(('active_ids'), []))]
		#raise osv.except_osv('Alerta',filtro)
		inside = []

		recibos = self.env['account.forth.category'].search(filtro)
		
		parser = {
			'02' : 'R',
			'07' : 'N',
			'D' : 'D',
			'00' : 'O',
		}
		
		ctxt=""
		periodo = None
		n=0
		separator = '|'
		in_ids = []
		for recibo in recibos:
			if periodo != recibo.periodo and periodo is not None:
				raise osv.except_osv('Alerta','Hay periodos distintos en la consulta')
			periodo = recibo.periodo
			has_ret = '1' if recibo.retencion != 0 else '0'
			com_type = parser[recibo.tipodocumento]
			n = n+1

			ctxt += recibo.tipodoc + separator
			ctxt += recibo.numdoc + separator
			ctxt += com_type + separator
			ctxt += recibo.serie + separator
			ctxt += recibo.numero + separator
			ctxt += str(recibo.monto) + separator
			ctxt += datetime.strptime(recibo.fechaemision, '%Y-%m-%d').strftime('%d/%m/%Y') + separator
			ctxt += ((datetime.strptime(recibo.fechapago, '%Y-%m-%d').strftime('%d/%m/%Y') ) if recibo.fechapago else '') + separator
			ctxt += has_ret + separator
			ctxt += separator
			ctxt += separator
			ctxt=ctxt+"""\r\n"""

		code = '0601'
		periodo = periodo.split('/')
		name = periodo[1]+periodo[0]
		user = self.env['res.users'].browse(self.env.uid)
		print 'name', name
		print 'user', user
		if user.company_id.id == False:
			raise osv.except_osv('Alerta','El usuario actual no tiene una compañia asignada. Contacte a su administrador.')
		if user.company_id.partner_id.id == False:
			raise osv.except_osv('Alerta','La compañia del usuario no tiene una empresa asignada. Contacte a su administrador.')
		if user.company_id.partner_id.nro_documento == False:
			raise osv.except_osv('Alerta','La compañia del usuario no tiene un numero de documento. Contacte a su administrador.')
			
		ruc = user.company_id.partner_id.nro_documento
		
		print 'ruc', ruc
		file_name = code + name + ruc + '.4ta'
		
		vals = {
			'output_name': file_name,
			'output_file': base64.encodestring(ctxt),	
			'respetar':1,		
		}

		sfs_id = self.env['export.file.save'].create(vals)
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}
	