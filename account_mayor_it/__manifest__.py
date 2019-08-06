# -*- encoding: utf-8 -*-
{
	'name': 'Account Analytic Book Major IT',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['import_base_it','account_registro_compra_it','automatic_fiscal_year_it'],
	'version': '1.0',
	'description':"""
	Crea el Libro Mayor para contabilidad

	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/account_analytic_book_major_wizard_view.xml','account_analytic_book_major_view.xml'],
	'installable': True
}
