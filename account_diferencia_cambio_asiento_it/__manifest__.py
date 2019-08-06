# -*- encoding: utf-8 -*-
{
	'name': 'Diferencia de Cambio Asiento IT',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['import_base_it','res_currency_rate_it'],
	'version': '1.0',
	'description':"""
	Creacion de Asiento de Diferencia de Cambio
	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/account_analytic_book_major_wizard_view.xml','account_analytic_book_major_view.xml'],
	'installable': True
}
