from odoo import models

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    def _get_product_purchase_description(self, product_lang):
        """ Override untuk hanya menampilkan nama produk di purchase order line """
        self.ensure_one()
        if not self.product_id:
            return ""
        return self.product_id.name