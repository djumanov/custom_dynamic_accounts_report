{
    'name': 'Odoo18 Custom Dynamic Accounting Reports',
    'version': '1.0.0',
    'category': 'Accounting',
    'depends': ['dynamic_accounts_report', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/custom_trial_balance.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_dynamic_accounts_report/static/src/xml/trial_balance.xml',
            'custom_dynamic_accounts_report/static/src/js/trial_balance.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
