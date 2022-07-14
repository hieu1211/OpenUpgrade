from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Load noupdate changes
    openupgrade.load_data(env.cr, "website_slides", "15.0.2.4/noupdate_changes.xml")
    openupgrade.delete_record_translations(
        env.cr,
        "website_slides",
        [
            "mail_template_slide_channel_invite",
            "slide_template_published",
            "slide_template_shared",
            "mail_notification_channel_invite",
        ],
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE slide_channel_tag
        SET color = trunc(random() * 11 + 1)
        WHERE color IS NULL;
        """,
    )
