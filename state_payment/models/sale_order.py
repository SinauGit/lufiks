from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # Gunakan selection_add untuk menambah status baru
    invoice_status = fields.Selection(selection_add=[
        ('full_payment', 'Full Payment'),
        ('partial_payment', 'Partial Payment')
    ])
    
    @api.depends('state', 'order_line.invoice_status', 'invoice_ids.payment_state', 'invoice_ids.state')
    def _get_invoice_status(self):
        super()._get_invoice_status()  # Panggil method asli dulu
        
        for order in self:
            invoices = order.invoice_ids.filtered(lambda inv: inv.state != 'cancel')
            if not invoices:
                continue
                
            # Cek status pembayaran invoice
            payment_states = invoices.mapped('payment_state')
            
            if all(state == 'in_payment' for state in payment_states):
                order.invoice_status = 'full_payment'
            elif any(state == 'partial' for state in payment_states):
                order.invoice_status = 'partial_payment'