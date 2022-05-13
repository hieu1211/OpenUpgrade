from openupgradelib import openupgrade


def _fill_stock_picking_type_reservation_method(env):
    openupgrade.logged_query(
        env.cr,
        """
            ALTER TABLE stock_picking_type
            ADD COLUMN IF NOT EXISTS reservation_method VARCHAR;
            UPDATE stock_picking_type
            SET reservation_method = 'at_confirm';
        """,
    )


def _create_column_to_avoid_computing(env):
    openupgrade.logged_query(
        env.cr,
        """
            ALTER TABLE stock_quant
                ADD COLUMN IF NOT EXISTS inventory_date date,
                ADD COLUMN IF NOT EXISTS inventory_diff_quantity FLOAT,
                ADD COLUMN IF NOT EXISTS inventory_quantity FLOAT,
                ADD COLUMN IF NOT EXISTS inventory_quantity_set BOOLEAN,
                ADD COLUMN IF NOT EXISTS reservation_date date;
        """,
    )


def _fill_stock_quant_package_package_use(env):
    openupgrade.logged_query(
        env.cr,
        """
            ALTER TABLE stock_quant_package
            ADD COLUMN IF NOT EXISTS package_use VARCHAR;
            UPDATE stock_quant_package
            SET package_use = 'disposable';
        """,
    )


def _fill_stock_quan_package_name_if_null(env):
    openupgrade.logged_query(
        env.cr,
        """
            UPDATE stock_quant_package
            SET name = 'Unknown Pack'
            WHERE name IS NULL;
        """,
    )


def _fill_stock_location_cyclic_inventory_frequency(env):
    openupgrade.logged_query(
        env.cr,
        """
            ALTER TABLE stock_location
            ADD COLUMN IF NOT EXISTS cyclic_inventory_frequency INTEGER;
            UPDATE stock_location
            SET cyclic_inventory_frequency = 0;
        """,
    )


def _fill_stock_quant_in_date(env):
    openupgrade.logged_query(
        env.cr,
        """
            UPDATE stock_quant
            SET in_date = NOW()
            WHERE in_date IS NULL;
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    _fill_stock_picking_type_reservation_method(env)
    _create_column_to_avoid_computing(env)
    _fill_stock_quant_package_package_use(env)
    _fill_stock_quan_package_name_if_null(env)
    _fill_stock_location_cyclic_inventory_frequency(env)
    _fill_stock_quant_in_date(env)
