# -*- encoding: utf-8 -*-
{
	'name': 'Analisis de Cuenta IT',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['import_base_it','automatic_fiscal_year_it'],
	'version': '1.0',
	'description':"""
	Analisis de Cuenta IT

	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/account_contable_period_view.xml','wizard/account_contable_fch_wizard_view.xml'],
	'installable': True
}
