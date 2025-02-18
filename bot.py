import os
import discord
from discord.ext import commands, tasks
import asyncio

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    raise RuntimeError("请设置环境变量 DISCORD_TOKEN")

class MyBot(commands.Bot):
    async def setup_hook(self):
        # 加载扩展（Cog 模块）
        await self.load_extension("commands.basic")
        await self.load_extension("commands.playlist")
        await self.tree.sync()
        print("Cogs loaded and command tree synced.")

intents = discord.Intents.all()
bot = MyBot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} is now online!')
    update_embeds.start()  # 启动后台任务

# 后台任务：每 60 秒更新一次当前播放状态 Embed 消息
from views import PLAYBACK_MESSAGES, PLAYBACK_INFO, create_radio_embed

@tasks.loop(seconds=60)
async def update_embeds():
    for guild_id, message in list(PLAYBACK_MESSAGES.items()):
        guild = bot.get_guild(guild_id)
        if not guild:
            continue
        vc = guild.voice_client
        # 如果语音连接存在且正在播放，并且有播放信息
        if vc and vc.is_playing() and guild_id in PLAYBACK_INFO:
            name, final_volume = PLAYBACK_INFO[guild_id]
            new_embed = create_radio_embed(name, final_volume, guild_id)
            try:
                await message.edit(embed=new_embed)
            except Exception as e:
                print("更新 Embed 失败：", e)

bot.run(DISCORD_TOKEN)
