from datetime import timedelta
import pytz
import datetime
from Script import script
from info import *
from utils import get_seconds
from database.users_chats_db import db
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from database.referdb import referdb

@Client.on_message(filters.command("myinfo"))
async def check_user_info(client, message):
    # Log when the command is received
    print("Received /myinfo command.")

    # Determine user ID to retrieve information
    if len(message.command) == 2:
        try:
            user_id = int(message.command[1])  # Extract the user_id from the command
            user = await client.get_users(user_id)
        except ValueError:
            return await message.reply_text("⚠ Invalid user ID format. Please provide a valid user ID.")
    else:
        user_id = message.from_user.id  # Use the sender's user_id if not provided
        user = message.from_user

    user_mention = user.mention

    # Log the user ID and mention
    print(f"Checking info for user ID: {user_id}, Mention: {user_mention}")

    # Fetch referral points
    referral_points = referdb.get_refer_points(user_id) or 0  # Ensure it defaults to 0 if none found
    print(f"Referral points for user {user_id}: {referral_points}")

    # Check if the user has premium access
    has_premium = await db.has_premium_access(user_id)
    print(f"User {user_id} has premium access: {has_premium}")

    # Construct user info based on premium access
    if has_premium:
        remaining_time = await db.check_remaining_usage(user_id)
        print(f"Remaining time for user {user_id}: {remaining_time}")

        # Format remaining time
        days = remaining_time.days
        hours, remainder = divmod(remaining_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_remaining_time = f"{days} day(s), {hours} hr(s), {minutes} min(s), {seconds} sec(s)"

        # Calculate expiry date and time in IST (India Standard Time)
        current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        expiry_time = current_time + remaining_time
        expiry_date = expiry_time.strftime("%d-%m-%Y")
        expiry_time = expiry_time.strftime("%I:%M:%S %p")  # 12-hour format

        subscribed_status = "True"  # User has premium
        user_status = "Paid User"

        user_info_text = (
            f"📝 <u>User Information</u>:\n\n"
            f"›› Username: {user_mention}\n"
            f"›› User ID: <code>{user_id}</code>\n"
            f"›› Status: {user_status}\n"
            f"›› Subscribed: {subscribed_status}\n"
            f"›› Expiry Date: {expiry_date}\n"
            f"›› Expiry Time: {expiry_time}\n"
            f"›› Remaining Time: {formatted_remaining_time}\n"
            f"›› Referral Points: {referral_points}"
        )
    else:
        subscribed_status = "False"  # User does not have premium
        user_status = "Free User"

        user_info_text = (
            f"📝 <u>User Information</u>:\n\n"
            f"›› Username: {user_mention}\n"
            f"›› User ID: <code>{user_id}</code>\n"
            f"›› Status: {user_status}\n"
            f"›› Subscribed: {subscribed_status}\n"
            f"›› Referral Points: {referral_points}\n"
            "⚠ User does not have premium access."
        )

    # Create inline buttons
    inline_buttons = [
        [
            InlineKeyboardButton("• Updates", url="https://t.me/CodeFlix_Bots"),
            InlineKeyboardButton("Get Premium •", callback_data="seeplans")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(inline_buttons)

    # Send the user info as a text message
    await message.reply_text(
        text=user_info_text,
        reply_markup=reply_markup
    )
