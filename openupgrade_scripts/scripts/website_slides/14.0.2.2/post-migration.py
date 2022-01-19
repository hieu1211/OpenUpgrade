from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env.cr, "website_slides", "14.0.2.2/noupdate_changes.xml")
