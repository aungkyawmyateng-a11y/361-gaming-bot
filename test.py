import os
import json
import time
import html
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
import telebot
from telebot import types

API_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 5023802528))


KPAY_NAME = os.environ.get('KPAY_NAME', "U Wunna Phone Khaing")
KPAY_PHONE = os.environ.get('KPAY_PHONE', "09778867878")
KBZPAY_QR_URL = os.environ.get('KBZPAY_QR_URL', "https://i.ibb.co/mVv8xQYd/qr.jpg")


PRICING = {
    "PS4 Slim": 7000,
    "Xbox": 7000,
    "PS5 Slim": 12000,
    "VIP - PS5 Pro": 20000
}

bot = telebot.TeleBot(API_TOKEN)

STATUS_FILE = "seats_status.json"

DEFAULT_SEATS = {
    "Station (1) [PS4 Slim]": {"available": True, "custom_info": None},
    "Station (2) [PS4 Slim]": {"available": True, "custom_info": None},
    "Station (3) [PS4 Slim]": {"available": True, "custom_info": None},
    "Station (4) [PS4 Slim]": {"available": True, "custom_info": None},
    "Station (5) [PS4 Slim]": {"available": True, "custom_info": None},
    "Station (6) [Xbox]": {"available": True, "custom_info": None},
    "Station (7) [PS5 Slim]": {"available": True, "custom_info": None},
    "Station (8) [PS5 Slim]": {"available": True, "custom_info": None},
    "Station (9) [PS5 Slim]": {"available": True, "custom_info": None},
    "Station (10) [VIP - PS5 Pro]": {"available": True, "custom_info": None}
}

def load_seats():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {STATUS_FILE}: {e}")
    return DEFAULT_SEATS.copy()

def save_seats():
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(seats_status, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving {STATUS_FILE}: {e}")

seats_status = load_seats()

user_sessions = {}      
pending_bookings = {}   
user_languages = {}

def get_lang(user_id):
    return user_languages.get(user_id, "mm")

def is_session_valid(user_id):
    if user_id not in user_sessions:
        return False
    if "timestamp" in user_sessions[user_id]:
        if time.time() - user_sessions[user_id]["timestamp"] > 600: 
            del user_sessions[user_id]
            return False
    user_sessions[user_id]["timestamp"] = time.time()
    return True


def calculate_time_range(arrival_str, hours_str):
    if "Now" in arrival_str or "အခု" in arrival_str:
        start_dt = datetime.now()
    else:
        try:
            start_dt = datetime.strptime(arrival_str, "%I:%M %p")
        except Exception:
            return arrival_str

    if hours_str == "Open" or "Open" in str(hours_str) or "စမှတ်" in str(hours_str):
        return f"{start_dt.strftime('%I:%M %p')} မှ စတင်၍"
    else:
        try:
            hrs = int(''.join(filter(str.isdigit, str(hours_str))))
            end_dt = start_dt + timedelta(hours=hrs)
            return f"{start_dt.strftime('%I:%M %p')} မှ {end_dt.strftime('%I:%M %p')} အထိ"
        except Exception:
            return f"{start_dt.strftime('%I:%M %p')} ({hours_str})"

def get_main_keyboard(user_id, lang_code):
    ln = LANGUAGES.get(lang_code, LANGUAGES["mm"])
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    markup.add(types.KeyboardButton(ln["btn_status"]), types.KeyboardButton(ln["btn_booking"]))
    markup.add(types.KeyboardButton(ln["btn_menu"]), types.KeyboardButton(ln["btn_games"]))
    markup.add(types.KeyboardButton(ln["btn_location"]), types.KeyboardButton(ln["btn_rules"]))
    markup.add(types.KeyboardButton(ln["btn_promo_event"]), types.KeyboardButton(ln["btn_contact"]))
    markup.add(types.KeyboardButton(ln["btn_lang"]))
    
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("⚙️ Admin Panel"))
    return markup


LANGUAGES = {
    "mm": {
        "welcome": "🎮 361° Gaming Lounge မှ ကြိုဆိုပါသည်! လိုအပ်သည့် ဝန်ဆောင်မှုကို ရွေးချယ်ပါ။",
        "btn_status": "🕹️ Station များကြည့်ရန်",
        "btn_booking": "📅 ဘွတ်ကင်လုပ်ရန်",
        "btn_menu": "🍔 Snacks and Drinks",
        "btn_games": "🎮 Game စာရင်းကြည့်ရန်",
        "btn_location": "📍 ဆိုင်တည်နေရာ",
        "btn_rules": "🔥 ဆိုင်တွင်းစည်းကမ်းများ",
        "btn_promo_event": "🎉 Promotions and Events",
        "btn_contact": "📱 ဆိုင်ရှင်အားဆက်သွယ်ရန်",
        "btn_lang": "🌐 Language / ဘာသာစကား / 语言",
        
        "status_title": "<b>🎮 Station ၁၀ ခု၏ လက်ရှိ Live အခြေအနေများ</b>\n\n",
        "seat_available": "🟢 စက်အားနေပါသည်",
        "seat_busy": "🔴 မအားသေးပါ",
        "seat_booked_prefix": "🔴 ဘွတ်ကင်အတည်ပြုထားပါသည်: ",
        "select_seat": "📅 ဘွတ်ကင်လုပ်လိုသည့် Station ကို ရွေးချယ်ပေးပါ -",
        "all_full": "❌ စိတ်မကောင်းပါဘူးခင်ဗျာ၊ လောလောဆယ် Station အားလုံး ပြည့်နေပါသည်။",
        "select_time_mode": "⏰ <b>{seat}</b> ၏ အားမည့်အချိန်အခြေအနေ:\n📌 <i>{info}</i>\n\nဆိုင်ကို ဘယ်အချိန် လာရောက်ကစားမှာလဲခင်ဗျာ?",
        "btn_now": "⚡ အခုချက်ချင်းလာမည် (Now)",
        "btn_choose_time": "⏰ အချိန်ရွေးချယ်မည် (Select Time)",
        "time_picker_title": "⏰ <b>လာမည့်အချိန်ကို Alarm ကဲ့သို့ ရွေးချယ်ပါ-</b>\n\n[ + ] နှင့် [ - ] ခလုတ်များကို နှိပ်၍ ပြင်ဆင်ပြီးပါက Confirm နှိပ်ပါ၊",
        "seat_selected": "🕹️ {seat}\n💰 ဈေးနှုန်း: {price} ကျပ်/နာရီ\n⏰ လာမည့်အချိန်: {time}\n\n<b>ဘယ်နှစ်နာရီကြာ</b> ကစားမှာလဲခင်ဗျာ?",
        "hour_suffix": " နာရီ", "start_match": "စမှတ် (Open)",
        "pay_option_title": "💳 ငွေပေးချေမှု ပုံစံကို ရွေးချယ်ပေးပါ -",
        "btn_pay_now": "💸 စရံငွေ (30%) ကြိုလွှဲမည်", "btn_pay_later": "🏪 ဆိုင်ရောက်မှ ရှင်းမည်",
        "req_phone": "📱 ဆိုင်မှ ဆက်သွယ်ရန် ဖုန်းနံပါတ် ပေးပို့ပေးပါ -",
        "btn_phone": "📱 ဖုန်းနံပါတ်ပေးရန်",
        "payment_title": "💸 <b>စရံငွေ (30%) လွှဲရန် အချက်အလက်များ</b>\n\nကျသင့်ငွေ စုစုပေါင်း: <b>{amount} ကျပ်</b>\n⚡ ပေးချေရမည့် စရံငွေ (30%): <b>{deposit} ကျပ်</b>\n\n👤 KPay Name: <b>{name}</b>\n📞 KPay Phone: <code>{phone}</code>\n\nQR Scanning သို့မဟုတ် ဖုန်းနံပါတ်သို့ <b>{deposit} ကျပ်</b> လွှဲပြီးပါက ငွေလွှဲဖြတ်ပိုင်း Screenshot ပို့ပေးပါ။",
        "sent_to_admin": "⏳ သင့်ဘွတ်ကင် တောင်းဆိုချက်ကို ဆိုင်ရှင်ထံ ပို့လိုက်ပါပြီ။ ဆိုင်ရှင်မှ စက်အား/မအား စစ်ဆေးပြီးပါက အကြောင်းပြန်ပေးပါမည်။",
        "booking_success": "🎉 ဘွတ်ကင် အတည်ဖြစ်ပါပြီ!\n\nဆိုင်မှ သင့်ရဲ့ ဘွတ်ကင် ({seat} | အချိန်: {arrival}) ကို အတည်ပြုလိုက်ပါပြီ။",
        "booking_rejected": "❌ စိတ်မကောင်းပါဘူးခင်ဗျာ၊ သင့်ရဲ့ ဘွတ်ကင် ({seat}) ချိန်ထားသည့်အချိန်တွင် စက်မအားသေးပါသဖြင့် ငြင်းပယ်လိုက်ရပါသည်။",
        "session_expired": "⚠️ အချိန်ကြာသွားသဖြင့် ဘွတ်ကင်လုပ်ငန်းစဉ် ပြတ်တောက်သွားပါသည်။ ကျေးဇူးပြု၍ အစမှ ပြန်လည်ရွေးချယ်ပေးပါ။",
        
        "msg_menu": (
            "<b>🍔 361° Snacks and Drinks Menu</b>\n\n"
            "🍿 <b>Snacks (အကြော်အလှော်များ)</b>\n"
            "• အာလူးချောင်းကြော် (French Fries) - ၅,၀၀၀ ကျပ်\n\n"
            "🍜 <b>ခေါက်ဆွဲများ (ကြက်ဥပါပြီး)</b>\n"
            "• YumYum ချဉ်စပ် - ၄,၀၀၀ ကျပ်\n"
            "• MAMA မျက်လုံး - ၄,၀၀၀ ကျပ်\n"
            "• YumYum Spicy သုပ် - ၅,၀၀၀ ကျပ်\n\n"
            "🍃 <b>လက်ဖက်သုပ်များ</b>\n"
            "• အကြော်+လက်ဖက် ပလိန်းသုပ် - ၅,၀၀၀ ကျပ်\n"
            "• ခရမ်းချဉ်သီး + ဂေါ်ဖီပါ လက်ဖက်သုပ် - ၆,၀၀၀ ကျပ်\n\n"
            "🥤 <b>အအေးနှင့် သောက်စရာများ</b>\n"
            "• Monster Energy Drink (Ultra White) - ၁၃,၀၀၀ ကျပ်\n"
            "• Monster Energy Drink (Original Black) - ၁၃,၀၀၀ ကျပ်\n"
            "• Monster Energy Drink (Pink) - ၁၃,၀၀၀ ကျပ်\n"
            "• Red Bull အပြာ - ၁၂,၀၀၀ ကျပ်\n"
            "• Coca-Cola - ၃,၀၀၀ ကျပ်\n"
            "• Sponsor - ၃,၀၀၀ ကျပ်\n"
            "• Red Bull အဝါ - ၃,၀၀၀ ကျပ်\n"
            "• Bing Hong Cha (Lemon Tea) - ၃,၀၀၀ ကျပ်\n"
            "• ရေသန့် - ၁,၀၀၀ ကျပ်"
        ),
        "msg_games": (
            "<b>🎮 361° Available Games List</b>\n\n"
            "⚽ <b>Sports & Fighting:</b>\n"
            "• EA Sports FC 26\n• NBA 2K26\n• WWE 2K26\n• UFC 6\n• Tekken 8\n• Sifu\n\n"
            "🔫 <b>Action, Adventure & RPG:</b>\n"
            "• Grand Theft Auto V (GTA V)\n• Red Dead Redemption II\n• God of War Ragnarök\n"
            "• Black Myth: Wukong\n• Marvel's Spider-Man 2\n• Ghost of Yōtei\n• Ghost of Tsushima\n"
            "• Elden Ring\n• Hogwarts Legacy\n• Cyberpunk 2077\n• The Last of Us Part II Remastered\n"
            "• Resident Evil 4\n• Resident Evil 9\n• Silent Hill f\n• Stellar Blade\n• Control\n"
            "• Call of Duty: Modern Warfare II\n• Crimson Desert\n• 007 First Light\n• Mafia: The Old Country\n\n"
            "👥 <b>Co-Op / Multiplayers & Fun Games:</b>\n"
            "• It Takes Two\n• A Way Out\n• Split Fiction\n• Astro Bot\n• Stray\n• Reanimal\n"
            "• LEGO Batman: Legacy of the Dark Knight"
        ),
        "msg_location": (
            "<b>📍 361° Gaming Lounge တည်နေရာ</b>\n\n"
            "🗺️ Google Maps Link တိုက်ရိုက်ကြည့်ရန်:\n"
            "https://maps.app.goo.gl/tpp8zCzhjBUacbZS8?g_st=ac"
        ),
        "msg_rules": (
            "<b>🔥 361° ဆိုင်တွင်း စည်းကမ်းချက်များ</b>\n\n"
            "🚬 <b>၁။</b> ဆိုင်အတွင်း ဆေးလိပ်သောက်သုံးနိုင်သော်လည်း ဆိုဖာများပေါ် ပြာမကျစေရန်နှင့် မလောင်ကျွမ်းစေရန် အထူးသတိပြုရမည်။\n"
            "🍃 <b>၂။</b> ကွမ်းဝါးသူများအနေဖြင့် ကွမ်းတံတွေးကို စည်းကမ်းရှိစွာ သေချာထွေးပေးရမည်။\n"
            "🎮 <b>၃။</b> Game Controller နှင့် ဆိုင်အတွင်း စက်ပစ္စည်းများ ပျက်စီး/ပျောက်ဆုံးပါက <b>ကာလပေါက်ဈေးအတိုင်း လျှော်ကြေးပေးလျော်ရမည်။</b>\n"
            "⏰ <b>၄။</b> ဘွတ်ကင်ချိန်ထက် ၁၅ မိနစ် နောက်ကျပါက ဘွတ်ကင်အား အလိုအလျောက် ပယ်ဖျက်မည်။"
        ),
        "msg_promo_event": (
            "<b>🎉 PROMOTIONS and EVENTS 🏆</b>\n\n"
            "🔥 <b>1+1 Special Promotion (Buy 1 Hour, Get 1 Hour FREE!)</b>\n"
            "📅 ကာလ: 20.10.2026 မှ 31.10.2026 အထိ (လကုန်အထိ)\n\n"
            "🏆 <b>361° Gaming Lounge E-Sports Tournament</b>\n"
            "⏳ Status: <i>Coming Soon! (မကြာမီ လာမည်)</i>"
        ),
        "msg_contact": f"<b>📱 ဆိုင်ရှင်အား တိုက်ရိုက်ဆက်သွယ်ရန်</b>\n\n👤 အမည်: <b>{KPAY_NAME}</b>\n📞 ဖုန်းနံပါတ်: <b>{KPAY_PHONE}</b>\n💬 Telegram သို့မဟုတ် ဖုန်းဖြင့် တိုက်ရိုက်ဆက်သွယ်နိုင်ပါသည်။"
    },
    "en": {
        "welcome": "🎮 Welcome to 361° Gaming Lounge! Please choose a service.",
        "btn_status": "🕹️ View Stations", "btn_booking": "📅 Book a Station",
        "btn_menu": "🍔 Snacks and Drinks", "btn_games": "🎮 Game List",
        "btn_location": "📍 Location", "btn_rules": "🔥 Shop Rules",
        "btn_promo_event": "🎉 Promotions and Events", "btn_contact": "📱 Contact Owner",
        "btn_lang": "🌐 Language / ဘာသာစကား / 语言",
        "status_title": "<b>🎮 Live Status of 10 Stations</b>\n\n",
        "seat_available": "🟢 Available",
        "seat_busy": "🔴 Occupied / Busy",
        "seat_booked_prefix": "🔴 Booked for: ",
        "select_seat": "📅 Please select the station you want to book:",
        "all_full": "❌ Sorry, all stations are currently full.",
        "select_time_mode": "⏰ Availability for <b>{seat}</b>:\n📌 <i>{info}</i>\n\nWhen will you arrive at the shop?",
        "btn_now": "⚡ Arrive Now",
        "btn_choose_time": "⏰ Select Specific Time",
        "time_picker_title": "⏰ <b>Select Arrival Time (Alarm Style):</b>\n\nUse [ + ] and [ - ] buttons to adjust, then click Confirm.",
        "seat_selected": "🕹️ {seat}\n💰 Price: {price} MMK/Hour\n⏰ Arrival Time: {time}\n\n<b>How many hours</b> would you like to play?",
        "hour_suffix": " Hour(s)", "start_match": "Open Match",
        "pay_option_title": "💳 Select Payment Option:",
        "btn_pay_now": "💸 Pay 30% Deposit Now", "btn_pay_later": "🏪 Pay at Counter",
        "req_phone": "📱 Please send your phone number -",
        "btn_phone": "📱 Share Phone Number",
        "payment_title": "💸 <b>Deposit Payment Details (30%)</b>\n\nTotal Price: <b>{amount} MMK</b>\n⚡ Required Deposit (30%): <b>{deposit} MMK</b>\n\n👤 KPay Name: <b>{name}</b>\n📞 KPay Phone: <code>{phone}</code>\n\nPlease transfer <b>{deposit} MMK</b> via QR/Phone and send Screenshot.",
        "sent_to_admin": "⏳ Your booking request has been sent to the owner for review.",
        "booking_success": "🎉 Booking Confirmed!\n\n({seat} | Time: {arrival})",
        "booking_rejected": "❌ Sorry, your booking request for {seat} has been declined.",
        "session_expired": "⚠️ Session expired. Please start your booking again.",
        "msg_menu": (
            "<b>🍔 361° Snacks and Drinks Menu</b>\n\n"
            "🍿 <b>Snacks</b>\n• French Fries - 5,000 MMK\n\n"
            "🍜 <b>Instant Noodles (Egg Included)</b>\n"
            "• YumYum Spicy Sour - 4,000 MMK\n• MAMA Myet Long - 4,000 MMK\n• YumYum Spicy Salad - 5,000 MMK\n\n"
            "🍃 <b>Tea Leaf Salads</b>\n"
            "• Plain Fried Tea Leaf Salad - 5,000 MMK\n• Tomato & Cabbage Tea Leaf Salad - 6,000 MMK\n\n"
            "🥤 <b>Drinks & Beverages</b>\n"
            "• Monster Energy Drink (Ultra White) - 13,000 MMK\n• Monster Energy Drink (Original Black) - 13,000 MMK\n"
            "• Monster Energy Drink (Pink) - 13,000 MMK\n• Red Bull Blue - 12,000 MMK\n• Coca-Cola - 3,000 MMK\n"
            "• Sponsor - 3,000 MMK\n• Red Bull Yellow - 3,000 MMK\n• Bing Hong Cha (Lemon Tea) - 3,000 MMK\n• Purified Water - 1,000 MMK"
        ),
        "msg_games": (
            "<b>🎮 361° Available Games List</b>\n\n"
            "⚽ <b>Sports & Fighting:</b>\n"
            "• EA Sports FC 26\n• NBA 2K26\n• WWE 2K26\n• UFC 6\n• Tekken 8\n• Sifu\n\n"
            "🔫 <b>Action, Adventure & RPG:</b>\n"
            "• Grand Theft Auto V (GTA V)\n• Red Dead Redemption II\n• God of War Ragnarök\n"
            "• Black Myth: Wukong\n• Marvel's Spider-Man 2\n• Ghost of Yōtei\n• Ghost of Tsushima\n"
            "• Elden Ring\n• Hogwarts Legacy\n• Cyberpunk 2077\n• The Last of Us Part II Remastered\n"
            "• Resident Evil 4\n• Resident Evil 9\n• Silent Hill f\n• Stellar Blade\n• Control\n"
            "• Call of Duty: Modern Warfare II\n• Crimson Desert\n• 007 First Light\n• Mafia: The Old Country\n\n"
            "👥 <b>Co-Op / Multiplayers & Fun Games:</b>\n"
            "• It Takes Two\n• A Way Out\n• Split Fiction\n• Astro Bot\n• Stray\n• Reanimal\n"
            "• LEGO Batman: Legacy of the Dark Knight"
        ),
        "msg_location": (
            "<b>📍 361° Gaming Lounge Location</b>\n\n"
            "🗺️ Direct Google Maps Link:\n"
            "https://maps.app.goo.gl/tpp8zCzhjBUacbZS8?g_st=ac"
        ),
        "msg_rules": (
            "<b>🔥 361° Basic Shop Rules</b>\n\n"
            "1. Smoking allowed, but refrain from dropping ash on sofas.\n"
            "2. Proper disposal of betel nut waste.\n"
            "3. Damaged equipment must be compensated at market value.\n"
            "4. Bookings automatically canceled after 15 mins late."
        ),
        "msg_promo_event": (
            "<b>🎉 PROMOTIONS and EVENTS 🏆</b>\n\n"
            "🔥 <b>1+1 Special Promotion (Buy 1 Hour Get 1 Hour Free)</b>\n"
            "📅 Date: 20.10.2026 to 31.10.2026\n\n"
            "🏆 <b>361° E-Sports Tournament</b>\n"
            "⏳ Status: <i>Coming Soon!</i>"
        ),
        "msg_contact": f"<b>📱 Contact Shop Owner</b>\n\n👤 Name: <b>{KPAY_NAME}</b>\n📞 Phone: <b>{KPAY_PHONE}</b>"
    },
    "zh": {
        "welcome": "🎮 欢迎光临 361° Gaming Lounge！请选择您需要的服务。",
        "btn_status": "🕹️ 查看所有座位", "btn_booking": "📅 预约座位",
        "btn_menu": "🍔 小吃与饮品", "btn_games": "🎮 游戏列表",
        "btn_location": "📍 店铺位置", "btn_rules": "🔥 店内规则",
        "btn_promo_event": "🎉 优惠与比赛", "btn_contact": "📱 联系老板",
        "btn_lang": "🌐 Language / ဘာသာစကား / 语言",
        "status_title": "<b>🎮 10个座位的实时状态</b>\n\n",
        "seat_available": "🟢 空闲中",
        "seat_busy": "🔴 使用中 / 暂无空位",
        "seat_booked_prefix": "🔴 已被预约: ",
        "select_seat": "📅 请选择您要预约的座位号：",
        "all_full": "❌ 抱歉，目前所有座位已满。",
        "select_time_mode": "⏰ <b>{seat}</b> 的空闲状态:\n📌 <i>{info}</i>\n\n请问您预计什么时间到店？",
        "btn_now": "⚡ 现在就去 (Now)",
        "btn_choose_time": "⏰ 自定义时间 (Select Time)",
        "time_picker_title": "⏰ <b>请选择到店时间 (闹钟模式):</b>\n\n点击 [ + ] 或 [ - ] 按钮进行调节，调整后点击确认。",
        "seat_selected": "🕹️ {seat}\n💰 价格: {price} 缅币/小时\n⏰ 到店时间: {time}\n\n<b>请问您想玩几个小时？</b>",
        "hour_suffix": " 小时", "start_match": "开台/不限时",
        "pay_option_title": "💳 请选择支付方式：",
        "btn_pay_now": "💸 支付 30% 定金", "btn_pay_later": "🏪 到店现金/转账",
        "req_phone": "📱 请发送您的手机号码：",
        "btn_phone": "📱 发送手机号码",
        "payment_title": "💸 <b>定金支付信息 (30%)</b>\n\n总金额: <b>{amount} 缅币</b>\n⚡ 应付定金 (30%): <b>{deposit} 缅币</b>\n\n👤 KPay 姓名: <b>{name}</b>\n📞 KPay 账号: <code>{phone}</code>\n\n请转账 <b>{deposit} 缅币</b> 并发送截图。",
        "sent_to_admin": "⏳ 您的预约申请已发送给老板审核。",
        "booking_success": "🎉 预约成功！\n\n（{seat} | 时间: {arrival}）",
        "booking_rejected": "❌ 抱歉，本店暂时拒绝了您对 {seat} 的预约申请。",
        "session_expired": "⚠️ 会话已过期，请重新开始预约。",
        "msg_menu": (
            "<b>🍔 361° 小吃与饮品菜单</b>\n\n"
            "🍿 <b>小吃</b>\n• 炸薯条 (French Fries) - 5,000 缅币\n\n"
            "🍜 <b>方便面类（含鸡蛋）</b>\n"
            "• YumYum 酸辣面 - 4,000 缅币\n• MAMA 眼睛面 - 4,000 缅币\n• YumYum 凉拌面 - 5,000 缅币\n\n"
            "🍃 <b>凉拌茶叶</b>\n"
            "• 原味炸豆凉拌茶叶 - 5,000 缅币\n• 番茄甘蓝凉拌茶叶 - 6,000 缅币\n\n"
            "🥤 <b>饮品类</b>\n"
            "• Monster 能量饮料 (Ultra White) - 13,000 缅币\n• Monster 能量饮料 (Original Black) - 13,000 缅币\n"
            "• Monster 能量饮料 (Pink) - 13,000 缅币\n• 蓝罐红牛 (Red Bull Blue) - 12,000 缅币\n• 可口可乐 (Coca-Cola) - 3,000 缅币\n"
            "• Sponsor 运动饮料 - 3,000 缅币\n• 黄罐红牛 (Red Bull Yellow) - 3,000 缅币\n• 冰红茶 (Lemon Tea) - 3,000 缅币\n• 矿泉水 - 1,000 缅币"
        ),
        "msg_games": (
            "<b>🎮 361° 现有游戏列表</b>\n\n"
            "⚽ <b>体育与格斗类:</b>\n"
            "• EA Sports FC 26\n• NBA 2K26\n• WWE 2K26\n• UFC 6\n• 铁拳 8 (Tekken 8)\n• 师父 (Sifu)\n\n"
            "🔫 <b>动作、冒险与角色扮演类:</b>\n"
            "• 侠盗猎车手 V (GTA V)\n• 荒野大镖客：救赎 2 (Red Dead Redemption II)\n• 战神：诸神黄昏 (God of War Ragnarök)\n"
            "• 黑神话：悟空 (Black Myth: Wukong)\n• 蜘蛛侠 2 (Marvel's Spider-Man 2)\n• 羊蹄山之魂 (Ghost of Yōtei)\n"
            "• 对马岛之魂 (Ghost of Tsushima)\n• 艾尔登法环 (Elden Ring)\n• 霍格沃茨之遗 (Hogwarts Legacy)\n"
            "• 赛博朋克 2077 (Cyberpunk 2077)\n• 最后生还者 第二部 复刻版 (TLOU Part II)\n• 生化危机 4 (Resident Evil 4)\n"
            "• 生化危机 9 (Resident Evil 9)\n• 寂静岭 f (Silent Hill f)\n• 剑星 (Stellar Blade)\n• 控制 (Control)\n"
            "• 使命召唤：现代战争 II\n• 红色沙漠 (Crimson Desert)\n• 007 初露锋芒 (007 First Light)\n• 四海兄弟：故乡 (Mafia: The Old Country)\n\n"
            "👥 <b>双人合作与休闲游戏:</b>\n"
            "• 双人成行 (It Takes Two)\n• 逃出生天 (A Way Out)\n• 拆弹专家 (Split Fiction)\n• 宇宙机器人 (Astro Bot)\n"
            "• 流浪 (Stray)\n• 兽性大发 (Reanimal)\n• 乐高蝙蝠侠"
        ),
        "msg_location": (
            "<b>📍 361° Gaming Lounge 店铺地址</b>\n\n"
            "🗺️ Google 地图直达链接:\n"
            "https://maps.app.goo.gl/tpp8zCzhjBUacbZS8?g_st=ac"
        ),
        "msg_rules": (
            "<b>🔥 361° 店内基本规则</b>\n\n"
            "1. 允许吸烟，但请注意不要将烟灰掉落到沙发上。\n"
            "2. 吐槟榔汁请保持卫生。\n"
            "3. 损坏设备需按市场价赔偿。\n"
            "4. 迟到15分钟预约自动取消。"
        ),
        "msg_promo_event": (
            "<b>🎉 优惠活动与比赛 🏆</b>\n\n"
            "🔥 <b>1+1 买一送一 (买1小时送1小时)</b>\n"
            "📅 活动时间: 2026年10月20日 至 10月31日\n\n"
            "🏆 <b>361° 电子竞技比赛</b>\n"
            "⏳ 状态: <i>Coming Soon! (敬请期待)</i>"
        ),
        "msg_contact": f"<b>📱 联系老板</b>\n\n👤 姓名: <b>{KPAY_NAME}</b>\n📞 电话: <b>{KPAY_PHONE}</b>"
    }
}

def get_station_info_text(seat_name, lang_code):
    ln = LANGUAGES.get(lang_code, LANGUAGES["mm"])
    seat = seats_status.get(seat_name, {"available": True, "custom_info": None})
    
    if seat["custom_info"]:
        return f"{ln['seat_booked_prefix']}{seat['custom_info']}"
    elif seat["available"]:
        return ln["seat_available"]
    else:
        return ln["seat_busy"]


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    if user_id in user_sessions:
        del user_sessions[user_id]
    show_language_options(message.chat.id)

def show_language_options(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🇲🇲 မြန်မာ", callback_data="setlang_mm"), 
        types.InlineKeyboardButton("🇬🇧 English", callback_data="setlang_en"),
        types.InlineKeyboardButton("🇨🇳 中文", callback_data="setlang_zh")
    )
    bot.send_message(chat_id, "Please select language / ဘာသာစကားရွေးချယ်ပါ / 请选择语言 :", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('setlang_'))
def handle_set_language(call):
    lang_code = call.data.split('_')[1]
    user_id = call.from_user.id
    user_languages[user_id] = lang_code
    
    bot.answer_callback_query(call.id, text="Language updated!")
    markup = get_main_keyboard(user_id, lang_code)
    bot.send_message(call.message.chat.id, LANGUAGES[lang_code]["welcome"], reply_markup=markup)


@bot.message_handler(content_types=['text'])
def handle_text_messages(message):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    ln = LANGUAGES.get(lang, LANGUAGES["mm"])
    text = message.text

    all_status_btns = [LANGUAGES[l]["btn_status"] for l in LANGUAGES]
    all_booking_btns = [LANGUAGES[l]["btn_booking"] for l in LANGUAGES]
    all_menu_btns = [LANGUAGES[l]["btn_menu"] for l in LANGUAGES]
    all_games_btns = [LANGUAGES[l]["btn_games"] for l in LANGUAGES]
    all_location_btns = [LANGUAGES[l]["btn_location"] for l in LANGUAGES]
    all_rules_btns = [LANGUAGES[l]["btn_rules"] for l in LANGUAGES]
    all_promo_btns = [LANGUAGES[l]["btn_promo_event"] for l in LANGUAGES]
    all_contact_btns = [LANGUAGES[l]["btn_contact"] for l in LANGUAGES]
    all_lang_btns = [LANGUAGES[l]["btn_lang"] for l in LANGUAGES]

    if text in all_status_btns:
        status_text = ln["status_title"]
        for seat in seats_status.keys():
            info = get_station_info_text(seat, lang)
            status_text += f"• <b>{seat}</b>\n  └ {info}\n\n"
        bot.send_message(message.chat.id, status_text, parse_mode="HTML")
        
    elif text in all_booking_btns:
        user_sessions[user_id] = {"lang": lang, "timestamp": time.time(), "chat_id": message.chat.id, "state": "booking"}
        markup = types.InlineKeyboardMarkup(row_width=1)
        has_available_seat = False
        for seat, data in seats_status.items():
            if data["available"]:
                markup.add(types.InlineKeyboardButton(text=f"🟢 {seat}", callback_data=f"b_seat_{seat}"))
                has_available_seat = True
        if has_available_seat:
            bot.send_message(message.chat.id, ln["select_seat"], reply_markup=markup)
        else:
            bot.send_message(message.chat.id, ln["all_full"])
            
    elif text in all_menu_btns: bot.send_message(message.chat.id, ln["msg_menu"], parse_mode="HTML")
    elif text in all_games_btns: bot.send_message(message.chat.id, ln["msg_games"], parse_mode="HTML")
    elif text in all_location_btns: bot.send_message(message.chat.id, ln["msg_location"], parse_mode="HTML")
    elif text in all_rules_btns: bot.send_message(message.chat.id, ln["msg_rules"], parse_mode="HTML")
    elif text in all_promo_btns: bot.send_message(message.chat.id, ln["msg_promo_event"], parse_mode="HTML")
    elif text in all_contact_btns: bot.send_message(message.chat.id, ln["msg_contact"], parse_mode="HTML")
    elif text in all_lang_btns: show_language_options(message.chat.id)
    elif text == "⚙️ Admin Panel" and user_id == ADMIN_ID: admin_command(message)



def get_time_picker_keyboard(h, m, p):
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("🔺 +1 Hr", callback_data=f"tp_hup_{h}_{m}_{p}"),
        types.InlineKeyboardButton("🔺 +5 Min", callback_data=f"tp_mup_{h}_{m}_{p}"),
        types.InlineKeyboardButton("🔺 AM/PM", callback_data=f"tp_pup_{h}_{m}_{p}")
    )
    markup.add(
        types.InlineKeyboardButton(f"⏰ {h:02d}", callback_data="tp_none"),
        types.InlineKeyboardButton(f"{m:02d}", callback_data="tp_none"),
        types.InlineKeyboardButton(p, callback_data="tp_none")
    )
    markup.add(
        types.InlineKeyboardButton("🔻 -1 Hr", callback_data=f"tp_hdn_{h}_{m}_{p}"),
        types.InlineKeyboardButton("🔻 -5 Min", callback_data=f"tp_mdn_{h}_{m}_{p}"),
        types.InlineKeyboardButton("🔻 AM/PM", callback_data=f"tp_pdn_{h}_{m}_{p}")
    )
    markup.add(types.InlineKeyboardButton("✅ Confirm Time", callback_data=f"tp_confirm_{h}_{m}_{p}"))
    return markup


@bot.callback_query_handler(func=lambda call: call.data.startswith('b_seat_'))
def handle_seat_selection(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    lang = get_lang(user_id)
    ln = LANGUAGES[lang]
    
    if not is_session_valid(user_id):
        bot.send_message(call.message.chat.id, ln["session_expired"])
        return
    
    seat_name = call.data.replace('b_seat_', '')
    user_sessions[user_id]["seat"] = seat_name
    seat_info = get_station_info_text(seat_name, lang)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(ln["btn_now"], callback_data="time_now"),
        types.InlineKeyboardButton(ln["btn_choose_time"], callback_data="time_custom")
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id, 
        text=ln["select_time_mode"].format(seat=seat_name, info=seat_info),
        parse_mode="HTML",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('time_'))
def handle_time_mode(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    lang = get_lang(user_id)
    ln = LANGUAGES[lang]
    
    if not is_session_valid(user_id):
        bot.send_message(call.message.chat.id, ln["session_expired"])
        return

    mode = call.data.split('_')[1]
    if mode == "now":
        user_sessions[user_id]["arrival_time"] = datetime.now().strftime("%I:%M %p")
        ask_hours_step(call.message, user_id)
    else:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id, 
            text=ln["time_picker_title"],
            parse_mode="HTML",
            reply_markup=get_time_picker_keyboard(10, 0, "AM")
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith('tp_'))
def handle_time_picker_clicks(call):
    bot.answer_callback_query(call.id)
    if call.data == "tp_none":
        return
        
    user_id = call.from_user.id
    lang = get_lang(user_id)
    ln = LANGUAGES[lang]
    
    if not is_session_valid(user_id):
        bot.send_message(call.message.chat.id, ln["session_expired"])
        return
    
    parts = call.data.split('_')
    action = parts[1]
    h, m, p = int(parts[2]), int(parts[3]), parts[4]
    
    if action == "confirm":
        user_sessions[user_id]["arrival_time"] = f"{h:02d}:{m:02d} {p}"
        ask_hours_step(call.message, user_id)
        return
        
    if action == "hup": h = 1 if h == 12 else h + 1
    elif action == "hdn": h = 12 if h == 1 else h - 1
    elif action == "mup": m = 0 if m == 55 else m + 5
    elif action == "mdn": m = 55 if m == 0 else m - 5
    elif action in ["pup", "pdn"]: p = "PM" if p == "AM" else "AM"
        
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text=ln["time_picker_title"], 
            parse_mode="HTML", 
            reply_markup=get_time_picker_keyboard(h, m, p)
        )
    except Exception:
        pass


def get_seat_price(seat_name):
    if "VIP" in seat_name: return PRICING["VIP - PS5 Pro"]
    elif "PS5 Slim" in seat_name: return PRICING["PS5 Slim"]
    elif "Xbox" in seat_name: return PRICING["Xbox"]
    return PRICING["PS4 Slim"]


def ask_hours_step(message, user_id):
    ln = LANGUAGES[user_sessions[user_id]["lang"]]
    seat_name = user_sessions[user_id]["seat"]
    arrival_time = user_sessions[user_id]["arrival_time"]
    price_per_hour = get_seat_price(seat_name)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(f"1{ln['hour_suffix']}", callback_data="b_hr_1"),
        types.InlineKeyboardButton(f"2{ln['hour_suffix']}", callback_data="b_hr_2"),
        types.InlineKeyboardButton(f"3{ln['hour_suffix']}", callback_data="b_hr_3"),
        types.InlineKeyboardButton(ln["start_match"], callback_data="b_hr_Open")
    )
    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message.message_id, 
        text=ln["seat_selected"].format(seat=seat_name, price=f"{price_per_hour:,}", time=arrival_time),
        parse_mode="HTML",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('b_hr_'))
def handle_hour_selection(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    lang = get_lang(user_id)
    ln = LANGUAGES[lang]
    
    if not is_session_valid(user_id):
        bot.send_message(call.message.chat.id, ln["session_expired"])
        return
    
    hours = call.data.split('_')[2]
    seat_name = user_sessions[user_id]["seat"]
    price_per_hour = get_seat_price(seat_name)
    
    hour_int = 1 if hours == "Open" else int(hours)
    total_price = price_per_hour * hour_int
    deposit_price = int(total_price * 0.30) # 30% Deposit
    
    time_range_text = calculate_time_range(user_sessions[user_id]["arrival_time"], hours)
    
    user_sessions[user_id]["hours"] = hours if hours == "Open" else f"{hours}{ln['hour_suffix']}"
    user_sessions[user_id]["time_range"] = time_range_text
    user_sessions[user_id]["amount"] = total_price
    user_sessions[user_id]["deposit"] = deposit_price
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(ln["btn_pay_now"], callback_data="b_pay_now"),
        types.InlineKeyboardButton(ln["btn_pay_later"], callback_data="b_pay_later")
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=ln["pay_option_title"],
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('b_pay_'))
def handle_payment_choice(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    lang = get_lang(user_id)
    ln = LANGUAGES[lang]
    
    if not is_session_valid(user_id):
        bot.send_message(call.message.chat.id, ln["session_expired"])
        return
    
    choice = call.data.split('_')[2]
    user_sessions[user_id]["pay_choice"] = choice
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton(ln["btn_phone"], request_contact=True))
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
        
    msg = bot.send_message(call.message.chat.id, ln["req_phone"], reply_markup=markup)
    bot.register_next_step_handler(msg, handle_phone_final)


def handle_phone_final(message):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    ln = LANGUAGES[lang]
    
    if not is_session_valid(user_id):
        bot.send_message(message.chat.id, ln["session_expired"], reply_markup=get_main_keyboard(user_id, lang))
        return
    
    if message.contact is not None:
        phone = message.contact.phone_number
    elif message.text is not None:
        if message.text == "/start":
            send_welcome(message)
            return
        phone = message.text.strip()
    else:
        msg = bot.send_message(message.chat.id, ln["req_phone"])
        bot.register_next_step_handler(msg, handle_phone_final)
        return
        
    user_sessions[user_id]["phone"] = phone
    
    if user_sessions[user_id]["pay_choice"] == "now":
        amount_str = f"{user_sessions[user_id]['amount']:,}"
        deposit_str = f"{user_sessions[user_id]['deposit']:,}"
        caption_txt = ln["payment_title"].format(amount=amount_str, deposit=deposit_str, name=KPAY_NAME, phone=KPAY_PHONE)
        
        try:
            bot.send_photo(message.chat.id, KBZPAY_QR_URL, caption=caption_txt, parse_mode="HTML")
        except Exception as e:
            print(f"Photo Error: {e}")
            bot.send_message(message.chat.id, caption_txt, parse_mode="HTML")
    else:
        user_sessions[user_id]["photo_id"] = None
        send_booking_to_admin(user_id)


@bot.message_handler(content_types=['photo'])
def handle_incoming_photo(message):
    user_id = message.from_user.id
    if user_id in user_sessions and user_sessions[user_id].get("pay_choice") == "now":
        user_sessions[user_id]["photo_id"] = message.photo[-1].file_id
        send_booking_to_admin(user_id)


def send_booking_to_admin(user_id):
    if user_id not in user_sessions:
        return
        
    booking_data = user_sessions.pop(user_id)
    pending_bookings[user_id] = booking_data
    
    lang = booking_data["lang"]
    try:
        cust_name = html.escape(str(bot.get_chat(user_id).first_name or "Customer"))
    except Exception:
        cust_name = "Customer"
        
    seat = booking_data["seat"]
    time_range = booking_data["time_range"]
    hours = booking_data["hours"]
    phone = html.escape(str(booking_data["phone"]))
    
    if booking_data["pay_choice"] == "now":
        pay_type = f"စရံ 30% ({booking_data['deposit']:,} ကျပ်) လွှဲထားပြီး"
    else:
        pay_type = "ဆိုင်ရောက်မှရှင်းမည်"
    
    bot.clear_step_handler_by_chat_id(chat_id=user_id)
    bot.send_message(user_id, LANGUAGES[lang]["sent_to_admin"], reply_markup=get_main_keyboard(user_id, lang))
    
    markup_admin = types.InlineKeyboardMarkup()
    markup_admin.add(
        types.InlineKeyboardButton("✅ Accept & Confirm", callback_data=f"adm_yes_{user_id}"), 
        types.InlineKeyboardButton("❌ Reject & Refund", callback_data=f"adm_no_{user_id}")
    )
    
    admin_text = (
        f"🔔 <b>ဘွတ်ကင်အသစ် တောင်းဆိုချက်!</b>\n\n"
        f"👤 အမည်: {cust_name}\n"
        f"🕹️ Station: <b>{seat}</b>\n"
        f"⏰ အချိန်အပိုင်းအခြား: <b>{time_range}</b>\n"
        f"⏳ ကြာမြင့်ချိန်: {hours}\n"
        f"💰 ကျသင့်ငွေ စုစုပေါင်း: {booking_data['amount']:,} ကျပ်\n"
        f"📱 ဖုန်းနံပါတ်: <code>{phone}</code>\n"
        f"💳 ငွေပေးချေမှု: <b>{pay_type}</b>"
    )
    
    try:
        if booking_data.get("photo_id"):
            bot.send_photo(ADMIN_ID, booking_data["photo_id"], caption=admin_text, reply_markup=markup_admin, parse_mode="HTML")
        else:
            bot.send_message(ADMIN_ID, admin_text, reply_markup=markup_admin, parse_mode="HTML")
    except Exception as e:
        print(f"Error sending to admin: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_'))
def handle_admin_confirmation(call):
    if call.from_user.id != ADMIN_ID:
        return
    parts = call.data.split('_')
    action = parts[1]
    target_user_id = int(parts[2])
    
    bot.answer_callback_query(call.id)
    if target_user_id not in pending_bookings: 
        bot.send_message(ADMIN_ID, "⚠️ ဤဘွတ်ကင်ကို အတည်ပြု/ငြင်းပယ် ပြီးသွားပါပြီ (သို့မဟုတ်) ဒေတာမရှိတော့ပါ။")
        return
        
    info = pending_bookings.pop(target_user_id)
    cust_ln = LANGUAGES.get(info.get("lang", "mm"), LANGUAGES["mm"])
    
    if action == "yes":
        seats_status[info["seat"]]["available"] = False
        seats_status[info["seat"]]["custom_info"] = f"{info['time_range']}"
        save_seats()
        
        msg_text = f"🟢 လက်ခံပြီးပါပြီ! {info['seat']} ၏ အခြေအနေအား အပ်ဒိတ်လုပ်လိုက်သည်။"
        bot.send_message(info["chat_id"], cust_ln["booking_success"].format(seat=info["seat"], arrival=info["time_range"]))
    else:
        msg_text = "❌ ငြင်းပယ်လိုက်ပါပြီ!"
        bot.send_message(info["chat_id"], cust_ln["booking_rejected"].format(seat=info["seat"]))
        
    bot.send_message(ADMIN_ID, msg_text)


def admin_command(message):
    markup = types.InlineKeyboardMarkup()
    for seat, data in seats_status.items():
        status_text = "🟢 လွတ်" if data["available"] else "🔴 မလွတ်"
        markup.add(types.InlineKeyboardButton(text=f"{seat}: {status_text}", callback_data=f"p_tgl_{seat}"))
    bot.send_message(ADMIN_ID, "⚙️ Admin Panel - စက်အခြေအနေ ပြောင်းလဲရန် နှိပ်ပါ", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('p_tgl_'))
def handle_panel_toggle(call):
    if call.from_user.id != ADMIN_ID:
        return
    seat_name = call.data.replace('p_tgl_', '')
    
    seats_status[seat_name]["available"] = not seats_status[seat_name]["available"]
    seats_status[seat_name]["custom_info"] = None
    save_seats()
        
    bot.answer_callback_query(call.id, text=f"{seat_name} Status ပြောင်းလဲပြီးပါပြီ")
    
    try:
        markup = types.InlineKeyboardMarkup()
        for seat, data in seats_status.items():
            status_text = "🟢 လွတ်" if data["available"] else "🔴 မလွတ်"
            markup.add(types.InlineKeyboardButton(text=f"{seat}: {status_text}", callback_data=f"p_tgl_{seat}"))
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    except Exception:
        pass



app = Flask(__name__)

@app.route('/')
def home():
    return "361° Gaming Lounge Bot is Alive and Running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_web, daemon=True)
    t.start()



if __name__ == "__main__":
    print("361° GAMING LOUNGE Bot Status Check Initiated...")
    keep_alive()
    try:
        bot.remove_webhook()
    except Exception:
        pass
    bot.infinity_polling(none_stop=True, timeout=60, long_polling_timeout=60)