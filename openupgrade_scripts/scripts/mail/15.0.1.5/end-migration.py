from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Fill values for mail_group model
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE mail_group ADD COLUMN IF NOT EXISTS legacy_channel_id INTEGER;
        INSERT INTO mail_group(name,
                                active,
                                alias_id,
                                description,
                                moderation,
                                moderation_notify,
                                moderation_notify_msg,
                                moderation_guidelines,
                                moderation_guidelines_msg,
                                access_mode,
                                access_group_id,
                                create_uid,
                                create_date,
                                write_uid,
                                write_date,
                                legacy_channel_id)
        SELECT name,
                active,
                alias_id,
                description,
                moderation,
                moderation_notify,
                moderation_notify_msg,
                moderation_guidelines,
                moderation_guidelines_msg,
                CASE WHEN public = 'private' THEN 'public' ELSE public END,
                group_public_id,
                create_uid,
                create_date,
                write_uid,
                write_date,
                id
        FROM mail_channel
        WHERE email_send = True;
        """,
    )

    # Fill values for mail_group_member model
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO mail_group_member(email,
                                        mail_group_id,
                                        partner_id,
                                        create_uid,
                                        create_date,
                                        write_uid,
                                        write_date)
        SELECT res_partner.email,
                mail_group.id,
                mail_channel_partner.partner_id,
                mail_channel_partner.create_uid,
                mail_channel_partner.create_date,
                mail_channel_partner.write_uid,
                mail_channel_partner.write_date
        FROM mail_channel_partner
        JOIN mail_group
            ON mail_channel_partner.channel_id = mail_group.legacy_channel_id
        LEFT JOIN res_partner
            ON mail_channel_partner.partner_id = res_partner.id;
        """,
    )
    mail_group_members = env["mail.group.member"].search([])
    mail_group_members._compute_email_normalized()

    # Fill values for Many2many table between mail_group and res_user
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO mail_group_moderator_rel(mail_group_id, res_users_id)
        SELECT mail_group.id,
                mail_channel_moderator_rel.res_users_id
        FROM mail_channel_moderator_rel
        JOIN mail_group
        ON mail_channel_moderator_rel.mail_channel_id = mail_group.legacy_channel_id;
        """,
    )

    # Fill values for mail_group_moderation model
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO mail_group_moderation(email,
                                            status,
                                            mail_group_id,
                                            create_uid,
                                            create_date,
                                            write_uid,
                                            write_date)
        SELECT mail_moderation.email,
                mail_moderation.status,
                mail_group.id,
                mail_moderation.create_uid,
                mail_moderation.create_date,
                mail_moderation.write_uid,
                mail_moderation.write_date
        FROM mail_moderation
        JOIN mail_group
        ON mail_moderation.channel_id = mail_group.legacy_channel_id;
        """,
    )

    # Fill values for mail_group_message model
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO mail_group_message(email_from_normalized,
                                        mail_group_id,
                                        mail_message_id,
                                        moderation_status,
                                        moderator_id,
                                        create_uid,
                                        create_date,
                                        write_uid,
                                        write_date)
        SELECT mail_message.email_from,
                mail_group.id,
                mail_message.id,
                mail_message.moderation_status,
                mail_message.moderator_id,
                mail_message.create_uid,
                mail_message.create_date,
                mail_message.write_uid,
                mail_message.write_date
        FROM mail_message
        JOIN mail_channel
            ON mail_message.model = 'mail.channel'
                AND mail_message.res_id in
                    (SELECT legacy_channel_id FROM mail_group)
        JOIN mail_group
            ON mail_group.legacy_channel_id = mail_channel.id;
        WITH subquery as (
            SELECT gm1.id as id , gm2.id as parent
            FROM mail_group_message gm1
            JOIN mail_message ms1
                ON ms1.id = gm1.mail_message_id
            JOIN mail_group_message gm2
                ON gm2.mail_message_id = ms1.parent_id
        )
        UPDATE mail_group_message gm1
        SET group_message_parent_id = subquery.parent
        FROM subquery
        WHERE gm1.id = subquery.id;
        UPDATE mail_message
        SET model = 'mail.group'
        FROM mail_group_message
        WHERE model = 'mail.channel'
            AND mail_group_message.mail_message_id = mail_message.id;
        """,
    )

    # Transfer attachment to new model
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE ir_attachment as att
        SET res_model = 'mail.group',
            res_id = mg.id
        FROM mail_group AS mg
        WHERE att.res_field = 'image_128'
            AND mg.legacy_channel_id = att.res_id
            AND att.res_model = 'mail.channel';
        """,
    )

    # Remove data tranfered
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE mail_moderation
        DROP CONSTRAINT IF EXISTS mail_moderation_channel_id_fkey;
        DELETE FROM mail_channel
            WHERE email_send = True;
        ALTER TABLE mail_group DROP COLUMN legacy_channel_id;
        """,
    )
