# -*- encoding: utf-8 -*-
{
	'name': 'Saldos Comprobantes Periodo Propietario',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['import_base_it','repaccount_contable_period_it'],
	'version': '1.0',
	'description':"""

	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/report_period.xml',
	'wizard/report_period_wizard.xml',
	'security/ir.model.access.csv',],
	'installable': True
}
