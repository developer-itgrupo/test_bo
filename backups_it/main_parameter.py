# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp import http
from openerp.http import request
import os
import datetime
from openerp.osv import osv
from zipfile import ZipFile
import zipfile
import zlib
import shutil
# import tools

class utilitario_parameter(models.Model):
	_name = 'utilitario.parameter'

	@api.model_cr 
	def init(self):
		self.env.cr.execute('select id from res_users')
		uid = self.env.cr.dictfetchall()
		self.env.cr.execute('select id from utilitario_parameter')
		ids = self.env.cr.fetchall()
		
		print 'ids', ids
		
		if len(ids) == 0:
			self.env.cr.execute("""INSERT INTO utilitario_parameter (create_uid, name) VALUES (""" + str(uid[0]['id']) + """, 'Parametros Generales');""")
	
	name = fields.Char('Nombre',size=50, default='Parametros Generales')

	directorio = fields.Char('Directorio')
	directorio_pg = fields.Char('Comando PostgreSQL pg_dump')
	directorio_dropb = fields.Char('Directorio Compartido')
	database_name = fields.Char('Base de datos')
	database_user = fields.Char('Usuario')
	database_password = fields.Char('Contraseña')
	ip_serverpg = fields.Char('IP Server PostgreSQL')
	port_serverpg = fields.Char('Puerto Server PostgreSQL')
	

	@api.onchange('directorio')
	def onchange_dir_create_file(self):
		if self.directorio:
			if self.directorio[-1] == '/':
				pass
			else:
				self.directorio = self.directorio + '/'
	

class backup_utilitario(models.Model):
	_name = 'backup.utilitario'

	
	def generar_backup(self):
		param =self.env['utilitario.parameter'].search([])[0]
		hora = str(datetime.datetime.now())[10:]
		horalimpia = hora.replace(' ','')
		horalimpia = horalimpia.replace(':','')

		filename = param.database_name+"_" + str(datetime.datetime.now())[:10]+horalimpia+ ".backup"
		filename_zip = param.database_name+"_" + str(datetime.datetime.now())[:10] + ".zip"
		codea = param.directorio_pg+" --dbname=postgresql://"+param.database_user+":"+param.database_password+"@"+param.ip_serverpg+":"+param.port_serverpg+"/"+param.database_name+" --format tar --blobs --encoding UTF8 --verbose > "  + param.directorio  + filename 
		print codea
		os.system(param.directorio_pg+" --dbname=postgresql://"+param.database_user+":"+param.database_password+"@"+param.ip_serverpg+":"+param.port_serverpg+"/"+param.database_name+" --format tar --blobs --encoding UTF8 --verbose > "  + param.directorio  + filename )
		zipfl = ZipFile( param.directorio  + filename_zip ,mode='w',allowZip64 = True)
		zipfl.write(param.directorio+filename,compress_type=zipfile.ZIP_DEFLATED)
		zipfl.close()
		shutil.copyfile(param.directorio+filename_zip,param.directorio_dropb+filename_zip)
		