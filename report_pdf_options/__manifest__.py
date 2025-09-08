# -*- coding: utf-8 -*-
{
    'name': 'report options',
    'author': 'Luis Rodrigo Port dan Revise By Rizky',
    'depends': ['web'],
    'data': [
        'views/ir_actions_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'report_pdf_options/static/src/**/*.xml',
            'report_pdf_options/static/src/js/PdfOptionsModal.js',
            'report_pdf_options/static/src/js/qwebactionmanager.js',
        ]
    }
}
