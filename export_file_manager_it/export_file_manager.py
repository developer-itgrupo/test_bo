import os
from odoo import api, fields, models

class ExportFileManager(models.TransientModel):
	_name = 'export.file.manager'
	
	file_name = fields.Char(string='Name',required=True)
	file = fields.Binary(string='file',required=True)
	
	@api.multi
	def export_file(self,**args):
		clear = args.get('clear',False) # Para limpiar el fichero creado
		path  = args.get('path',False) # ruta completa del fichero
		if clear and path:
			if os.path.exists(path):
				os.remove(path)
			else:
				print('Path file does not exist !')	
		return {'uid' : self.id,'type': 'ir.actions.act_url','url' : '/web/content/%s/%s/file/%s?download=true' %(self._name,self.id,self.file_name),}

