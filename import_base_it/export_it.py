# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _

class export_file_save(osv.TransientModel):
	_name = 'export.file.save'	
	
	output_name = fields.Char('Output filename', size=128)
	output_file = fields.Binary('Output file', readonly=True, filename="output_name")
	link = fields.Char('Link Descarga')

	@api.model
	def create(self,vals):
		val_tmp = base64.decodestring(vals['output_file'])		
		vals['output_file'] = False
		t = super(export_file_save,self).create(vals)
		param = self.env['main.parameter'].search([])[0]
		direc_completa = self.env.cr.dbname + '-' + vals['output_name'].split('.')[0] + '_' + str(t.id) +'.'+  vals['output_name'].split('.')[1]
		if 'respetar' in vals:
			direc_completa =  vals['output_name']
		f_o = open(param.download_directory+ direc_completa , 'wb')
		f_o.write(val_tmp)
		f_o.close()
		t.link = param.download_url + direc_completa
		return t