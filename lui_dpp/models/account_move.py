from odoo import api, fields, models, exceptions, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    tax_base_amount = fields.Monetary(
        string='Tax Base Amount ',
        compute='_compute_tax_base_amount',
        store=True,
        currency_field='currency_id',
    )

    @api.depends('amount_untaxed')
    def _compute_tax_base_amount(self):
        for move in self:
            move.tax_base_amount = move.amount_untaxed * (11/12) if move.amount_untaxed else 0.0
