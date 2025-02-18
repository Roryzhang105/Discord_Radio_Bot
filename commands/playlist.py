import discord
from discord.ext import commands
from discord import app_commands
from db import add_station, delete_station, get_playlist, set_current_index, get_default_volume, set_default_volume
from music import auto_adjust_volume
from views import RadioControlView, StationSelectView

class PlaylistCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="play", description="播放指定电台流（名称和 URL），并存入播放列表")
    async def play(self, interaction: discord.Interaction, name: str, url: str):
        index = add_station(name, url)
        set_current_index(index)
        if not interaction.guild.voice_client:
            if interaction.user.voice and interaction.user.voice.channel:
                await interaction.user.voice.channel.connect()
            else:
                await interaction.response.send_message("你没有在语音频道中哦！")
                return
        vc = interaction.guild.voice_client
        if vc.is_playing():
            vc.stop()
        factor = auto_adjust_volume(url)
        final_volume = get_default_volume() * factor
        source = discord.FFmpegPCMAudio(url, **{
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        })
        vc.play(discord.PCMVolumeTransformer(source, volume=final_volume))
        view = RadioControlView()
        await interaction.response.send_message(f"正在播放：{name} ({url})\n当前音量: {final_volume:.2f}", view=view)

    @app_commands.command(name="add_station", description="手动添加一个电台到播放列表")
    async def add_station_cmd(self, interaction: discord.Interaction, name: str, url: str):
        add_station(name, url)
        playlist = get_playlist()
        await interaction.response.send_message(f"已添加电台：{name} ({url})。播放列表共 {len(playlist)} 个电台。", ephemeral=True)

    @app_commands.command(name="delete_station", description="删除播放列表中的电台")
    async def delete_station_cmd(self, interaction: discord.Interaction, url: str):
        if delete_station(url):
            await interaction.response.send_message(f"已删除电台：{url}", ephemeral=True)
        else:
            await interaction.response.send_message("未找到该电台。", ephemeral=True)

    @app_commands.command(name="set_volume", description="设置默认音量，范围 0 到 100")
    async def set_volume(self, interaction: discord.Interaction, level: int):
        if level < 0 or level > 100:
            await interaction.response.send_message("请输入 0 到 100 的音量值。", ephemeral=True)
            return
        vol = level / 100.0
        set_default_volume(vol)
        await interaction.response.send_message(f"默认音量已设置为 {level}%。", ephemeral=True)

    @app_commands.command(name="select", description="通过下拉菜单选择播放已存储的电台")
    async def select(self, interaction: discord.Interaction):
        view = StationSelectView()
        await interaction.response.send_message("请选择要播放的电台：", view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(PlaylistCog(bot))
