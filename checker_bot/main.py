import telebot
import os
import json
from flask import Flask, request

TOKEN = "7679592392:AAFK0BHxrvxH_I23UGveiVGzc_-M10lPUOA"
REQUIRED_CHANNELS = ["@hottof"]
DB_FILE = "db.json"

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def is_member(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'creator', 'administrator']:
                return False
        except:
            return False
    return True

@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    if len(args) > 1:
        link_id = args[1]
        if is_member(message.from_user.id):
            send_file(message, link_id)
        else:
            send_subscription_prompt(message, link_id)
    else:
        bot.send_message(message.chat.id, "برای مشاهده فایل باید از طریق لینک وارد شوید.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("check_"))
def check_subscription(call):
    link_id = call.data.split("_")[1]
    if is_member(call.from_user.id):
        send_file(call.message, link_id)
    else:
        send_subscription_prompt(call.message, link_id)

def send_subscription_prompt(message, link_id):
    markup = telebot.types.InlineKeyboardMarkup()
    for ch in REQUIRED_CHANNELS:
        markup.add(telebot.types.InlineKeyboardButton(f"عضویت در {ch}", url=f"https://t.me/{ch[1:]}"))
    markup.add(telebot.types.InlineKeyboardButton("بررسی عضویت", callback_data=f"check_{link_id}"))
    bot.send_message(message.chat.id, "برای دریافت فایل عضو شوید:", reply_markup=markup)

def send_file(message, link_id):
    db = load_db()
    file_id = db.get(link_id)
    if not file_id:
        bot.send_message(message.chat.id, "فایل یافت نشد.")
        return
    bot.send_video(message.chat.id, file_id, caption="@hottof | تُفِ داغ")

@server.route("/checker/" + TOKEN, methods=["POST"])
def webhook():
    bot.process_new_updates([
        telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    ])
    return "OK", 200
