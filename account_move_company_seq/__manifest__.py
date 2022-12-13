# -*- coding: utf-8 -*-
{
    'name': 'Account Move Company Sequence',
    'summary': 'This module will add new field on any account move to get Year Company Sequence',
    'version': '0.1',
    'license': "AGPL-3",
    'author': 'Ahmed Sherby, Ahmed Salama',
    'category': 'Accounting/Accounting',
    'depends': ['account'],
    'data': [
        'data/res_company_data.xml',

        'views/account_move_view_changes.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
