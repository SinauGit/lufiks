# ©  2008-2021 Deltatech
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        # update lot info for reception
        for picking in self:
            for move_line in picking.move_line_ids_without_package:
                if move_line.lot_id:
                    values = {}
                    if move_line.location_id.usage == "supplier" and move_line.location_dest_id.usage in ["internal"]:
                        # Ambil unit_cost dari SVL yang sudah dibuat
                        svl = self.env['stock.valuation.layer'].search([
                            ('stock_move_id', '=', move_line.move_id.id),
                            ('quantity', '>', 0)
                        ], limit=1)
                        
                        if svl and svl.quantity:
                            unit_cost = abs(svl.value / svl.quantity)
                        else:
                            # Fallback ke price_unit jika SVL tidak ditemukan
                            unit_cost = move_line.move_id.price_unit
                        
                        if move_line.product_id.tracking == "serial":
                            values["inventory_value"] = unit_cost * move_line.qty_done
                        else:
                            values["inventory_value"] = unit_cost * move_line.qty_done
                            
                        values["input_price"] = unit_cost
                        values["unit_price"] = unit_cost
                        values["input_date"] = move_line.picking_id.scheduled_date
                        
                        # Tambahkan Purchase Order info
                        if move_line.move_id.purchase_line_id:
                            purchase_order = move_line.move_id.purchase_line_id.order_id
                            values["purchase_order_id"] = purchase_order.id
                            values["purchase_order_name"] = purchase_order.name
                        
                        if move_line.product_id.tracking == "serial":
                            values["location_id"] = move_line.location_dest_id.id
                        move_line.lot_id.write(values)
        return res
