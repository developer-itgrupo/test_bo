# -*- coding: utf-8 -*-
# © 2011-2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    'name': 'Account Analytic Required',
    'version': '10.0.1.1.0',
    'category': 'Analytic Accounting',
    'license': 'AGPL-3',
    'author': "ITGRUPO-COMPATIBLE-BO",
    'website': 'http://www.akretion.com/',
    'depends': ['account', 'account_type_menu','import_base_it','menu_consistencia','automatic_fiscal_year_it'],
    'data': ['views/account.xml'],
    'installable': True,
}
