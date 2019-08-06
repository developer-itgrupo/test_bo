# -*- encoding: utf-8 -*-
{
	'name': 'Account Prestamo IT',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['account','account_parametros_it'],
	'version': '1.0',
	'description':"""
	Account Prestamo
	""",
	'auto_install': False,
	'demo': [],
	'data':	['security/security.xml',
			'security/ir.model.access.csv',
			'account_prestamo_view.xml',
			'cuota_wizard_view.xml',
			'accounting_parameters_view.xml',
			'account_generation_wizard_view.xml'],
	'installable': True
}
