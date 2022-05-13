from openupgradelib import openupgrade


def _fill_data_stock_package_type_and_reference(env):
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE stock_package_type
            ADD COLUMN IF NOT EXISTS product_packaging_id INTEGER;

        INSERT INTO stock_package_type(name,
                                        sequence,
                                        barcode,
                                        company_id,
                                        create_uid,
                                        create_date,
                                        write_uid,
                                        write_date,
                                        product_packaging_id)
        SELECT name,
                sequence,
                barcode,
                company_id,
                create_uid,
                create_date,
                write_uid,
                write_date,
                id
        FROM product_packaging;

        UPDATE product_packaging
        SET package_type_id = stock_package_type.id
        FROM stock_package_type
        WHERE stock_package_type.product_packaging_id = product_packaging.id;

        UPDATE stock_quant_package
        SET package_type_id = stock_package_type.id
        FROM stock_package_type
        WHERE stock_package_type.product_packaging_id = stock_quant_package.packaging_id;

        ALTER TABLE stock_package_type DROP COLUMN product_packaging_id;
        """,
    )


def _fill_stock_move_is_inventory(env):
    openupgrade.logged_query(
        env.cr,
        """
            UPDATE stock_move
            SET is_inventory = True
            Where inventory_id IS NOT NULL;
        """,
    )


def _fill_stock_picking_type_print_label(env):
    openupgrade.logged_query(
        env.cr,
        """
            UPDATE stock_picking_type
            SET print_label = True
            WHERE code = 'outgoing';
        """,
    )


def _create_default_return_type_for_all_warehouses(env):
    picking_type = "return_type_id"
    all_warehouses = env["stock.warehouse"].with_context(active_test=True).search([])
    for wh in all_warehouses:
        sequence_data = wh._get_sequence_values()
        sequence = env["ir.sequence"].create(sequence_data[picking_type])

        max_sequence = env["stock.picking.type"].search_read(
            [("sequence", "!=", False)], ["sequence"], limit=1, order="sequence desc"
        )
        max_sequence = max_sequence and max_sequence[0]["sequence"] or 0

        data_return_type = wh._get_picking_type_update_values()[picking_type]
        create_data, max_sequence = wh._get_picking_type_create_values(max_sequence)

        data_return_type.update(
            {
                "warehouse_id": wh.id,
                "sequence_id": sequence.id,
                **create_data[picking_type],
            }
        )
        env["stock.picking.type"].create(data_return_type)


def _fill_stock_quant_last_inventory_date(env):
    openupgrade.logged_query(
        env.cr,
        """
            UPDATE stock_location sl
            SET last_inventory_date =
                    (SELECT sml.date
                    FROM stock_move_line as sml
                    JOIN stock_move as sm ON sml.move_id = sm.id
                    WHERE sml.company_id = sl.company_id
                        AND sml.state = 'done'
                        AND sm.is_inventory = true
                        AND (sml.location_id = sl.id
                            OR sml.location_dest_id = sl.id)
                    ORDER BY sml.date DESC
                    LIMIT 1
                    );
        """,
    )


def _fill_product_category_packaging_reserve_method(env):
    openupgrade.logged_query(
        env.cr,
        """
            UPDATE product_category
            SET packaging_reserve_method = 'partial';
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env.cr, "stock", "15.0.1.1/noupdate_changes.xml")
    openupgrade.delete_record_translations(
        env.cr,
        "stock",
        ["mail_template_data_delivery_confirmation"],
    )
    # try delete noupdate records
    openupgrade.delete_records_safely_by_xml_id(
        env,
        [
            "stock.stock_inventory_comp_rule",
            "stock.stock_inventory_line_comp_rule",
            "stock.sequence_tracking",
        ],
    )

    openupgrade.convert_field_to_html(env.cr, "stock_picking", "note", "note")

    _fill_data_stock_package_type_and_reference(env)
    _fill_stock_move_is_inventory(env)
    _fill_stock_picking_type_print_label(env)
    _create_default_return_type_for_all_warehouses(env)
    _fill_stock_quant_last_inventory_date(env)
    _fill_product_category_packaging_reserve_method(env)
