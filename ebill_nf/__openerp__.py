# -*- encoding: utf-8 -*-
{
	'name'    : 'Facturacion electrónica Nubefact',
	'category': 'account',
	'author'  : 'ITGRUPO-COMPATIBLE-BO',
	'version' : '1.0',

	'description':"""
		Facturacion electrónica Nubefact
	""",
	
	'auto_install': False,
	'demo'        : [],
	'depends'     : [
	'account_invoice_it',
	'odoope_einvoice_base',
	'account_tax_code_it',
	'res_partner_it',
	'account_parametros_it'
	],
	'data'        :	[
					'account_journal_view.xml',
					'account_invoice_view.xml',
					'security/ir.model.access.csv'
					],
	'installable' : True
}


# 'account_invoice_series_it',
# 'account_improve_sunat_it',
# 'account_parameter_it',
# 'currency_sunat_change_it',
# 'account_type_doc_it'
