from odoo import fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    up_field = fields.Char(string="Up", help="Field untuk menyimpan informasi Up") 