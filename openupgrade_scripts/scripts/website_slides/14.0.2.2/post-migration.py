from openupgradelib import openupgrade


def _update_groups_menuitem(env):
    grp_officer = env.ref("website_slides.group_website_slides_officer")
    env.ref("website_slides.website_slides_menu_root").groups_id = [
        (6, 0, grp_officer.ids),
    ]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env.cr, "website_slides", "14.0.2.2/noupdate_changes.xml")

    openupgrade.delete_record_translations(
        env.cr,
        "website_slides",
        [
            "mail_template_slide_channel_invite",
            "slide_template_published",
            "slide_template_shared",
        ],
    )
    env["slide.channel.partner"].search([])._recompute_completion()
    openupgrade.copy_fields_multilang(
        env.cr,
        "slide.channel",
        "slide_channel",
        ["description_short"],
        "id",
        "slide.channel",
        "slide_channel",
        ["description"],
        False,
    )
    _update_groups_menuitem(env)
