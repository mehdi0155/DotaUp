import os
import json
import random
import string
import telebot
from telebot import types
from flask import Flask, request

# -------------------- Config --------------------

UPLOADER_TOKEN = "7920918778:AAFF4MDkYX4qBpuyXyBgcuCssLa6vjmTN1c"
CHECKER_TOKEN = "7679592392:AAFK0BHxrvxH_I23UGveiVGzc_-M10lPUOA"
CHANNEL = "@hottof"
ADMINS = [6387942633, 5459406429]
CHECKER_BOT_USERNAME = "TofLinkBot"
REQUIRED_CHANNELS = ["@hottof"]
DB_FILE = "db.json"

# -------------------- Shared DB --------------------

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_to_db(link_id, file_id):
    db = load_db()
    db[link_id] = file_id
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

# -------------------- Uploader Bot --------------------

uploader_bot = telebot.TeleBot(UPLOADER_TOKEN)
uploader_data = {}
pending_posts = {}

def is_admin(user_id):
    return user_id in ADMINS

def generate_link_id():
    db = load_db()
    while True:
        link_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        if link_id not in db:
            return link_id

@uploader_bot.message_handler(commands=['start'])
def uploader_start(message):
    if is_admin(message.from_user.id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("آپلود ویدیو"))
        uploader_bot.send_message(message.chat.id, "خوش آمدید.", reply_markup=markup)
    else:
        uploader_bot.send_message(message.chat.id, "دسترسی ندارید.")

@uploader_bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "آپلود ویدیو")
def ask_video(message):
    msg = uploader_bot.send_message(message.chat.id, "ویدیو را ارسال کنید.")
    uploader_bot.register_next_step_handler(msg, receive_video)

def receive_video(message):
    if not message.video:
        uploader_bot.send_message(message.chat.id, "فقط ویدیو بفرستید.")
        return
    uploader_data[message.from_user.id] = {'file_id': message.video.file_id}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("ندارم", callback_data="no_cover"))
    uploader_bot.send_message(message.chat.id, "کاور را ارسال کنید یا روی 'ندارم' کلیک کنید.", reply_markup=markup)
    uploader_bot.register_next_step_handler(message, receive_cover)

@uploader_bot.callback_query_handler(func=lambda c: c.data == "no_cover")
def no_cover(call):
    uploader_bot.answer_callback_query(call.id)
    data = uploader_data.get(call.from_user.id)
    if data:
        data['cover'] = None
        msg = uploader_bot.send_message(call.message.chat.id, "کپشن و توضیح فایل را بفرستید.")
        uploader_bot.register_next_step_handler(msg, receive_caption)

def receive_cover(message):
    if message.photo:
        file_id = message.photo[-1].file_id
        data = uploader_data.get(message.from_user.id)
        if data:
            data['cover'] = file_id
            msg = uploader_bot.send_message(message.chat.id, "کپشن و توضیح فایل را بفرستید.")
            uploader_bot.register_next_step_handler(msg, receive_caption)
    else:
        uploader_bot.send_message(message.chat.id, "فقط عکس بفرست یا روی 'ندارم' کلیک کن.")

def receive_caption(message):
    data = uploader_data.get(message.from_user.id)
    if data:
        data['caption'] = message.text
        preview_post(message)

def preview_post(message):
    data = uploader_data.get(message.from_user.id)
    if data:
        link_id = generate_link_id()
        pending_posts[message.from_user.id] = link_id
        save_to_db(link_id, data['file_id'])
        link = f"https://t.me/{CHECKER_BOT_USERNAME}?start={link_id}"
        caption = f"{data['caption']}\n\n@hottof | تُفِ داغ"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("مشاهده فایل", url=link))
        if data['cover']:
            uploader_bot.send_photo(message.chat.id, data['cover'], caption=caption, reply_markup=markup)
        else:
            uploader_bot.send_message(message.chat.id, caption, reply_markup=markup)
        confirm_markup = types.InlineKeyboardMarkup()
        confirm_markup.add(
            types.InlineKeyboardButton("ارسال در کانال", callback_data="send_now"),
            types.InlineKeyboardButton("لغو ارسال", callback_data="cancel_post")
        )
        uploader_bot.send_message(message.chat.id, "آیا این پست ارسال شود؟", reply_markup=confirm_markup)

@uploader_bot.callback_query_handler(func=lambda call: call.data in ["send_now", "cancel_post"])
def process_confirmation(call):
    uploader_bot.answer_callback_query(call.id)
    if call.data == "send_now":
        data = uploader_data.get(call.from_user.id)
        link_id = pending_posts.get(call.from_user.id)
        if data and link_id:
            link = f"https://t.me/{CHECKER_BOT_USERNAME}?start={link_id}"
            caption = f"{data['caption']}\n\n@hottof | تُفِ داغ"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("مشاهده فایل", url=link))
            if data['cover']:
                uploader_bot.send_photo(CHANNEL, data['cover'], caption=caption, reply_markup=markup)
            else:
                uploader_bot.send_message(CHANNEL, caption, reply_markup=markup)
            uploader_bot.send_message(call.message.chat.id, "پست با موفقیت ارسال شد.")
            del uploader_data[call.from_user.id]
            del pending_posts[call.from_user.id]
    else:
        uploader_data.pop(call.from_user.id, None)
        pending_posts.pop(call.from_user.id, None)
        uploader_bot.send_message(call.message.chat.id, "ارسال لغو شد.")

# -------------------- Checker Bot --------------------

checker_bot = telebot.TeleBot(CHECKER_TOKEN)

def is_member(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            status = checker_bot.get_chat_member(channel, user_id).status
            if status not in ["member", "creator", "administrator"]:
                return False
        except:
            return False
    return True

@checker_bot.message_handler(commands=['start'])
def checker_start(message):
    args = message.text.split()
    if len(args) > 1:
        link_id = args[1]
        if is_member(message.from_user.id):
            send_file(message.chat.id, link_id)
        else:
            send_subscription_prompt(message.chat.id, link_id)
    else:
        checker_bot.send_message(message.chat.id, "به ربات خوش آمدید.")

@checker_bot.callback_query_handler(func=lambda c: c.data.startswith("check_"))
def check_callback(call):
    link_id = call.data.split("_", 1)[1]
    if is_member(call.from_user.id):
        send_file(call.message.chat.id, link_id)
    else:
        send_subscription_prompt(call.message.chat.id, link_id)

def send_subscription_prompt(chat_id, link_id):
    markup = types.InlineKeyboardMarkup()
    for ch in REQUIRED_CHANNELS:
        markup.add(types.InlineKeyboardButton(f"عضویت در {ch}", url=f"https://t.me/{ch[1:]}"))
    markup.add(types.InlineKeyboardButton("بررسی عضویت", callback_data=f"check_{link_id}"))
    checker_bot.send_message(chat_id, "برای دریافت فایل باید عضو کانال شوید.", reply_markup=markup)

def send_file(chat_id, link_id):
    db = load_db()
    file_id = db.get(link_id)
    if file_id:
        checker_bot.send_video(chat_id, file_id, caption="@hottof | تُفِ داغ")
    else:
        checker_bot.send_message(chat_id, "فایل یافت نشد یا حذف شده.")

# -------------------- Flask Server --------------------

app = Flask(__name__)

@app.route(f"/uploader/{UPLOADER_TOKEN}", methods=['POST'])
def webhook_uploader():
    uploader_bot.process_new_updates([types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

@app.route(f"/checker/{CHECKER_TOKEN}", methods=['POST'])
def webhook_checker():
    checker_bot.process_new_updates([types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
