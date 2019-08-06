# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _


class ir_module_module(models.Model):
	_inherit = 'ir.module.module'

	itgrupo_version_instalada = fields.Integer('IT GRUPO VERSION INSTALADA',default=1)
	itgrupo_version_actual = fields.Integer('IT GRUPO VERSION ACTUAL', compute="get_itgrupo_version_actual")


	@api.depends('name')
	def get_itgrupo_version_actual(self):
		default_version = 1
		for module in self:
			module.itgrupo_version_actual = self.get_module_info(module.name).get('ITGRUPO_VERSION', default_version)


	@api.one
	def button_immediate_uninstall(self):
		self.itgrupo_version_instalada = 1
		t = super(ir_module_module,self).button_immediate_uninstall()
		return t



	@api.one
	def button_immediate_upgrade(self):
		self.itgrupo_version_instalada = self.itgrupo_version_actual
		t = super(ir_module_module,self).button_immediate_upgrade()
		return t


	@api.one
	def button_immediate_install(self):
		self.itgrupo_version_instalada = self.itgrupo_version_actual
		t = super(ir_module_module,self).button_immediate_install()
		return t
