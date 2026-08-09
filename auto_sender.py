async def send_ad_photos():
        try:
            await client.send_file(entity, photo_list, caption=AD_CAPTION, parse_mode='markdown')
            logger.info(f"广告相册已发送给 {chat_str}")
        except Exception as e:
            logger.error(f"发送广告相册失败: {e}")

    global current_job_id
    if current_job_id:
        scheduler.remove_job(current_job_id)
    job = scheduler.add_job(send_ad_photos, "cron", hour=hour, minute=minute, id="ad_photo_job")
    current_job_id = job.id
    await event.reply(f"✅ 多图广告定时已设置：每天 {time_str} 发给 {chat_str}\n图片：{', '.join(photo_list)}")

@client.on(events.NewMessage(from_users=ADMIN_ID, pattern=r'/cancel'))
async def cancel_cmd(event):
    global current_job_id
    if current_job_id:
        scheduler.remove_job(current_job_id)
        current_job_id = None
        await event.reply("✅ 定时任务已取消")
    else:
        await event.reply("没有正在运行的定时任务")

@client.on(events.NewMessage(from_users=ADMIN_ID, pattern=r'/status'))
async def status_cmd(event):
    if current_job_id:
        job = scheduler.get_job(current_job_id)
        if job:
            next_run = job.next_run_time.astimezone(TZ).strftime("%Y-%m-%d %H:%M:%S")
            await event.reply(f"⏰ 定时任务运行中，下次发送：{next_run}")
    else:
        await event.reply("⏸️ 没有定时任务")

# ====================== 启动 ======================
async def main_telethon():
    await client.start()
    scheduler.start()
    logger.info("定时发送服务已启动")
    await client.run_until_disconnected()

def start_telethon():
    asyncio.run(main_telethon())

if name == "main":
    threading.Thread(target=run_flask, daemon=True).start()
    start_telethon()
