import discord
from discord.ext import commands
from discord import app_commands

class BasicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="join", description="加入你所在的语音频道")
    async def join(self, interaction: discord.Interaction):
        if interaction.user.voice and interaction.user.voice.channel:
            channel = interaction.user.voice.channel
            await channel.connect()
            await interaction.response.send_message(f"已加入 {channel.mention}")
        else:
            await interaction.response.send_message("你没有在语音频道中哦！", ephemeral=True)

    @app_commands.command(name="leave", description="离开当前语音频道")
    async def leave(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("已离开语音频道。")
        else:
            await interaction.response.send_message("我当前不在语音频道中。", ephemeral=True)

    @app_commands.command(name="stop", description="停止播放当前音频")
    async def stop(self, interaction: discord.Interaction):
        if not interaction.guild.voice_client:
            await interaction.response.send_message("我没有在语音频道中哦！")
            return
        vc = interaction.guild.voice_client
        if vc.is_playing():
            vc.stop()
            await interaction.response.send_message("已停止播放。")
        else:
            await interaction.response.send_message("当前没有正在播放的音频。")

async def setup(bot: commands.Bot):
    await bot.add_cog(BasicCog(bot))
