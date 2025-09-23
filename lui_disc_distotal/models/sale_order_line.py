# Copyright 2017-20 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare, float_round


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    discount_fixed = fields.Float(
        string="Discount (Fixed)",
        digits="Product Price",
        help="Fixed amount discount per unit.",
    )

    price_subtotal_before_discount = fields.Monetary(
        string='Subtotal Before Discount',
        compute='_compute_price_subtotal_before_discount',
        currency_field='currency_id',
        store=True
    )

    markup_percent = fields.Float(
        string="Markup (%)",
        digits=(16, 2),
        default=0.0,
        help="Markup percentage to be applied to unit price"
    )

    original_price_unit = fields.Float(
        string="Original Price Unit",
        digits="Product Price",
        help="Original price unit before markup"
    )

    @api.onchange("markup_percent")
    def _onchange_markup_percent(self):
        """Apply markup percentage to price_unit"""
        if self.env.context.get('skip_markup_onchange'):
            return
            
        # Set original price berdasarkan price_unit saat ini jika belum ada
        if not self.original_price_unit and self.price_unit:
            self.original_price_unit = self.price_unit
            
        # Hitung price_unit baru berdasarkan markup
        if self.original_price_unit:
            if self.markup_percent:
                markup_amount = float_round(
                    self.original_price_unit * (self.markup_percent / 100.0),
                    precision_digits=self.env["decimal.precision"].precision_get("Product Price")
                )
                new_price = self.original_price_unit + markup_amount
            else:
                new_price = self.original_price_unit
            
            # Update price_unit tanpa trigger onchange lain
            self.with_context(skip_price_unit_onchange=True).price_unit = new_price
            
            # Recalculate discount_fixed berdasarkan discount percent yang ada
            if self.discount:
                self.with_context(ignore_discount_onchange=True)._sync_discount_percent_to_fixed()

    @api.onchange("price_unit")
    def _onchange_price_unit(self):
        """Handle price_unit changes"""
        if self.env.context.get('skip_price_unit_onchange'):
            return
            
        # Jika price_unit berubah dan tidak ada markup, set sebagai original
        if self.price_unit and not self.markup_percent and not self.original_price_unit:
            self.original_price_unit = self.price_unit
        
        # Sync discount jika ada perubahan price_unit
        if self.discount and not self.env.context.get('ignore_discount_onchange'):
            self.with_context(ignore_discount_onchange=True)._sync_discount_percent_to_fixed()

    def _sync_discount_percent_to_fixed(self):
        """Sinkronisasi dari discount percent ke discount_fixed"""
        if not self.price_unit:
            self.discount_fixed = 0.0
            return
        self.discount_fixed = float_round(
            (self.discount or 0.0) * self.price_unit / 100.0,
            precision_digits=self.env["decimal.precision"].precision_get("Product Price"),
        )

    def _sync_discount_fixed_to_percent(self):
        """Sinkronisasi dari discount_fixed ke discount percent"""
        if not self.price_unit or not self.discount_fixed:
            self.discount = 0.0
            return
        self.discount = float_round(
            (self.discount_fixed / self.price_unit) * 100,
            precision_digits=self.env["decimal.precision"].precision_get("Discount"),
        )

    @api.model
    def create(self, vals_list):
        """Set original_price_unit on creation and handle markup"""
        if not isinstance(vals_list, list):
            vals_list = [vals_list]
            
        for vals in vals_list:
            # Ambil nilai-nilai yang diperlukan
            price_unit = vals.get('price_unit', 0.0)
            markup_percent = vals.get('markup_percent', 0.0)
            original_price_unit = vals.get('original_price_unit', 0.0)
            
            # Set original_price_unit jika belum ada
            if price_unit and not original_price_unit:
                # Jika ada markup, hitung balik original price
                if markup_percent:
                    vals['original_price_unit'] = price_unit / (1 + markup_percent / 100.0)
                else:
                    vals['original_price_unit'] = price_unit
            
            # Apply markup jika ada original_price_unit
            elif original_price_unit and markup_percent:
                markup_amount = float_round(
                    original_price_unit * (markup_percent / 100.0),
                    precision_digits=self.env["decimal.precision"].precision_get("Product Price")
                )
                vals['price_unit'] = original_price_unit + markup_amount
                
            # Sync discount values
            if vals.get('discount') and vals.get('price_unit'):
                vals['discount_fixed'] = float_round(
                    vals['discount'] * vals['price_unit'] / 100.0,
                    precision_digits=self.env["decimal.precision"].precision_get("Product Price")
                )
            elif vals.get('discount_fixed') and vals.get('price_unit'):
                vals['discount'] = float_round(
                    (vals['discount_fixed'] / vals['price_unit']) * 100,
                    precision_digits=self.env["decimal.precision"].precision_get("Discount")
                )
                    
        return super().create(vals_list)

    def write(self, vals):
        """Handle markup when writing values"""
        # Hindari recursive calls
        if self.env.context.get('skip_write_markup'):
            return super().write(vals)
        
        # Process each record
        for line in self:
            new_vals = vals.copy()
            
            # Handle price_unit changes
            if 'price_unit' in new_vals and 'markup_percent' not in new_vals and 'original_price_unit' not in new_vals:
                # Jika price_unit diubah langsung tanpa markup, update original_price_unit
                if not line.markup_percent:
                    new_vals['original_price_unit'] = new_vals['price_unit']
            
            # Handle markup_percent changes
            elif 'markup_percent' in new_vals:
                # Gunakan original_price_unit yang ada atau yang baru
                original_price = new_vals.get('original_price_unit', line.original_price_unit)
                
                # Jika belum ada original_price_unit, gunakan current price_unit
                if not original_price and line.price_unit:
                    if line.markup_percent:
                        # Hitung balik dari price_unit saat ini
                        original_price = line.price_unit / (1 + line.markup_percent / 100.0)
                    else:
                        original_price = line.price_unit
                    new_vals['original_price_unit'] = original_price
                
                # Calculate new price_unit with markup
                if original_price:
                    markup_percent = new_vals.get('markup_percent', 0.0)
                    if markup_percent:
                        markup_amount = float_round(
                            original_price * (markup_percent / 100.0),
                            precision_digits=self.env["decimal.precision"].precision_get("Product Price")
                        )
                        new_vals['price_unit'] = original_price + markup_amount
                    else:
                        new_vals['price_unit'] = original_price
            
            # Handle discount synchronization
            if 'discount' in new_vals and 'discount_fixed' not in new_vals:
                price_unit_to_use = new_vals.get('price_unit', line.price_unit)
                if price_unit_to_use:
                    new_vals['discount_fixed'] = float_round(
                        new_vals['discount'] * price_unit_to_use / 100.0,
                        precision_digits=self.env["decimal.precision"].precision_get("Product Price")
                    )
            elif 'discount_fixed' in new_vals and 'discount' not in new_vals:
                price_unit_to_use = new_vals.get('price_unit', line.price_unit)
                if price_unit_to_use and new_vals['discount_fixed']:
                    new_vals['discount'] = float_round(
                        (new_vals['discount_fixed'] / price_unit_to_use) * 100,
                        precision_digits=self.env["decimal.precision"].precision_get("Discount")
                    )
            
            # Update record with skip context to avoid recursion
            super(SaleOrderLine, line.with_context(skip_write_markup=True)).write(new_vals)
        
        return True

    @api.depends('price_unit', 'product_uom_qty')
    def _compute_price_subtotal_before_discount(self):
        """Hitung subtotal sebelum discount dengan mempertimbangkan quantity"""
        for line in self:
            line.price_subtotal_before_discount = line.price_unit * line.product_uom_qty

    @api.onchange("discount")
    def _onchange_discount_percent(self):
        """Sinkron dari percent -> fixed (per unit)"""
        if self.env.context.get("ignore_discount_onchange"):
            return
        self.with_context(ignore_discount_onchange=True)._sync_discount_percent_to_fixed()

    @api.onchange("discount_fixed")
    def _onchange_discount_fixed(self):
        """Sinkron dari fixed -> percent"""
        if self.env.context.get("ignore_discount_onchange"):
            return
        self.with_context(ignore_discount_onchange=True)._sync_discount_fixed_to_percent()

    def _convert_to_tax_base_line_dict(self):
        """Prior to calculating the tax totals for a line, update the discount value
        used in the tax calculation to the full float value. Otherwise, we get rounding
        errors in the resulting calculated totals.
        """
        self.ensure_one()

        # Accurately pass along the fixed discount amount to the tax computation method.
        if self.discount_fixed:
            return self.env["account.tax"]._convert_to_tax_base_line_dict(
                self,
                partner=self.order_id.partner_id,
                currency=self.order_id.currency_id,
                product=self.product_id,
                taxes=self.tax_id,
                price_unit=self.price_unit,
                quantity=self.product_uom_qty,
                discount=self._get_discount_from_fixed_discount(),
                price_subtotal=self.price_subtotal,
            )

        return super()._convert_to_tax_base_line_dict()

    def _get_discount_from_fixed_discount(self):
        """Calculate the discount percentage from the fixed discount amount using current price_unit."""
        self.ensure_one()
        if not self.discount_fixed or not self.price_unit:
            return 0.0

        return float_round(
            (self.discount_fixed / self.price_unit) * 100,
            precision_digits=self.env["decimal.precision"].precision_get("Discount"),
        )

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res.update({
            "discount_fixed": self.discount_fixed,
            # "markup_percent": self.markup_percent,
            # "original_price_unit": self.original_price_unit
        })
        return res

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line dengan mempertimbangkan markup dan discount yang benar.
        """
        for line in self:
            # Calculate price after markup (sudah ada di price_unit)
            price = line.price_unit
            
            # Apply discount
            if line.discount_fixed:
                # Jika menggunakan fixed discount, kurangi dari price
                price_reduce = price - line.discount_fixed
            else:
                # Jika menggunakan percentage discount
                price_reduce = price * (1 - (line.discount or 0.0) / 100.0)
            
            taxes = line.tax_id.compute_all(
                price_reduce,
                line.order_id.currency_id,
                line.product_uom_qty,
                product=line.product_id,
                partner=line.order_id.partner_shipping_id
            )
            
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })