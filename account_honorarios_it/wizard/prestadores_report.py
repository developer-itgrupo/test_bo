# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

class prestadores_report(osv.osv_memory):
	_name = "prestadores.report"

	@api.multi
	def get_prestadores(self):
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		
		filtro = [('id', 'in', self.env.context.get(('active_ids'), []))]
		#raise osv.except_osv('Alerta',filtro)
		inside = []

		recibos = self.env['account.forth.category'].search(filtro)
		
		ctxt=""
		periodo = None
		n=0
		separator = '|'
		in_ids = []
		for recibo in recibos:
			if periodo != recibo.periodo and periodo is not None:
				raise osv.except_osv('Alerta','Hay periodos distintos en la consulta')
			periodo = recibo.periodo
			partner = self.env['res.partner'].search([('name','=',recibo.partner)])
			is_resident = '2' if partner.is_resident else '1' 
			has_agree = '1' if partner.has_agree else '0' 
			n = n+1
			if not partner.id in in_ids:
				in_ids.append(partner.id)
				first_name = partner.nombre if partner.nombre != False else ''
				last_name_f = partner.apellido_p if partner.apellido_p != False else ''
				last_name_m = partner.apellido_m if partner.apellido_m != False else ''
				ctxt += recibo.tipodoc + separator
				ctxt += recibo.numdoc + separator
				ctxt += last_name_f + separator
				ctxt += last_name_m + separator
				ctxt += first_name + separator
				ctxt += is_resident + separator
				ctxt += has_agree + separator
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
		file_name = code + name + ruc + '.ps4'
		
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

