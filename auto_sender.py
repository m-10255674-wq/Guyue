import os
import asyncio
import pytz
import logging
from telethon import TelegramClient, events
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask
import threading
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sender")  # 直接给一个固定名字

app = Flask(__name__)

@app.route('/')
def home():
    return "Userbot sender is running"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

if not API_ID or not API_HASH or not ADMIN_ID:
    raise ValueError("请在环境变量中设置 API_ID, API_HASH, ADMIN_ID")

TZ = pytz.timezone("Asia/Kuala_Lumpur")
client = TelegramClient("my_session", API_ID, API_HASH)
scheduler = AsyncIOScheduler(timezone=TZ)
current_job_id = None

async def send_scheduled(chat, message):
    try:
        await client.send_message(chat, message)
        logger.info(f"已发送给 {chat}")
    except Exception as e:
        logger.error(f"发送失败: {e}")

def set_daily(hour, minute, chat, message):
    global current_job_id
    if current_job_id:
        scheduler.remove_job(current_job_id)
    job = scheduler.add_job(send_scheduled, "cron", hour=hour, minute=minute, args=[chat, message], id="daily_job")
    current_job_id = job.id

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

@client.on(events.NewMessage(from_users=ADMIN_ID, pattern=r'/cancel'))
async def cancel_cmd(event):
    global current_job_id
    if current_job_id:
        scheduler.remove_job(current_job_id)
        current_job_id = None
        await event.reply("✅ 定时任务已取消")
    else:
        await event.reply("没有任务")

@client.on(events.NewMessage(from_users=ADMIN_ID, pattern=r'/status'))
async def status_cmd(event):
    if current_job_id:
        job = scheduler.get_job(current_job_id)
        if job:
            next_run = job.next_run_time.astimezone(TZ).strftime("%Y-%m-%d %H:%M:%S")
            await event.reply(f"⏰ 定时任务运行中，下次：{next_run}")
    else:
        await event.reply("没有任务")

async def main_telethon():
    await client.start()
    scheduler.start()
    logger.info("定时发送服务已启动")
    await client.run_until_disconnected()

def start_telethon():
    asyncio.run(main_telethon())

if name == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    start_telethon()
