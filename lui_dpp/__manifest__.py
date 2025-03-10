{
    'name': 'LUI DPP',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'LUI DPP',
    'description': """
    """,
    'depends': ['account', 'sale', 'purchase'],
    'data': [
        'views/account_move_view.xml',
        # 'views/sale_order_view.xml',
        'views/purchase_order_view.xml',
        # 'views/inherite_report_so.xml',
        # 'views/inherite_report_so_action.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
} 