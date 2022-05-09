from openupgradelib import openupgrade


def _rename_fields(env):
    openupgrade.rename_fields(
        env,
        [
            (
                "mail.activity.type",
                "mail_activity_type",
                "default_next_type_id",
                "triggered_next_type_id",
            ),
            (
                "mail.activity.type",
                "mail_activity_type",
                "next_type_ids",
                "suggested_next_type_ids",
            ),
            (
                "mail.activity.type",
                "mail_activity_type",
                "default_description",
                "default_note",
            ),
            ("mail.message", "mail_message", "no_auto_thread", "reply_to_force_new"),
            ("mail.notification", "mail_notification", "mail_id", "mail_mail_id"),
        ],
    )


def _detele_sql_constraint(env):
    openupgrade.logged_query(
        env.cr,
        """ALTER TABLE mail_followers
           DROP CONSTRAINT IF EXISTS
               mail_followers_mail_followers_res_channel_res_model_id_uniq;
           ALTER TABLE mail_followers
           DROP CONSTRAINT IF EXISTS mail_followers_partner_xor_channel;
           ALTER TABLE mail_message
           DROP CONSTRAINT IF EXISTS
               mail_message_res_partner_needaction_rel_notification_partner_required;
        """,
    )
    openupgrade.delete_records_safely_by_xml_id(
        env, ["crm.constraint_crm_lead_tag_name_uniq"]
    )


def _rename_tables(env):
    openupgrade.rename_tables(
        env.cr, [("mail_message_res_partner_needaction_rel", "mail_notification")]
    )


def _install_new_module(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE ir_module_module
        SET state='to install'
        WHERE name = 'mail_group' AND state='uninstalled';
        """,
    )


def _delete_channel_follower_records(env):
    openupgrade.logged_query(
        env.cr,
        """
        DELETE FROM mail_followers
        WHERE partner_id IS NULL;
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    _rename_fields(env)
    _rename_tables(env)
    _detele_sql_constraint(env)
    _install_new_module(env)
    _delete_channel_follower_records(env)
    openupgrade.copy_columns(
        env.cr,
        {
            "mail_activity_type": [
                ("force_next", None, None),
                ("res_model_id", None, None),
            ],
            "mail_notification": [("failure_type", None, None)],
        },
    )
