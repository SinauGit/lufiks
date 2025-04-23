from odoo import models, api, fields

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    # Simpan nama original sebelum diupdate
    original_name = fields.Char(string="Original Name", help="Nama asli sebelum diupdate dari invoice", copy=False)
    
    # Fungsi untuk mengupdate name pada sale order line ketika ada invoice line yang diubah
    def sync_name_from_invoice_line(self):
        """
        Fungsi untuk memperbarui name pada sale order line dari invoice line
        yang terkait, terutama untuk kasus down payment
        """
        for line in self:
            # Simpan nama original jika belum tersimpan
            if not line.original_name and line.name:
                line.original_name = line.name
                
            # Hanya lakukan untuk baris yang memiliki invoice_lines
            if line.invoice_lines:
                for inv_line in line.invoice_lines:
                    if inv_line.move_id.move_type in ['out_invoice', 'out_refund']:
                        # Jika nama invoice line berbeda dengan sale order line, update
                        if inv_line.name and inv_line.name != line.name:
                            line.name = inv_line.name
                            break
    
    # Metode untuk mengembalikan deskripsi ke nilai aslinya
    def restore_original_name(self):
        """
        Mengembalikan deskripsi ke nilai aslinya sebelum diupdate dari invoice
        """
        for line in self:
            if line.original_name:
                line.name = line.original_name
        return True
    
    # Saat line dibuat, simpan nama original
    @api.model
    def create(self, vals):
        """Override create untuk menyimpan nama original"""
        line = super(SaleOrderLine, self).create(vals)
        if line.name and not line.original_name:
            line.original_name = line.name
        return line
    
    # Override metode default
    def _get_sale_order_line_multiline_description_sale(self):
        """ Override untuk hanya menampilkan nama produk """
        self.ensure_one()
        if not self.product_id:
            return ""
        return self.product_id.name