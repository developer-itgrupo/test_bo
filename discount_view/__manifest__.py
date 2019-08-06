
{
    'name': 'Discount onlyread',
    'version': '10',
    'license': 'AGPL-3',
    'author': 'ITGRUPO-COMPATIBLE-BO',
    'category': 'Customize',
    'summary': 'Cambios personalizados',
    'depends': ['sale'],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'inherit_view.xml',
    ],
    'installable': True,
}
