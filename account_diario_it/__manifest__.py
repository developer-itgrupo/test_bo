# -*- encoding: utf-8 -*-
{
	'name': 'Account Diario IT',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['import_base_it','account_registro_compra_it','automatic_fiscal_year_it'],
	'version': '1.0',
	'description':"""

	GENERAR PARA LIBRO DIARIO
	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_move_line_book_view.xml','wizard/account_move_line_book_wizard_view.xml','wizard/account_move_line_book_report_wizard_view.xml'],
	'installable': True
}
