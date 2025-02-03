from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    tax_base_amount = fields.Monetary(
        string='Tax Base Amount',
        compute='_compute_tax_base_amount',
        store=True,
        currency_field='currency_id',
    )

    @api.depends('amount_untaxed')
    def _compute_tax_base_amount(self):
        for order in self:
            order.tax_base_amount = order.amount_untaxed * (11/12) if order.amount_untaxed else 0.0 