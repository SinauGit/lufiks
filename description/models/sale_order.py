from odoo import fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    up_field = fields.Char(string="Up", help="Field untuk menyimpan informasi Up")
    
    # def action_sync_all_lines(self):
    #     """
    #     Metode untuk sinkronisasi semua nama baris order dengan invoice line
    #     """
    #     for order in self:
    #         for line in order.order_line:
    #             line.sync_name_from_invoice_line()
        
    #     return True 