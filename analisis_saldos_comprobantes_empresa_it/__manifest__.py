# -*- encoding: utf-8 -*-
{
	'name': 'Saldos Comprobantes Analisis x Empresa IT',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['import_base_it','repaccount_contable_period_it','automatic_fiscal_year_it'],
	'version': '1.0',
	'description':"""
Analisis de Saldos por Comprobantes por Empresa
	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/account_contable_period_view.xml','wizard/account_contable_fch_wizard_view.xml'],
	'installable': True
}
