import os
import asyncio
from datetime import datetime
from telethon import TelegramClient, events
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

# ====================== 配置（环境变量） ======================
API_ID = int(os.environ.get("API_ID", "123456"))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))  # 你的个人账号数字ID（发给 @userinfobot 获得）
TZ = pytz.timezone("Asia/Kuala_Lumpur")          # 马来西亚时区

# ====================== 初始化客户端 ======================
client = TelegramClient("my_account", API_ID, API_HASH)
scheduler = AsyncIOScheduler(timezone=TZ)
current_job_id = None

# ====================== 定时任务管理 ======================
async def send_scheduled_message(chat, message):
    try:
        await client.send_message(chat, message)
        print(f"[{datetime.now(TZ).strftime('%H:%M')}] 已发送给 {chat}")
    except Exception as e:
        print(f"发送失败：{e}")

def schedule_daily(hour: int, minute: int, chat, message):
    global current_job_id
    # 先移除旧任务
    if current_job_id:
        scheduler.remove_job(current_job_id)
    job = scheduler.add_job(
        send_scheduled_message,
        "cron",
        hour=hour,
        minute=minute,
        args=[chat, message],
        id="daily_job"
    )
    current_job_id = job.id
    return job

# ====================== 命令处理 ======================
@client.on(events.NewMessage(from_users=ADMIN_ID, pattern=r'/schedule\s+(\d{1,2}:\d{2})\s+(\S+)\s+(.+)'))
async def set_schedule(event):
    time_str = event.pattern_match.group(1)
    chat_str = event.pattern_match.group(2)
    message = event.pattern_match.group(3)

    try:
        hour, minute = map(int, time_str.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except:
        await event.reply("❌ 时间格式错误，请使用 HH:MM（如 09:00）")
        return

    # 尝试将 chat 解析为实体（@username 或 手机号）
    try:
        entity = await client.get_entity(chat_str)
    except Exception as e:
        await event.reply(f"❌ 无法找到用户 {chat_str}：{e}")
        return

    schedule_daily(hour, minute, entity, message)
    await event.reply(f"✅ 已设置每天 {time_str} 向 {chat_str} 发送：\n{message}")

@client.on(events.NewMessage(from_users=ADMIN_ID, pattern=r'/cancel'))
async def cancel_schedule(event):
    global current_job_id
    if current_job_id:
        scheduler.remove_job(current_job_id)
        current_job_id = None
        await event.reply("❌ 定时任务已取消")
    else:
        await event.reply("没有正在运行的定时任务")

@client.on(events.NewMessage(from_users=ADMIN_ID, pattern=r'/status'))
async def job_status(event):
    if current_job_id:
        job = scheduler.get_job(current_job_id)
        if job:
            next_time = job.next_run_time.astimezone(TZ).strftime("%Y-%m-%d %H:%M:%S")
            await event.reply(f"⏰ 定时任务运行中\n下次发送时间：{next_time}")
        else:
            await event.reply("没有定时任务")
    else:
        await event.reply("没有定时任务")

# ====================== 启动 ======================
async def main():
    await client.start()
    print("✅ 账号已登录")
    scheduler.start()
    print("定时器已启动，等待命令...")
    await client.run_until_disconnected()

if name == "main":
    asyncio.run(main())
