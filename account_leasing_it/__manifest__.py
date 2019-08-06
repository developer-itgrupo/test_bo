# -*- encoding: utf-8 -*-
{
	'name': 'Account Leasing IT',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['account','activo_fijo','account_parametros_it','account_invoice_it'],
	'version': '1.0',
	'description':"""
	Account Leasing IT
	""",
	'auto_install': False,
	'demo': [],
	'data':	['security/security.xml',
			'security/ir.model.access.csv',
			'account_leasing_view.xml',
			'leasing_wizard_view.xml',
			'leasing_parameters_view.xml',
			'leasing_generation_view.xml'],
	'installable': True
}
