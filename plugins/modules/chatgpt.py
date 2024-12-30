import requests
import time
from pyrogram.enums import ChatAction, ParseMode
from pyrogram import filters, Client
from MukeshAPI import api

from info import *
import qrcode
from io import BytesIO
import re
import os 

# Variables to store stats
total_users = set()  # To keep track of unique users
total_queries = 0  # To count total queries
total_responses = 0  # To count total responses

# Function to get greeting based on time
def get_greeting():
    current_hour = time.localtime().tm_hour
    if current_hour < 12:
        return "Good morning"
    elif 12 <= current_hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"

# Function to send logs to LOG_CHANNEL
async def send_log(bot, message, query, response):
    user_id = message.from_user.id
    user_name = message.from_user.first_name if message.from_user else "Unknown"
    log_message = f"""
**User Query Log**
- **User ID**: `{user_id}`
- **Name**: {user_name}
- **Query**: {query}
- **Response**: {response}
"""
    await bot.send_message(LOG_CHANNEL, log_message, parse_mode=ParseMode.MARKDOWN)

# Basic command for AI interaction
@Client.on_message(filters.command(["chatgpt", "ai", "lucy", "ask", "ucy", "gpt"], prefixes=[".", "L", "l", "", "S", "/"]))
async def chat_gpt(bot, message):
    global total_queries, total_responses
    
    try:
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        
        user_id = message.from_user.id
        name = message.from_user.first_name if message.from_user else "User"
        greeting = get_greeting()

        # Track unique users
        total_users.add(user_id)
        
        if len(message.command) < 2:
            response = f"**{greeting} {name}, how can I assist you today?**"
            await message.reply_text(response)
        else:
            query = message.text.split(' ', 1)[1].strip().lower()  # Convert the query to lowercase
            
            # Check if it's a custom query for owner
            if "who is your owner" in query:
                response = "›› **__My owner is Subaru. He created me__**"
                await message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            else:
                total_queries += 1  # Increment query count
                response = api.gemini(query)["results"]
                formatted_response = f"›› **__{response}__**"
                await message.reply_text(formatted_response, parse_mode=ParseMode.MARKDOWN)
                total_responses += 1  # Increment response count

        # Log the user interaction
        await send_log(bot, message, query if len(message.command) > 1 else "No query", response)
    
    except Exception as e:
        await message.reply_text(f"**Error:** _{e}_", parse_mode=ParseMode.MARKDOWN)


# Admin commands: /aistats to view stats
@Client.on_message(filters.command(["aistats"], prefixes=["/", "."]) & filters.user(ADMINS))
async def ai_stats(bot, message):
    global total_queries, total_responses
    
    try:
        total_users_count = len(total_users)
        stats_message = f"""
**AI Bot Stats:**
- **Total Unique Users**: {total_users_count}
- **Total Queries Processed**: {total_queries}
- **Total Responses Given**: {total_responses}
"""
        await message.reply_text(stats_message, parse_mode=ParseMode.MARKDOWN)
    
    except Exception as e:
        await message.reply_text(f"**Error:** _{e}_", parse_mode=ParseMode.MARKDOWN)

# AI Sentiment Analysis
@Client.on_message(filters.command(["sentiment"], prefixes=["/", "."]))
async def sentiment_analysis(bot, message):
    global total_queries, total_responses
    
    try:
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        
        if len(message.command) < 2:
            response = "Usage: /sentiment {text}"
            await message.reply_text(response)
            return
        
        text = " ".join(message.command[1:])
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity
        response = f"**Sentiment Polarity**: {sentiment}"
        await message.reply_text(response)
        
        # Log the user interaction
        await send_log(bot, message, text, response)
        total_queries += 1
        total_responses += 1
    
    except Exception as e:
        await message.reply_text(f"**Error:** _{e}_", parse_mode=ParseMode.MARKDOWN)

from textblob import TextBlob

# AI Summarizer
# Summarize function
@Client.on_message(filters.command(["summarize"], prefixes=["/", "."]))
async def summarize_text(bot, message):
    try:
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        
        if len(message.command) < 2:
            await message.reply_text("Usage: /summarize {text}")
            return
        
        # Join the provided text for summarization
        text = " ".join(message.command[1:]).strip()
        
        if not text:
            await message.reply_text("**Error:** _You must provide text to summarize._", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Basic summarization approach: take the first few sentences
        sentences = text.split('. ')
        summary = '. '.join(sentences[:3])  # Summarizing by using the first three sentences

        if not summary:
            summary = "**No summary could be generated. Please provide a longer text.**"
        
        response = f"**Summary**: _{summary}_"
        await message.reply_text(response)
    
    except Exception as e:
        await message.reply_text(f"**Error:** _{e}_", parse_mode=ParseMode.MARKDOWN)

@Client.on_message(filters.command(["qrcode"], prefixes=["/", "."]))
async def generate_qrcode(bot, message):
    try:
        if len(message.command) < 2:
            await message.reply_text("Usage: /qrcode {text/link}")
            return
        
        text = " ".join(message.command[1:])
        img = qrcode.make(text)
        
        bio = BytesIO()
        bio.name = 'qrcode.png'
        img.save(bio, 'PNG')
        bio.seek(0)
        
        await bot.send_photo(message.chat.id, bio, caption=f"**QR code for:** _{text}_")
    
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@Client.on_message(filters.command(["ipinfo"], prefixes=["/", "."]))
async def ip_information(bot, message):
    try:
        if len(message.command) < 2:
            await message.reply_text("Usage: /ipinfo {IP address}")
            return
        
        ip = message.command[1]
        ip_info_url = f"http://ip-api.com/json/{ip}"
        data = requests.get(ip_info_url).json()
        
        if data['status'] == 'fail':
            response = f"Error: {data['message']}"
        else:
            response = f"""
**IP Information:**
- **IP Address**: {data['query']}
- **Country**: {data['country']}
- **Region**: {data['regionName']}
- **City**: {data['city']}
- **ISP**: {data['isp']}
- **Latitude**: {data['lat']}
- **Longitude**: {data['lon']}
"""
        await message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
    
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@Client.on_message(filters.command(["ud"], prefixes=["/", "."]))
async def define_word(bot, message):
    try:
        if len(message.command) < 2:
            await message.reply_text("Usage: /define {word}")
            return
        
        word = message.command[1]
        dictionary_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        data = requests.get(dictionary_url).json()
        
        if "title" in data and data['title'] == "No Definitions Found":
            response = f"No definition found for {word}"
        else:
            definition = data[0]['meanings'][0]['definitions'][0]['definition']
            response = f"**Definition of {word}:**\n{definition}"
        
        await message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
    
    except Exception as e:
        await message.reply_text(f"Error: {e}")
