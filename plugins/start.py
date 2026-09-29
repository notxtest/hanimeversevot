from helper.helper_func import *
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
import humanize
from config import MSG_EFFECT, OWNER_ID
from plugins.shortner import get_short
from helper.helper_func import get_messages, force_sub, decode, batch_auto_del_notification
import asyncio
import secrets
import random
from datetime import datetime


# ===============================================================#
# BYPASS / TOKEN CONFIG
# ===============================================================#

BYPASS_WINDOW = 60


# ===============================================================#
# BYPASS / TOKEN HELPERS
# ===============================================================#

def generate_new_token():
    """
    Generate a completely new random token.

    A new token is generated:
    1. When an original link is opened for the first time.
    2. When a bypass is detected.

    Existing active sessions reuse their current token.
    """
    return secrets.token_urlsafe(18)


def get_open_link_url(client, token):
    """
    Generate Telegram /start URL for a token.
    """
    return f"https://t.me/{client.username}?start={token}"


def get_short_token(base64_string):
    """
    Existing short-token format:

        yu3elk{CURRENT_TOKEN}7

    Returns only CURRENT_TOKEN.
    """
    if (
        base64_string.startswith("yu3elk")
        and base64_string.endswith("7")
    ):
        return base64_string[6:-1]

    return None


async def send_open_link_message(
    client,
    message,
    original_token,
    current_token
):
    """
    Send the shortener message.

    The shortener receives the CURRENT token.
    """

    open_link = get_open_link_url(
        client,
        f"yu3elk{current_token}7"
    )

    try:
        short_link = get_short(
            open_link,
            client
        )

    except Exception as e:
        client.LOGGER(
            __name__,
            client.name
        ).warning(
            f"Shortener failed: {e}"
        )

        await message.reply(
            "Couldn't generate short link."
        )

        return False

    short_photo = client.messages.get(
        "SHORT_PIC",
        ""
    )

    short_caption = client.messages.get(
        "SHORT_MSG",
        ""
    )

    tutorial_link = getattr(
        client,
        "tutorial_link",
        "https://t.me/+5qAwb0OP6-02MTdl"
    )

    await client.send_photo(
        chat_id=message.chat.id,
        photo=short_photo,
        caption=short_caption,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "• ᴏᴘᴇɴ ʟɪɴᴋ",
                    url=short_link
                ),
                InlineKeyboardButton(
                    "ᴛᴜᴛᴏʀɪᴀʟ •",
                    url=tutorial_link
                )
            ],
            [
                InlineKeyboardButton(
                    " • ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ •",
                    url="https://t.me/CineVines_Bot"
                )
            ]
        ])
    )

    return True


# ===============================================================#
# /START
# ===============================================================#

@Client.on_message(filters.command("start") & filters.private)
@force_sub
async def start_command(
    client: Client,
    message: Message
):

    user_id = message.from_user.id

    # ===========================================================#
    # 1. ADD USER IF NOT PRESENT
    # ===========================================================#

    present = await client.mongodb.present_user(
        user_id
    )

    if not present:
        try:
            await client.mongodb.add_user(
                user_id
            )

        except Exception as e:
            client.LOGGER(
                __name__,
                client.name
            ).warning(
                f"Error adding a user:\n{e}"
            )

    # ===========================================================#
    # 2. CHECK BAN
    # ===========================================================#

    is_banned = await client.mongodb.is_banned(
        user_id
    )

    if is_banned:
        return await message.reply(
            "**You have been banned from using this bot!**"
        )

    text = message.text

    # ===========================================================#
    # LINK START
    # ===========================================================#

    if len(text) > 7:

        try:
            original_payload = text.split(
                " ",
                1
            )[1]

            base64_string = original_payload

            is_short_link = False
            current_token = None

            # ---------------------------------------------------#
            # SHORT TOKEN FORMAT
            #
            # yu3elk{CURRENT_TOKEN}7
            # ---------------------------------------------------#

            if (
                base64_string.startswith("yu3elk")
                and base64_string.endswith("7")
            ):

                current_token = get_short_token(
                    base64_string
                )

                if not current_token:
                    return await message.reply(
                        "⚠️ Invalid or expired link."
                    )

                is_short_link = True

        except IndexError:
            return await message.reply(
                "Invalid command format."
            )

        # =======================================================#
        # 3. CHECK PREMIUM
        # =======================================================#

        is_user_pro = await client.mongodb.is_pro(
            user_id
        )

        # =======================================================#
        # 4. CHECK SHORTENER STATUS
        # =======================================================#

        shortner_enabled = getattr(
            client,
            "shortner_enabled",
            True
        )

        # =======================================================#
        # 5. ORIGINAL TOKEN
        # =======================================================#

        original_token = base64_string

        # =======================================================#
        # FREE USER + SHORTENER ENABLED
        # =======================================================#

        if (
            not is_user_pro
            and user_id != OWNER_ID
            and shortner_enabled
        ):

            # ===================================================#
            # ORIGINAL LINK
            # ===================================================#

            if not is_short_link:

                # ------------------------------------------------#
                # Check for an existing active session.
                #
                # If one exists, reuse its CURRENT token.
                #
                # A new token is NOT created every time.
                # ------------------------------------------------#

                active_session = (
                    await client.mongodb
                    .get_active_bypass_session(
                        original_token
                    )
                )

                if active_session:

                    current_token = (
                        active_session.get(
                            "current_token"
                        )
                    )

                else:

                    # --------------------------------------------#
                    # First attempt → create new token
                    # --------------------------------------------#

                    current_token = generate_new_token()

                    await client.mongodb.create_bypass_session(
                        original_token=original_token,
                        current_token=current_token,
                        user_id=user_id
                    )

                # ------------------------------------------------#
                # Send shortener link
                # ------------------------------------------------#

                await send_open_link_message(
                    client=client,
                    message=message,
                    original_token=original_token,
                    current_token=current_token
                )

                return

            # ===================================================#
            # SHORTENER RESULT
            # ===================================================#

            session = await client.mongodb.get_bypass_session(
                current_token
            )

            # ---------------------------------------------------#
            # Session not found
            # ---------------------------------------------------#

            if not session:

                return await message.reply(
                    "⚠️ Invalid or expired link."
                )

            # ---------------------------------------------------#
            # IMPORTANT:
            #
            # Get the REAL original token from the database.
            #
            # This fixes the previous bug where:
            #
            # original_token = yu3elk{token}7
            #
            # was incorrectly compared with the database
            # original_token.
            # ---------------------------------------------------#

            original_token = session.get(
                "original_token"
            )

            if not original_token:

                return await message.reply(
                    "⚠️ Invalid or expired link."
                )

            # ---------------------------------------------------#
            # Token invalidated?
            # ---------------------------------------------------#

            if session.get(
                "invalid",
                False
            ):

                return await message.reply(
                    "⚠️ This link is no longer valid."
                )

            # ===================================================#
            # BYPASS DETECTION
            # ===================================================#

            created_at = session.get(
                "created_at"
            )

            if created_at:

                try:

                    now = datetime.now()

                    # MongoDB normally returns a naive datetime
                    # when stored using datetime.now().
                    elapsed = (
                        now - created_at
                    ).total_seconds()

                    # ------------------------------------------------#
                    # LESS THAN 60 SECONDS
                    # = BYPASS DETECTED
                    # ------------------------------------------------#

                    if elapsed < BYPASS_WINDOW:

                        # --------------------------------------------#
                        # INVALIDATE OLD TOKEN
                        # --------------------------------------------#

                        await client.mongodb.invalidate_bypass_token(
                            current_token
                        )

                        # --------------------------------------------#
                        # CREATE COMPLETELY NEW TOKEN
                        # --------------------------------------------#

                        new_token = generate_new_token()

                        await client.mongodb.create_bypass_session(
                            original_token=original_token,
                            current_token=new_token,
                            user_id=user_id
                        )

                        # --------------------------------------------#
                        # TRY AGAIN
                        #
                        # Goes to ORIGINAL /start token.
                        #
                        # The original link will automatically
                        # use the newly created active token.
                        # --------------------------------------------#

                        try_again_url = get_open_link_url(
                            client,
                            original_token
                        )

                        # --------------------------------------------#
                        # BYPASS MESSAGE
                        # --------------------------------------------#

                        bypass_message = (
                            "> ⚠️ **Bypass Detected!**\n\n"
                            "> Please don't try to bypass the shortener. "
                            "Repeated bypass attempts may result in a permanent ban.\n\n"
                            "> If you believe this happened by mistake, "
                            "please contact **@Cinevines_bot** for help."
                        )

                        await message.reply(
                            bypass_message,
                            reply_markup=InlineKeyboardMarkup([
                                [
                                    InlineKeyboardButton(
                                        "🔄 TRY AGAIN",
                                        url=try_again_url
                                    )
                                ]
                            ])
                        )

                        return

                except Exception as e:

                    client.LOGGER(
                        __name__,
                        client.name
                    ).warning(
                        f"Bypass time check failed: {e}"
                    )

            # ===================================================#
            # NORMAL SUCCESS
            #
            # If 60+ seconds have passed, continue normally.
            # ===================================================#

        # =======================================================#
        # 6. DECODE AND PREPARE FILE IDS
        # =======================================================#

        try:

            # ---------------------------------------------------#
            # For short-link:
            #
            # current token → database session
            # database session → original token
            # original token → decode
            # ---------------------------------------------------#

            if is_short_link:

                session = await client.mongodb.get_bypass_session(
                    current_token
                )

                if not session:

                    return await message.reply(
                        "⚠️ Invalid or expired link."
                    )

                if session.get(
                    "invalid",
                    False
                ):

                    return await message.reply(
                        "⚠️ This link is no longer valid."
                    )

                base64_string = session.get(
                    "original_token"
                )

                if not base64_string:

                    return await message.reply(
                        "⚠️ Invalid or expired link."
                    )

            # ===================================================#
            # DECODE
            # ===================================================#

            string = await decode(
                base64_string
            )

            argument = string.split(
                "-"
            )

            ids = []
            source_channel_id = None

            # ===================================================#
            # BATCH
            # ===================================================#

            if len(argument) == 3:

                encoded_start = int(
                    argument[1]
                )

                encoded_end = int(
                    argument[2]
                )

                # ------------------------------------------------#
                # PRIMARY CHANNEL
                # ------------------------------------------------#

                primary_multiplier = abs(
                    client.db
                )

                start_primary = int(
                    encoded_start /
                    primary_multiplier
                )

                end_primary = int(
                    encoded_end /
                    primary_multiplier
                )

                if (
                    encoded_start %
                    primary_multiplier == 0
                    and
                    encoded_end %
                    primary_multiplier == 0
                ):

                    source_channel_id = client.db

                    start = start_primary
                    end = end_primary

                    client.LOGGER(
                        __name__,
                        client.name
                    ).info(
                        f"Decoded batch from primary "
                        f"channel {source_channel_id}: "
                        f"{start}-{end}"
                    )

                else:

                    # --------------------------------------------#
                    # SECONDARY CHANNELS
                    # --------------------------------------------#

                    db_channels = getattr(
                        client,
                        "db_channels",
                        {}
                    )

                    for channel_id_str in db_channels.keys():

                        channel_id = int(
                            channel_id_str
                        )

                        channel_multiplier = abs(
                            channel_id
                        )

                        start_test = int(
                            encoded_start /
                            channel_multiplier
                        )

                        end_test = int(
                            encoded_end /
                            channel_multiplier
                        )

                        if (
                            encoded_start %
                            channel_multiplier == 0
                            and
                            encoded_end %
                            channel_multiplier == 0
                        ):

                            source_channel_id = (
                                channel_id
                            )

                            start = start_test
                            end = end_test

                            client.LOGGER(
                                __name__,
                                client.name
                            ).info(
                                f"Decoded batch from secondary "
                                f"channel {source_channel_id}: "
                                f"{start}-{end}"
                            )

                            break

                    # --------------------------------------------#
                    # FALLBACK TO PRIMARY
                    # --------------------------------------------#

                    if source_channel_id is None:

                        source_channel_id = client.db

                        start = start_primary
                        end = end_primary

                ids = (
                    range(
                        start,
                        end + 1
                    )
                    if start <= end
                    else list(
                        range(
                            start,
                            end - 1,
                            -1
                        )
                    )
                )

            # ===================================================#
            # SINGLE MESSAGE
            # ===================================================#

            elif len(argument) == 2:

                encoded_msg = int(
                    argument[1]
                )

                # ------------------------------------------------#
                # PRIMARY DB CHANNEL
                # ------------------------------------------------#

                if (
                    hasattr(
                        client,
                        "db_channel"
                    )
                    and
                    client.db_channel
                ):

                    primary_multiplier = abs(
                        client.db_channel.id
                    )

                    msg_id_primary = int(
                        encoded_msg /
                        primary_multiplier
                    )

                    if (
                        encoded_msg %
                        primary_multiplier == 0
                    ):

                        source_channel_id = (
                            client.db_channel.id
                        )

                        ids = [
                            msg_id_primary
                        ]

                    else:

                        # ----------------------------------------#
                        # SECONDARY CHANNELS
                        # ----------------------------------------#

                        db_channels = getattr(
                            client,
                            "db_channels",
                            {}
                        )

                        for channel_id_str in db_channels.keys():

                            channel_id = int(
                                channel_id_str
                            )

                            channel_multiplier = abs(
                                channel_id
                            )

                            msg_id_test = int(
                                encoded_msg /
                                channel_multiplier
                            )

                            if (
                                encoded_msg %
                                channel_multiplier == 0
                            ):

                                source_channel_id = (
                                    channel_id
                                )

                                ids = [
                                    msg_id_test
                                ]

                                break

                        # ----------------------------------------#
                        # FALLBACK
                        # ----------------------------------------#

                        if source_channel_id is None:

                            source_channel_id = (
                                client.db_channel.id
                                if hasattr(
                                    client,
                                    "db_channel"
                                )
                                else client.db
                            )

                            ids = [
                                msg_id_primary
                            ]

                else:

                    # --------------------------------------------#
                    # LEGACY FALLBACK
                    # --------------------------------------------#

                    source_channel_id = client.db

                    ids = [
                        int(
                            encoded_msg /
                            abs(client.db)
                        )
                    ]

        except Exception as e:

            client.LOGGER(
                __name__,
                client.name
            ).warning(
                f"Error decoding base64: {e}"
            )

            return await message.reply(
                "⚠️ Invalid or expired link."
            )

        # =======================================================#
        # 7. GET MESSAGES
        # =======================================================#

        temp_msg = await message.reply(
            "Wait A Sec.."
        )

        messages = []

        try:

            # ---------------------------------------------------#
            # SOURCE CHANNEL
            # ---------------------------------------------------#

            if source_channel_id:

                client.LOGGER(
                    __name__,
                    client.name
                ).info(
                    f"Trying to get messages from "
                    f"source channel: {source_channel_id}"
                )

                try:

                    ids_list = list(
                        ids
                    )

                    msgs = await client.get_messages(
                        chat_id=source_channel_id,
                        message_ids=ids_list
                    )

                    valid_msgs = [
                        msg
                        for msg in msgs
                        if msg is not None
                    ]

                    messages.extend(
                        valid_msgs
                    )

                    client.LOGGER(
                        __name__,
                        client.name
                    ).info(
                        f"Found {len(valid_msgs)} messages "
                        f"from source channel "
                        f"{source_channel_id}"
                    )

                    # ------------------------------------------------#
                    # FALLBACK FOR MISSING MESSAGES
                    # ------------------------------------------------#

                    if len(valid_msgs) < len(ids_list):

                        valid_ids = {
                            msg.id
                            for msg in valid_msgs
                        }

                        missing_ids = [
                            mid
                            for mid in ids_list
                            if mid not in valid_ids
                        ]

                        if missing_ids:

                            client.LOGGER(
                                __name__,
                                client.name
                            ).info(
                                f"Missing {len(missing_ids)} "
                                f"messages, trying fallback system"
                            )

                            additional_messages = (
                                await get_messages(
                                    client,
                                    missing_ids
                                )
                            )

                            messages.extend(
                                additional_messages
                            )

                            client.LOGGER(
                                __name__,
                                client.name
                            ).info(
                                f"Found "
                                f"{len(additional_messages)} "
                                f"additional messages from fallback"
                            )

                except Exception as e:

                    client.LOGGER(
                        __name__,
                        client.name
                    ).warning(
                        f"Error getting messages from source "
                        f"channel {source_channel_id}: {e}"
                    )

                    messages = await get_messages(
                        client,
                        ids
                    )

            else:

                # ------------------------------------------------#
                # MULTI-CHANNEL FALLBACK
                # ------------------------------------------------#

                messages = await get_messages(
                    client,
                    ids
                )

        except Exception as e:

            await temp_msg.edit_text(
                "Something went wrong!"
            )

            client.LOGGER(
                __name__,
                client.name
            ).warning(
                f"Error getting messages: {e}"
            )

            return

        # =======================================================#
        # NO FILES FOUND
        # =======================================================#

        if not messages:

            return await temp_msg.edit(
                "Couldn't find the files in the database."
            )

        await temp_msg.delete()

        # =======================================================#
        # SEND FILES
        # =======================================================#

        yugen_msgs = []

        for msg in messages:

            caption = (
                client.messages.get(
                    "CAPTION",
                    ""
                ).format(
                    previouscaption=(
                        msg.caption.html
                        if msg.caption
                        else msg.document.file_name
                    )
                )
                if bool(
                    client.messages.get(
                        "CAPTION",
                        ""
                    )
                )
                and bool(
                    msg.document
                )
                else (
                    ""
                    if not msg.caption
                    else msg.caption.html
                )
            )

            reply_markup = (
                msg.reply_markup
                if not client.disable_btn
                else None
            )

            try:

                copied_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    reply_markup=reply_markup,
                    protect_content=client.protect
                )

                yugen_msgs.append(
                    copied_msg
                )

            except FloodWait as e:

                await asyncio.sleep(
                    e.x
                )

                copied_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    reply_markup=reply_markup,
                    protect_content=client.protect
                )

                yugen_msgs.append(
                    copied_msg
                )

            except Exception as e:

                client.LOGGER(
                    __name__,
                    client.name
                ).warning(
                    f"Failed to send message: {e}"
                )

        # =======================================================#
        # 8. AUTO DELETE
        # =======================================================#

        if (
            messages
            and
            client.auto_del > 0
        ):

            # Keep original /start payload.
            transfer_link = original_payload

            asyncio.create_task(
                batch_auto_del_notification(
                    bot_username=client.username,
                    messages=yugen_msgs,
                    delay_time=client.auto_del,
                    transfer_link=transfer_link,
                    chat_id=message.from_user.id,
                    client=client
                )
            )

        return

    # ===========================================================#
    # NORMAL /START
    # ===========================================================#

    else:

        buttons = [
            [
                InlineKeyboardButton(
                    "Help",
                    callback_data="about"
                ),
                InlineKeyboardButton(
                    "Close",
                    callback_data="close"
                )
            ]
        ]

        if user_id in client.admins:

            buttons.insert(
                0,
                [
                    InlineKeyboardButton(
                        "⛩️ ꜱᴇᴛᴛɪɴɢꜱ ⛩️",
                        callback_data="settings"
                    )
                ]
            )

        photo = client.messages.get(
            "START_PHOTO",
            ""
        )

        start_caption = client.messages.get(
            "START",
            "Welcome, {mention}"
        ).format(
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            username=(
                None
                if not message.from_user.username
                else "@" + message.from_user.username
            ),
            mention=message.from_user.mention,
            id=message.from_user.id
        )

        if photo:

            await client.send_photo(
                chat_id=message.chat.id,
                photo=photo,
                caption=start_caption,
                message_effect_id=random.choice(MSG_EFFECT),
                reply_markup=InlineKeyboardMarkup(
                    buttons
                )
            )

        else:

            await client.send_message(
                chat_id=message.chat.id,
                text=start_caption,
                message_effect_id=random.choice(MSG_EFFECT),
                reply_markup=InlineKeyboardMarkup(
                    buttons
                )
            )

        return


# ===============================================================#
# /BYPASS
# ===============================================================#

@Client.on_message(
    filters.command("bypass") & filters.private
)
async def bypass_command(
    client: Client,
    message: Message
):

    user_id = message.from_user.id

    # ===========================================================#
    # ADMIN ONLY
    # ===========================================================#

    if (
        user_id != OWNER_ID
        and
        user_id not in client.admins
    ):

        return await message.reply(
            "❌ You are not authorized to use this command."
        )

    try:

        stats = await client.mongodb.get_bypass_statistics()

        total = stats.get(
            "total",
            0
        )

        bypasses = stats.get(
            "bypasses",
            []
        )

        # =======================================================#
        # NO BYPASS
        # =======================================================#

        if total == 0:

            return await message.reply(
                "🛡️ **Bypass Statistics**\n\n"
                "Total Bypasses: `0`\n\n"
                "No bypass detected yet."
            )

        # =======================================================#
        # HEADER
        # =======================================================#

        text = (
            "🛡️ **BYPASS STATISTICS**\n\n"
            f"🔢 **Total Bypasses:** `{total}`\n\n"
        )

        # =======================================================#
        # DETAILS
        # =======================================================#

        for index, data in enumerate(
            bypasses[:50],
            start=1
        ):

            bypass_user = data.get(
                "user_id",
                "Unknown"
            )

            original_token = data.get(
                "original_token",
                "Unknown"
            )

            current_token = data.get(
                "current_token",
                "Unknown"
            )

            bypassed_at = data.get(
                "bypassed_at"
            )

            if bypassed_at:

                bypass_time = bypassed_at.strftime(
                    "%d-%m-%Y %H:%M:%S"
                )

            else:

                bypass_time = "Unknown"

            text += (
                f"**#{index}**\n"
                f"👤 User ID: `{bypass_user}`\n"
                f"🔑 Original: `{original_token}`\n"
                f"🎫 Token: `{current_token}`\n"
                f"🕐 Time: `{bypass_time}`\n\n"
            )

            # ---------------------------------------------------#
            # Telegram message length safety
            # ---------------------------------------------------#

            if len(text) > 3500:

                text += (
                    "Showing latest 50 bypass records."
                )

                break

        await message.reply(
            text
        )

    except Exception as e:

        client.LOGGER(
            __name__,
            client.name
        ).warning(
            f"/bypass error: {e}"
        )

        await message.reply(
            "❌ Failed to load bypass statistics."
        )


# ===============================================================#
# /REQUEST
# ===============================================================#

@Client.on_message(
    filters.command("request") & filters.private
)
async def request_command(
    client: Client,
    message: Message
):

    user_id = message.from_user.id

    is_admin = (
        user_id in client.admins
    )

    is_user_premium = (
        await client.mongodb.is_pro(
            user_id
        )
    )

    # ===========================================================#
    # ADMIN / OWNER
    # ===========================================================#

    if (
        is_admin
        or
        user_id == OWNER_ID
    ):

        await message.reply_text(
            "🔹 **You are my sensei!**\n"
            "This command is only for users."
        )

        return

    # ===========================================================#
    # PREMIUM CHECK
    # ===========================================================#

    if not is_user_premium:

        BUTTON_URL = "https://t.me/hanime_space"

        reply_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💎 Upgrade to Premium",
                    url=BUTTON_URL
                )
            ]
        ])

        await message.reply(
            "❌ **You are not a premium user.**\n"
            "Upgrade to premium to access this feature.",
            reply_markup=reply_markup
        )

        return

    # ===========================================================#
    # REQUEST TEXT
    # ===========================================================#

    if len(message.command) < 2:

        await message.reply(
            "⚠️ **Send me your request in this format:**\n"
            "`/request Your_Request_Here`"
        )

        return

    requested = " ".join(
        message.command[1:]
    )

    # ===========================================================#
    # SEND REQUEST TO OWNER
    # ===========================================================#

    owner_message = (
        f"📩 **New Request from "
        f"{message.from_user.mention}**\n\n"
        f"🆔 User ID: `{user_id}`\n"
        f"📝 Request: `{requested}`"
    )

    await client.send_message(
        OWNER_ID,
        owner_message
    )

    await message.reply(
        "✅ **Thanks for your request!**\n"
        "Your request will be reviewed soon. Please wait."
    )


# ===============================================================#
# /PROFILE
# ===============================================================#

@Client.on_message(
    filters.command("profile") & filters.private
)
async def my_plan(
    client: Client,
    message: Message
):

    user_id = message.from_user.id

    is_admin = (
        user_id in client.admins
    )

    # ===========================================================#
    # ADMIN / OWNER
    # ===========================================================#

    if (
        is_admin
        or
        user_id == OWNER_ID
    ):

        await message.reply_text(
            "🔹 You're my sensei! "
            "This command is only for users."
        )

        return

    # ===========================================================#
    # PREMIUM CHECK
    # ===========================================================#

    is_user_premium = (
        await client.mongodb.is_pro(
            user_id
        )
    )

    # ===========================================================#
    # PREMIUM USER
    # ===========================================================#

    if is_user_premium:

        await message.reply_text(
            "**👤 Profile Information:**\n\n"
            "🔸 Ads: Disabled\n"
            "🔸 Plan: Premium\n"
            "🔸 Request: Enabled\n\n"
            "🌟 You're a Premium User!"
        )

    # ===========================================================#
    # FREE USER
    # ===========================================================#

    else:

        await message.reply_text(
            "**👤 Profile Information:**\n\n"
            "🔸 Ads: Enabled\n"
            "🔸 Plan: Free\n"
            "🔸 Request: Disabled\n\n"
            "🔓 Unlock Premium to get more benefits\n"
            "Contact: @CineVines_Bot"
        )