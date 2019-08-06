# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _
from odoo import modules

class ir_module_module(models.Model):
	_inherit = 'ir.module.module'

	itgrupo_fecha_instalada = fields.Char('ITGrupo Fecha Instalada',default='2018-01-01 00:00:00')
	itgrupo_fecha_actual = fields.Char('ITGrupo Fecha Actual', compute="get_fecha_actual")

	direccion = fields.Char('Direccion',compute="get_direccion")

	logger_file = fields.Text('Log',compute="get_logger_file")

	@api.one
	def get_logger_file(self):
		t = ""
		if self.direccion:
			try:
				filer = open(self.direccion + '/static/readme.rdm','rb')
				t = filer.read()
				filer.close()
			except Exception as e:
				pass
		self.logger_file = t

	@api.one
	def get_direccion(self):
		self.direccion = str( modules.get_module_path(self.name) )


	@api.depends('name')
	def get_fecha_actual(self):
		for module in self:

			import os.path, time
			mayor_tam = False
			import os

			rpta = ""
			for base, dirs, files in os.walk(module.direccion):
			  for file in files:
			    if file[-3:] in ('.py','.js') or file[-4:] in ('.xml'):
			      tmp = os.path.getmtime( base + '/' + file )
			      if mayor_tam != False and mayor_tam < tmp:
			        mayor_tam = tmp
			      elif mayor_tam == False:
			        mayor_tam = tmp

			import time

			module.itgrupo_fecha_actual	= time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(mayor_tam))


	@api.one
	def button_immediate_uninstall(self):
		self.itgrupo_fecha_instalada = '2018-01-01 00:00:00'
		t = super(ir_module_module,self).button_immediate_uninstall()
		return t



	@api.one
	def button_immediate_upgrade(self):
		self.itgrupo_fecha_instalada = self.itgrupo_fecha_actual
		t = super(ir_module_module,self).button_immediate_upgrade()
		return t


	@api.one
	def button_immediate_install(self):
		self.itgrupo_fecha_instalada = self.itgrupo_fecha_actual
		t = super(ir_module_module,self).button_immediate_install()
		return t
