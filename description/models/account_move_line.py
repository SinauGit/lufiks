from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    @api.onchange('name')
    def _onchange_name_update_so_line(self):
        """
        Ketika kolom name (Label) pada invoice line diubah, 
        otomatis update kolom name (description) pada sales order line
        """
        # Hanya melakukan update jika ada perubahan dan ada sale_line_ids
        if self.name and self.sale_line_ids and self.move_id.move_type in ['out_invoice', 'out_refund']:
            for sale_line in self.sale_line_ids:
                # Update kolom name pada semua sale order line yang terkait
                sale_line.name = self.name
    
    @api.model
    def create(self, vals):
        """Override create method untuk memastikan update name pada sale order line ketika invoice line dibuat"""
        # Buat dulu invoice line
        line = super(AccountMoveLine, self).create(vals)
        
        # Jika ada kolom name dan sale_line_ids, update sale order line
        if line.name and line.sale_line_ids and line.move_id.move_type in ['out_invoice', 'out_refund']:
            for sale_line in line.sale_line_ids:
                _logger.info(f"[CREATE] Updating SO line name to '{line.name}' for SO line ID {sale_line.id}")
                sale_line.sudo().write({'name': line.name})
                
        return line
    
    def write(self, vals):
        """Override write method untuk memastikan update name pada sale order line ketika invoice line diupdate"""
        result = super(AccountMoveLine, self).write(vals)
        
        # Jika yang diupdate adalah kolom name
        if 'name' in vals and vals.get('name'):
            for line in self:
                # Hanya proses untuk invoice customer (out_invoice/out_refund)
                if line.move_id.move_type in ['out_invoice', 'out_refund'] and line.sale_line_ids:
                    for sale_line in line.sale_line_ids:
                        # Update name di sale order line tanpa trigger onchange lagi
                        sale_line.sudo().write({'name': vals.get('name')})
        
        return result


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    def action_post(self):
        """Override action_post untuk memastikan deskripsi di SO tetap konsisten setelah konfirmasi invoice"""
        # Panggil metode asli terlebih dahulu
        result = super(AccountMove, self).action_post()
        
        # Jika invoice yang dikonfirmasi adalah invoice customer
        if self.move_type in ['out_invoice', 'out_refund']:
            # Setelah invoice dikonfirmasi, sinkronkan kembali nama dari invoice line ke sales order line
            for line in self.invoice_line_ids:
                if line.sale_line_ids:
                    for sale_line in line.sale_line_ids:
                        if line.name and line.name != sale_line.name:
                            _logger.info(f"[POST] Syncing SO line name from '{sale_line.name}' to '{line.name}' after invoice confirmation")
                            sale_line.sudo().write({'name': line.name})
        
        return result