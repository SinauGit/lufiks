# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import ValidationError

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.constrains("default_code")
    def _check_default_code_unique_ci(self):
        """
        Validasi Python agar pesan error lebih ramah.
        Unik secara case-insensitive, abaikan nilai kosong.
        """
        for rec in self:
            code = (rec.default_code or "").strip()
            if not code:
                continue
            # Cek eksak case-insensitive menggunakan SQL agar presisi & cepat
            self.env.cr.execute(
                """
                SELECT 1
                  FROM product_product
                 WHERE id <> %s
                   AND default_code IS NOT NULL
                   AND trim(default_code) <> ''
                   AND lower(default_code) = lower(%s)
                 LIMIT 1
                """,
                (rec.id or 0, code),
            )
            if self.env.cr.fetchone():
                raise ValidationError(
                    _("Internal Reference '%s' already used in other products (case-insensitive check).") % code
                )

    def init(self):
        """
        Tambah UNIQUE INDEX parsial di database:
        - Unik pada lower(default_code)  => case-insensitive
        - Hanya untuk default_code yang tidak kosong
        Catatan: jika sudah ada duplikasi di data saat ini, pembuatan index akan gagal.
        Perbaiki duplikasi dulu lalu install ulang modul.
        """
        super().init()
        self._cr.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS product_default_code_ci_uniq_idx
                ON product_product (lower(default_code))
             WHERE default_code IS NOT NULL AND trim(default_code) <> '';
            """
        )
