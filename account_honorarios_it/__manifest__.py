# -*- encoding: utf-8 -*-
{
	'name': 'Account Honorarios IT',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['import_base_it', 'account_registro_compra_it','automatic_fiscal_year_it'],
	'version': '1.0',
	'description':"""
		Libros de Honorarios
	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_forth_category_view.xml','wizard/account_forth_category_wizard_view.xml','wizard/prestadores_report_view.xml', 'wizard/fees_report_view.xml'],
	'installable': True
}
