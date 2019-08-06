# -*- encoding: utf-8 -*-
{
	'name': 'Account Caja y Banco IT',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['import_base_it','account_registro_compra_it','automatic_fiscal_year_it'],
	'version': '1.0',
	'description':"""
	Libro de caja y Bancos

	Menu: 
		-Libro Caja y Bancos
	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_move_line_bank_view.xml','wizard/account_move_line_bank_wizard_view.xml'],
	'installable': True
}
