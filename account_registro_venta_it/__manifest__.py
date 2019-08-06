# -*- encoding: utf-8 -*-
{
	'name': 'Account Sale Register IT',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['import_base_it','account_registro_compra_it','automatic_fiscal_year_it'],
	'version': '1.0',
	'ITGRUPO_VERSION':2,
	'description':"""
	Registro de Ventas
	""",
	'auto_install': False,
	'demo': [],
    'qweb' : [],
	'data':	['account_sale_register_view.xml','wizard/account_sale_register_report_wizard_view.xml'],
	'installable': True
}
