# -*- coding: utf-8 -*-
from openerp.http import Controller
from openerp.http import request, route
import decimal
import openerp.http as http
from openerp import models, fields, api
import base64
from openerp.osv import osv
import decimal
import sys, traceback
from openerp.tools.translate import _
from lxml.builder import E
from collections import defaultdict
from lxml import etree
from itertools import chain, repeat

def name_boolean_group(id):
	return 'in_group_' + str(id)

def name_selection_groups(ids):
	return 'sel_groups_' + '_'.join(map(str, ids))

def is_boolean_group(name):
	return name.startswith('in_group_')

def is_selection_groups(name):
	return name.startswith('sel_groups_')

def is_reified_group(name):
	return is_boolean_group(name) or is_selection_groups(name)

def get_boolean_group(name):
	return int(name[9:])

def get_selection_groups(name):
	return map(int, name[11:].split('_'))

def partition(f, xs):
	"return a pair equivalent to (filter(f, xs), filter(lambda x: not f(x), xs))"
	yes, nos = [], []
	for x in xs:
		(yes if f(x) else nos).append(x)
	return yes, nos
class res_groups(models.Model):
	_inherit ='res.groups'

	para_configurar_menus = fields.Boolean('Para Configurar Menus')
	configurado = fields.Boolean('Personalización',help=u"Respeta configuración de Menus")


	@api.model
	def get_groups_by_application32(self):
		""" Return all groups classified by application (module category), as a list::

				[(app, kind, groups), ...],

			where ``app`` and ``groups`` are recordsets, and ``kind`` is either
			``'boolean'`` or ``'selection'``. Applications are given in sequence
			order.  If ``kind`` is ``'selection'``, ``groups`` are given in
			reverse implication order.
		"""
		def linearize(app, gs):
			# determine sequence order: a group appears after its implied groups
			order = {g: len(g.trans_implied_ids & gs) for g in gs}
			# check whether order is total, i.e., sequence orders are distinct
			if len(set(order.itervalues())) == len(gs):
				return (app, 'selection', gs.sorted(key=order.get))
			else:
				return (app, 'boolean', gs)

		# classify all groups by application
		by_app, others = defaultdict(self.browse), self.browse()
		for g in self.get_application_groups([]):
			if g.category_id:
				if g.para_configurar_menus:					
					by_app[g.category_id] += g
			else:
				others += g
		# build the result
		res = []
		for app, gs in sorted(by_app.iteritems(), key=lambda (a, _): a.sequence or 0):
			res.append(linearize(app, gs))
		if others:
			res.append((self.env['ir.module.category'], 'boolean', others))


		return res

	

	@api.model
	def _update_user_groups_view(self):
		""" Modify the view with xmlid ``base.user_groups_view``, which inherits
			the user form view, and introduces the reified group fields.
		"""
		if self._context.get('install_mode'):
			# use installation/admin language for translatable names in the view
			user_context = self.env['res.users'].context_get()
			self = self.with_context(**user_context)

		# We have to try-catch this, because at first init the view does not
		# exist but we are already creating some basic groups.
		view = self.env.ref('base.user_groups_view', raise_if_not_found=False)
		if view and view.exists() and view._name == 'ir.ui.view':
			group_no_one = view.env.ref('base.group_no_one')
			xml1, xml2 = [], []
			xml1.append(E.separator(string=_('Application'), colspan="2"))
			for app, kind, gs in self.get_groups_by_application():
				# hide groups in categories 'Hidden' and 'Extra' (except for group_no_one)
				attrs = {}
				if app.xml_id in ('base.module_category_hidden', 'base.module_category_extra', 'base.module_category_usability'):
					attrs['groups'] = 'base.group_no_one'

				if kind == 'selection':
					# application name with a selection field
					field_name = name_selection_groups(gs.ids)
					xml1.append(E.field(name=field_name, **attrs))
					xml1.append(E.newline())
				else:
					# application separator with boolean fields
					app_name = app.name or _('Other')
					xml2.append(E.separator(string=app_name, colspan="4", **attrs))
					for g in gs:
						field_name = name_boolean_group(g.id)
						if g == group_no_one:
							# make the group_no_one invisible in the form view
							xml2.append(E.field(name=field_name, invisible="1", **attrs))
						else:
							xml2.append(E.field(name=field_name, **attrs))

			xml2.append({'class': "o_label_nowrap"})
			xml = E.field(E.group(*(xml1), col="2"), E.group(*(xml2), col="4"), name="groups_id", position="replace")
			xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY GROUPS"))
			xml_content = etree.tostring(xml, pretty_print=True, xml_declaration=True, encoding="utf-8")
			view.with_context(lang=None).write({'arch': xml_content})


		view = self.env.ref('database_consulting_jp_it.user_groups_view_itf', raise_if_not_found=False)

		if view and view.exists() and view._name == 'ir.ui.view':
			group_no_one = view.env.ref('base.group_no_one')
			xml1, xml2 = [], []
			xml1.append(E.separator(string='Acceso a Menus', colspan="2"))
			for app, kind, gs in self.get_groups_by_application32():
				# hide groups in categories 'Hidden' and 'Extra' (except for group_no_one)
				attrs = {}
				if app.xml_id in ('base.module_category_hidden', 'base.module_category_extra', 'base.module_category_usability'):
					attrs['groups'] = 'base.group_no_one'
				
				if kind == 'selection':
					pass
				else:
					# application separator with boolean fields
					app_name = app.name or _('Other')
					xml2.append(E.separator(string=app_name, colspan="4", **attrs))
					for g in gs:
						field_name = name_boolean_group(g.id)
						if g == group_no_one:
							# make the group_no_one invisible in the form view
							xml2.append(E.field(name=field_name, invisible="1", **attrs))
						else:
							xml2.append(E.field(name=field_name, **attrs))

			xml2.append({'class': "o_label_nowrap"})
			xml = E.field(E.group(*(xml1), col="2"), E.group(*(xml2), col="4"), name="groups_id", position="replace")
			xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY GROUPS"))
			xml_content = etree.tostring(xml, pretty_print=True, xml_declaration=True, encoding="utf-8")
			view.with_context(lang=None).write({'arch': xml_content})
			

class modelsautorgroup(http.Controller):

	@http.route('/autogroup', type='http', website=True)
	def tabla_static_indexm(self, **kw):
		try:	
			t = request.env['ir.ui.menu'].with_context({'lang': 'es_PE'}).search([('parent_id','=',False)])
			for i in t:
				app = request.env['ir.module.category'].search([('name','=',i.name)])
				if len(app)>0:
					app = app[0]
				else:
					app = request.env['ir.module.category'].create({'name':i.with_context({'lang': 'es_PE'}).name})

				newGrupo = request.env['res.groups'].search([('name','=',u'Menu Principal '+i.with_context({'lang': 'es_PE'}).name)])
				if len(newGrupo)>0:
					newGrupo = newGrupo[0]
					#newGrupo.users = [(4,1)]
					#newGrupo.menu_access = [(4,i.id)]
					newGrupo.para_configurar_menus = True
					newGrupo.configurado = True
					request.env.cr.execute(""" update res_groups set para_configurar_menus= true, configurado = true where id =  """+ str(newGrupo.id) + " and name = '"+ u'Menu Principal '+i.with_context({'lang': 'es_PE'}).name + "'"  )
				else:
					newGrupo = request.env['res.groups'].create({'category_id':app.id,'name':u'Menu Principal '+i.with_context({'lang': 'es_PE'}).name})
					newGrupo.users = [(4,1)]
					newGrupo.menu_access = [(4,i.id)]
					newGrupo.para_configurar_menus = True
					newGrupo.configurado = True
					request.env.cr.execute(""" update res_groups set para_configurar_menus= true, configurado = true where id =  """+ str(newGrupo.id) + " and name = '"+ u'Menu Principal '+i.with_context({'lang': 'es_PE'}).name + "'"  )
				for elem in i.child_id:
					newGrupoi = request.env['res.groups'].search([('name','=',u'Menu ' + i.with_context({'lang': 'es_PE'}).name +': ' + elem.with_context({'lang': 'es_PE'}).name)])
					if len(newGrupoi)>0:
						newGrupoi = newGrupoi[0]
						#newGrupoi.users = [(4,1)]
						#newGrupoi.menu_access = [(4,elem.id)]
						newGrupoi.para_configurar_menus = True
						newGrupoi.configurado = True
						request.env.cr.execute(""" update res_groups set para_configurar_menus= true, configurado = true where id =  """+ str(newGrupoi.id) + " and name = '"+ u'Menu ' + i.with_context({'lang': 'es_PE'}).name +': ' + elem.with_context({'lang': 'es_PE'}).name + "'"  )
					else:
						newGrupoi = request.env['res.groups'].create({'category_id':app.id,'name':u'Menu ' + i.with_context({'lang': 'es_PE'}).name +': ' + elem.with_context({'lang': 'es_PE'}).name})
						newGrupoi.users = [(4,1)]
						newGrupoi.menu_access = [(4,elem.id)]
						#newGrupoi.implied_ids = [(4,newGrupo.id)]
						newGrupoi.configurado = True
						newGrupoi.para_configurar_menus = True
						request.env.cr.execute(""" update res_groups set para_configurar_menus= true, configurado = true where id =  """+ str(newGrupoi.id) + " and name = '"+ u'Menu ' + i.with_context({'lang': 'es_PE'}).name +': ' + elem.with_context({'lang': 'es_PE'}).name + "'"  )

			return 'Termino de Configurar Menus'
		except Exception as e:
			http.request._cr.rollback()
			exc_type, exc_value, exc_traceback = sys.exc_info()
			t= traceback.format_exception(exc_type, exc_value,exc_traceback)
			return str(t) 


class modelsremodel1232521525(http.Controller):

	@http.route('/unicavez', type='http', website=True)
	def tabla_static_indexfsm(self, **kw):
		try:
			k = request.env['ir.ui.menu'].search([])
			for m in k:
				for mlk in m.groups_id:
					if mlk.configurado == False:
						m.groups_id = [(3,mlk.id)]

			return 'Termino de Configurar Modelos(Permisos)'
		except Exception as e:
			http.request._cr.rollback()
			exc_type, exc_value, exc_traceback = sys.exc_info()
			t= traceback.format_exception(exc_type, exc_value,exc_traceback)
			return str(t) 



	@http.route('/ocultomodelosInhabilitado', type='http', website=True)
	def tabla_static_indexm(self, **kw):
		try:
			t = request.env['ir.model'].search([])
			for i in t:
				for j in i.access_ids:
					j.unlink()
				request.env['ir.model.access'].create({'name':'Modulo Autocreate','active':True,'model_id':i.id,'perm_read':True,'perm_write':True,'perm_create':True,'perm_unlink':True})

			k = request.env['ir.ui.menu'].search([])
			for m in k:
				for mlk in m.groups_id:
					if mlk.configurado == False:
						m.groups_id = [(3,mlk.id)]

			return 'Termino de Configurar Modelos(Permisos)'
		except Exception as e:
			http.request._cr.rollback()
			exc_type, exc_value, exc_traceback = sys.exc_info()
			t= traceback.format_exception(exc_type, exc_value,exc_traceback)
			return str(t) 

class modelsremodel(http.Controller):

	@http.route('/modelos', type='http', website=True)
	def tabla_static_index(self, **kw):
		try:
			t = request.env['ir.model'].search([])
			for i in t:
				flag = True
				for j in i.access_ids:
					if j.name =='Modulo Autocreate':
						flag = False
				if flag:
					request.env['ir.model.access'].create({'name':'Modulo Autocreate','group_id':False,'active':True,'model_id':i.id,'perm_read':True,'perm_write':True,'perm_create':True,'perm_unlink':True})

			return 'Termino de Configurar Modelos(Permisos)'
		except Exception as e:
			http.request._cr.rollback()
			exc_type, exc_value, exc_traceback = sys.exc_info()
			t= traceback.format_exception(exc_type, exc_value,exc_traceback)
			return str(t) 



class modelsremodel(http.Controller):

	@http.route('/eliminategroup', type='http', website=True)
	def tabla_static_indexm(self, **kw):
		try:
			for i in request.env['res.groups'].search([('para_configurar_menus','=',True)]):
				if len(i.menu_access) == 0:
					i.unlink()

			return 'Termino de Eliminar Menus'
		except Exception as e:
			http.request._cr.rollback()
			exc_type, exc_value, exc_traceback = sys.exc_info()
			t= traceback.format_exception(exc_type, exc_value,exc_traceback)
			return str(t) 