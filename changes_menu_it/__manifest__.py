
# -*- coding: utf-8 -*-
# __openerp__.py
{
    'name': "Arreglos BackOffice",
    'category': 'Other',
    'author': 'ITGRUPO-COMPATIBLE-BO',
    'depends': ['account','kardex_it','account_account_it'],
    'version': '1.0',
    'description': """
    - Agregar Kardex Fisico y Valorado (Inventario y Compras)
    - Borrar Menu Valoración del inventario
    - Contabilidad: Campo Codigo (Tipo EF, Diario)
    - Ocultar Periodo Uso Percepcion (Solo Ventas)
    """,
    'data': [        
        'changes_menu_view.xml',
        'account_it_view.xml',
        'account_journal_view.xml',
        'account_invoice_view.xml',
    ],
}
