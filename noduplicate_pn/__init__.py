from . import models

def uninstall_hook(cr, registry):
    # Hapus index unik saat uninstall
    cr.execute("DROP INDEX IF EXISTS product_default_code_ci_uniq_idx;")
