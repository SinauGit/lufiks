# ©  2008-2022 Deltatech
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ProductionLot(models.Model):
    _inherit = "stock.lot"

    inventory_value = fields.Float("Inventory value")
    unit_price = fields.Float("Unit Price")
    input_price = fields.Float("Input Price")
    input_date = fields.Date(string="Input date")
    location_id = fields.Many2one("stock.location", compute="_compute_location", store=True)
    purchase_order_id = fields.Many2one("purchase.order", string="Purchase Order", readonly=True)
    purchase_order_name = fields.Char(string="PO Number", readonly=True)

    @api.depends("quant_ids")
    def _compute_location(self):
        for lot in self:
            quants = lot.quant_ids.filtered(lambda x: x.quantity > 0)
            if len(quants) > 1:  # multiple quants, can be in different locations
                lot.location_id = False
            else:
                lot.location_id = quants.location_id

    def action_recompute_unit_price(self):
        """
        Recompute unit_price, input_price, inventory_value untuk lot/serial number
        dari data historis stock move
        """
        for lot in self:
            # Skip jika sudah ada nilai
            if lot.unit_price and lot.input_price:
                continue

            # Cari stock move line pertama yang membawa lot/serial ini masuk ke internal location
            move_line = self.env['stock.move.line'].search([
                ('lot_id', '=', lot.id),
                ('state', '=', 'done'),
                ('location_id.usage', '=', 'supplier'),
                ('location_dest_id.usage', 'in', ['internal', 'transit'])
            ], order='date asc', limit=1)

            if move_line:
                # Ambil price dari move
                price_unit = move_line.move_id.price_unit
                qty_done = move_line.qty_done
                
                # Cari purchase order dari move
                purchase_order = False
                purchase_order_name = False
                if move_line.move_id.purchase_line_id:
                    purchase_order = move_line.move_id.purchase_line_id.order_id
                    purchase_order_name = purchase_order.name
                
                values = {
                    'input_price': price_unit,
                    'unit_price': price_unit,
                    'inventory_value': price_unit * qty_done if lot.product_id.tracking == 'serial' else price_unit * lot.product_qty,
                    'input_date': move_line.date.date() if move_line.date else fields.Date.today(),
                    'purchase_order_id': purchase_order.id if purchase_order else False,
                    'purchase_order_name': purchase_order_name,
                }
                lot.write(values)
                continue

            # Jika tidak ada move dari supplier, coba cari dari stock valuation layer
            svl = self.env['stock.valuation.layer'].search([
                ('stock_move_id.move_line_ids.lot_id', '=', lot.id),
                ('quantity', '>', 0)
            ], order='create_date asc', limit=1)

            if svl and svl.quantity:
                unit_cost = abs(svl.value / svl.quantity) if svl.quantity else 0
                values = {
                    'input_price': unit_cost,
                    'unit_price': unit_cost,
                    'inventory_value': unit_cost if lot.product_id.tracking == 'serial' else unit_cost * lot.product_qty,
                }
                lot.write(values)
                continue

            # Fallback: gunakan standard price dari product
            if lot.product_id and not lot.unit_price:
                standard_price = lot.product_id.standard_price
                values = {
                    'unit_price': standard_price,
                    'inventory_value': standard_price if lot.product_id.tracking == 'serial' else standard_price * lot.product_qty,
                }
                lot.write(values)

        return True

    def action_recompute_all_unit_price(self):
        """
        Action untuk recompute semua lot/serial number yang belum punya unit_price
        """
        lots_without_price = self.search([
            '|',
            ('unit_price', '=', 0),
            ('unit_price', '=', False)
        ])
        
        if lots_without_price:
            lots_without_price.action_recompute_unit_price()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Recompute Success',
                    'message': f'{len(lots_without_price)} serial/lot numbers have been recomputed.',
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Records',
                    'message': 'All serial/lot numbers already have unit price.',
                    'type': 'info',
                    'sticky': False,
                }
            }
