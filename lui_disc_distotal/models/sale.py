from odoo import api, fields, models, _
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
        """Compute amount dengan mempertimbangkan markup dan discount yang tepat."""
        for order in self:
            amount_untaxed = amount_tax = 0.0
            amount_discount = 0.0
            for line in order.order_line:
                # Skip non-product lines
                if line.display_type:
                    continue
                    
                # Hitung gross berdasarkan price_unit (yang sudah ter-markup) dan quantity
                gross = line.product_uom_qty * line.price_unit
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                
                # Calculate actual discount amount
                if line.discount_fixed:
                    # Fixed discount per unit * quantity
                    line_discount = line.discount_fixed * line.product_uom_qty
                elif line.discount:
                    # Percentage discount dari gross amount
                    line_discount = gross * (line.discount / 100.0)
                else:
                    line_discount = 0.0
                    
                amount_discount += line_discount
                
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
                                 digits='Account',
                                 readonly=True,
                                 states={'draft': [('readonly', False)],
                                         'sent': [('readonly', False)]})
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True,
                                     readonly=True, compute='_amount_all',
                                     tracking=True)
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True,
                                 compute='_amount_all',
                                 tracking=True)
    amount_total = fields.Monetary(string='Total', store=True, readonly=True,
                                   compute='_amount_all',
                                   tracking=True)
    amount_discount = fields.Monetary(string='Discount', store=True,
                                      readonly=True, compute='_amount_all',
                                      digits='Account',
                                      tracking=True)

    @api.onchange('discount_type','discount_rate','order_line')
    def supply_rate(self):
        """Apply discount berdasarkan type dengan mempertimbangkan price_unit yang sudah ter-markup"""
        for order in self:
            lines = order.order_line.filtered(lambda l: l.display_type in (False, 'product'))
            if not lines:
                continue

            # Set context untuk mencegah infinite loop
            with self.env.protecting(['discount', 'discount_fixed'], lines):
                if order.discount_type == 'percent':
                    for line in lines:
                        # Set discount percentage
                        line.with_context(ignore_discount_onchange=True).discount = order.discount_rate or 0.0
                        # Calculate discount_fixed based on current price_unit (already includes markup)
                        line.with_context(ignore_discount_onchange=True).discount_fixed = (line.price_unit * line.discount / 100.0) if line.price_unit else 0.0

                elif order.discount_type == 'amount':
                    # Calculate total base using price_unit (already includes markup) * quantity
                    total_base = sum(l.product_uom_qty * l.price_unit for l in lines)
                    
                    if total_base:
                        # Distribute discount proportionally
                        for line in lines:
                            line_total = line.product_uom_qty * line.price_unit
                            line_share = (line_total / total_base) * (order.discount_rate or 0.0)
                            per_unit_fixed = (line_share / line.product_uom_qty) if line.product_uom_qty else 0.0
                            
                            # Set fixed discount per unit
                            line.with_context(ignore_discount_onchange=True).discount_fixed = per_unit_fixed
                            # Calculate percentage from fixed discount
                            line.with_context(ignore_discount_onchange=True).discount = (per_unit_fixed / line.price_unit * 100.0) if line.price_unit else 0.0
                
                elif order.discount_type == 'perline':
                    # Keep individual line discounts as they are
                    pass

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


class SaleOrderLine(models.Model):
    """Inherit sale order line and add fields"""
    _inherit = "sale.order.line"

    discount = fields.Float(string='Discount (%)', digits=(16, 2), default=0.0)
    total_discount = fields.Float(string="Total Discount", default=0.0, store=True, compute='_compute_total_discount')
    
    @api.depends('discount', 'discount_fixed', 'product_uom_qty', 'price_unit')
    def _compute_total_discount(self):
        """Calculate total discount amount for the line"""
        for line in self:
            if line.display_type:
                line.total_discount = 0.0
                continue
                
            if line.discount_fixed:
                # Fixed discount per unit * quantity
                line.total_discount = line.discount_fixed * line.product_uom_qty
            elif line.discount:
                # Percentage discount dari gross amount
                gross = line.product_uom_qty * line.price_unit
                line.total_discount = gross * (line.discount / 100.0)
            else:
                line.total_discount = 0.0