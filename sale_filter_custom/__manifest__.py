# -*- coding: utf-8 -*-
{
    'name': 'Sale Filter Custom - This Year',
    'version': '16.0.1.0.3',
    'category': 'Sales',
    'summary': 'Custom filters for Sales Orders and Quotations with This Year filter',
    'description': """
Custom Sales Filter - This Year
================================

This module adds custom filters for Sales Orders and Quotations with year-based filtering.

Features:
---------

Sales Order Filters:
* My All SO (renamed from My Orders)
* My SO This Year
* All SO This Year
* To Invoice
* To Upsell
* Order Date

Quotation Filters:
* My Quotation This Year
* All Quotation This Year
* My All Quotations (renamed from My Quotations)

All filters automatically filter data by current year.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['sale', 'sale_management'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
