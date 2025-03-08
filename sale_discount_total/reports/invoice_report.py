from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    discount = fields.Float('Discount', readonly=True)

    def _select(self):
        res = super(AccountInvoiceReport,self)._select()
        select_str = res + """, line.discount AS discount """
        return select_str

