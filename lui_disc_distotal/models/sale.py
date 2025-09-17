from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"


    type_discount_print = fields.Selection(
        [('Line_before', 'Per Product Percentage with Before Discount '),
        ('Line_after', 'Per Product Percentage with After Discount '),
        ('Line_amount_before', 'Per Product Amount with Before Discount'),
        ('Line_amount_after', 'Per Product Amount with After Discount'),
        ('total', 'Total SO ')],
        string='Type Print Discount ?',
        default='Line_before')

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """Gunakan Σ(gross - subtotal) agar dukung fixed & percent."""
        for order in self:
            amount_untaxed = amount_tax = 0.0
            amount_discount = 0.0
            for line in order.order_line:
                gross = line.product_uom_qty * line.price_unit
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                amount_discount += max(gross - line.price_subtotal, 0.0)
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_discount': amount_discount,
                'amount_total': amount_untaxed + amount_tax,
            })

    discount_type = fields.Selection(
        [('perline','Per Line'), ('percent','Percentage'), ('amount','Amount')],
        string='Discount type', default='perline',
        readonly=True, states={'draft':[('readonly',False)], 'sent':[('readonly',False)]}
    )
    discount_rate = fields.Float('Discount Rate',
                                 digits=dp.get_precision('Account'),
                                 readonly=True,
                                 states={'draft': [('readonly', False)],
                                         'sent': [('readonly', False)]})
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True,
                                     readonly=True, compute='_amount_all',
                                     track_visibility='always')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True,
                                 compute='_amount_all',
                                 track_visibility='always')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True,
                                   compute='_amount_all',
                                   track_visibility='always')
    amount_discount = fields.Monetary(string='Discount', store=True,
                                      readonly=True, compute='_amount_all',
                                      digits=dp.get_precision('Account'),
                                      track_visibility='always')

    @api.onchange('discount_type','discount_rate','order_line')
    def supply_rate(self):
        for order in self:
            lines = order.order_line.filtered(lambda l: l.display_type in (False, 'product'))
            if not lines:
                continue

            if order.discount_type == 'percent':
                for line in lines:
                    line.discount = order.discount_rate or 0.0
                    # Hitung discount_fixed berdasarkan persentase
                    line.discount_fixed = (line.price_unit * line.discount / 100.0) if line.price_unit else 0.0

            elif order.discount_type == 'amount':
                total_base = sum(l.product_uom_qty * l.price_unit for l in lines) or 1.0
                
                # Distribusi proporsional berdasarkan nilai total per baris
                for line in lines:
                    line_total = line.product_uom_qty * line.price_unit
                    line_share = (line_total / total_base) * (order.discount_rate or 0.0)
                    per_unit_fixed = (line_share / line.product_uom_qty) if line.product_uom_qty else 0.0
                    
                    line.discount_fixed = per_unit_fixed
                    # Hitung persentase dari fixed discount
                    line.discount = (per_unit_fixed / line.price_unit * 100.0) if line.price_unit else 0.0

    def _prepare_invoice(self, ):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({
            'discount_type': self.discount_type,
            'discount_rate': self.discount_rate,
            'amount_discount': self.amount_discount,
        })
        return invoice_vals

    def button_dummy(self):

        self.supply_rate()
        return True

    # def write(self, vals):
    #     print(self)
    #     print(self.order_line)
    #     for line in self.order_line:
    #         line.write({
    #             'price_subtotal': line.total_discount
    #         })
    #     return super(SaleOrder, self).write(vals)
    # @api.onchange('discount_type', 'discount_rate')
    # def warning_msg(self):
    #     # settings_discount = self.env['ir.config_parameter'].get_param('group_discount_per_so_line')
    #     local_fields = self.env['sale.order.line'].fields_get()
    #     print(local_fields)
    #     # settings_discount = order.discount
    #     # print(settings_discount)
    #     # if not settings_discount:
    #     #     raise ValidationError(_("You have enable discount from configuration setting"))


class SaleOrderLine(models.Model):
    """Inherit sale order  line and add fields"""
    _inherit = "sale.order.line"

    discount = fields.Float(string='Discount (%)', digits=(16, 2), default=0.0)
    total_discount = fields.Float(string="Total Discount", default=0.0,
                                  store=True)
