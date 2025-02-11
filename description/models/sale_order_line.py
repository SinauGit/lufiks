from odoo import models

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    def _get_sale_order_line_multiline_description_sale(self):
        """ Override untuk hanya menampilkan nama produk """
        self.ensure_one()
        if not self.product_id:
            return ""
        return self.product_id.name 