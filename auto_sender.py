import os
import sys
import asyncio
import pytz
import logging
from telethon import TelegramClient, events
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask
import threading

# ====================== 日志 ======================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sender")

# ====================== Flask 保活 ======================
app = Flask(name)

@app.route('/')
def home():
    return "Userbot sender is running"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ====================== 环境变量 ======================
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

print(f"Loaded env: API_ID={API_ID}, API_HASH={'***' if API_HASH else 'MISSING'}, ADMIN_ID={ADMIN_ID}", flush=True)

if not API_ID or not API_HASH or not ADMIN_ID:
    print("ERROR: Missing required environment variables. Exiting.", flush=True)
    sys.exit(1)

TZ = pytz.timezone("Asia/Kuala_Lumpur")
client = TelegramClient("my_session", API_ID, API_HASH)
scheduler = AsyncIOScheduler(timezone=TZ)
current_job_id = None

# ====================== 广告文案 ======================
AD_CAPTION = """╭━━━━━━━━━━━╮
🔥 HOK白菜价代打 🔥
╰━━━━━━━━━━━╯

😵‍💫 还在为冲不上分而烦恼吗❓
🐷 还在被猪队友拖累吗❓

🏆 多次巅峰榜前10上榜 · 超高胜率实力打手
⚡ 快速冲分 · 稳定发挥 · 高效率完成

👑 想拥有属于自己的国标吗❓
🚀 想快速突破段位吗❓
🔥 那就来找我❗

━━━━━━━━━━━━━━
👑 【冲星价格】 👑
🔥 王者 0–100星
💰 RM1 / ⭐

💎 星耀段位
⭐ 星耀一颗：RM0.50
⭐ 星耀以下：RM0.40

🔥 王者 1–50星只需 RM50 ❗❓

━━━━━━━━━━━━━━
🏅 【国标价格】 🏅
🎯 指定英雄小国标
💰 RM25

🔥 指定热门英雄小国标
💰 RM35

👑 指定英雄大国标
💰 RM50

⚔️ 指定热门英雄大国标
💰 RM70
━━━━━━━━━━━━━━
🎮 【服务方式】

🤝 陪玩上分 · 一起冲刺
⚡ 上号代打 · 快速完成

🏆 专业实力 · 高效冲分
🔥 超值价格 · 实力在线 · 高效冲分！ 🔥
━━━━━━━━━━━━━━

📩 下单机器人：@guyuehok_bot"""

# ====================== 定时发送函数 ======================
async def send_scheduled(chat, message):
    try:
        await client.send_message(chat, message, parse_mode='markdown')
        logger.info(f"已发送给 {chat}")
    except Exception as e:
        logger.error(f"发送失败: {e}")

def set_daily(hour, minute, chat, message):
    global current_job_id
    if current_job_id:
        scheduler.remove_job(current_job_id)
    job = scheduler.add_job(send_scheduled, "cron", hour=hour, minute=minute, args=[chat, message], id="daily_job")
    current_job_id = job.id

# ====================== 命令处理 ======================
@client.on(events.NewMessage(from_users=ADMIN_ID, pattern=r'/schedule\s+(\d{1,2}:\d{2})\s+(\S+)\s+(.+)'))
async def set_schedule(event):
    time_str = event.pattern_match.group(1)
    chat_str = event.pattern_match.group(2)
    message = event.pattern_match.group(3)
    try:
        hour, minute = map(int, time_str.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59): raise ValueError
    except:
        await event.reply("❌ 时间格式错误，请使用 HH:MM")
        return
    try:
        entity = await client.get_entity(chat_str)
    except Exception as e:
        await event.reply(f"❌ 找不到用户: {e}")
        return
    set_daily(hour, minute, entity, message)
    await event.reply(f"✅ 定时任务已设置：每天 {time_str} 发给 {chat_str}\n内容：{message}")

@client.on(events.NewMessage(from_users=ADMIN_ID, pattern=r'/ad_photo\s+(\d{1,2}:\d{2})\s+(\S+)\s+(.+)'))
async def set_ad_photo(event):
    time_str = event.pattern_match.group(1)
    chat_str = event.pattern_match.group(2)
    photos_str = event.pattern_match.group(3)

    try:
        hour, minute = map(int, time_str.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59): raise ValueError
    except:
        await event.reply("❌ 时间格式错误，请使用 HH:MM")
        return
    try:
        entity = await client.get_entity(chat_str)
    except Exception as e:
        await event.reply(f"❌ 找不到用户 {chat_str}: {e}")
        return

    photo_list = [p.strip() for p in photos_str.split(',') if p.strip()]
    if not photo_list:
        await event.reply("❌ 至少需要一张图片")
        return
