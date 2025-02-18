import discord
from discord import ui
import math
import time
from db import get_playlist, get_current_index, set_current_index, get_default_volume
from music import auto_adjust_volume

# 全局变量，用于记录各个 guild 的播放状态
PLAYBACK_START_TIMES = {}  # {guild_id: start_time}
PLAYBACK_MESSAGES = {}     # {guild_id: message}
PLAYBACK_INFO = {}         # {guild_id: (name, final_volume)}

def volume_to_db(volume: float) -> float:
    """将音量（0~1）转换为分贝值"""
    if volume <= 0:
        return -float('inf')
    return 20 * math.log10(volume)

def format_elapsed(elapsed: int) -> str:
    """将秒数格式化为 mm:ss 格式"""
    minutes = elapsed // 60
    seconds = elapsed % 60
    return f"{minutes:02d}:{seconds:02d}"

def create_radio_embed(name: str, final_volume: float, guild_id: int) -> discord.Embed:
    """创建展示当前播放电台信息的 Embed"""
    db_value = volume_to_db(final_volume)
    start_time = PLAYBACK_START_TIMES.get(guild_id, time.time())
    elapsed = int(time.time() - start_time)
    embed = discord.Embed(
        title="当前播放",
        description=f"【{name}】",
        color=discord.Color.blurple()
    )
    embed.add_field(name="播放时长", value=format_elapsed(elapsed), inline=True)
    embed.add_field(name="音量调整", value=f"约降低 {abs(db_value):.1f} dB", inline=True)
    return embed

class StationSelect(discord.ui.Select):
    def __init__(self):
        playlist = get_playlist()
        options = []
        for record in playlist:
            options.append(
                discord.SelectOption(
                    label=record['name'],
                    value=str(record['id']),
                    description="点击播放此电台"
                )
            )
        super().__init__(placeholder="请选择要播放的电台", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        selected_id = int(self.values[0])
        playlist = get_playlist()
        for idx, record in enumerate(playlist):
            if record['id'] == selected_id:
                url = record['url']
                name = record['name']
                set_current_index(idx)
                vc = interaction.guild.voice_client
                if not vc:
                    if interaction.user.voice and interaction.user.voice.channel:
                        vc = await interaction.user.voice.channel.connect()
                    else:
                        await interaction.followup.send("请先加入语音频道。", ephemeral=True)
                        return
                if vc.is_playing():
                    vc.stop()
                # 记录播放开始时间
                PLAYBACK_START_TIMES[interaction.guild.id] = time.time()
                factor = auto_adjust_volume(url)
                final_volume = get_default_volume() * factor
                source = discord.FFmpegPCMAudio(
                    url,
                    **{'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
                )
                vc.play(discord.PCMVolumeTransformer(source, volume=final_volume))
                PLAYBACK_INFO[interaction.guild.id] = (name, final_volume)
                view = RadioControlView()
                # 更新原始回复，显示 Embed 和控制面板
                await interaction.edit_original_response(embed=create_radio_embed(name, final_volume, interaction.guild.id), view=view)
                return
        await interaction.followup.send("未找到对应的电台。", ephemeral=True)

class StationSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StationSelect())

class RadioControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⏮️ 上一个电台", style=discord.ButtonStyle.secondary, custom_id="prev_station", row=0)
    async def prev_station(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        playlist = get_playlist()
        if not playlist:
            await interaction.edit_original_response(content="播放列表为空。", embed=None, view=None)
            return
        current_index = get_current_index()
        new_index = current_index - 1 if current_index > 0 else len(playlist) - 1
        set_current_index(new_index)
        record = playlist[new_index]
        url = record['url']
        name = record['name']
        vc = interaction.guild.voice_client
        if not vc:
            if interaction.user.voice and interaction.user.voice.channel:
                vc = await interaction.user.voice.channel.connect()
            else:
                await interaction.edit_original_response(content="请先加入语音频道。", embed=None, view=None)
                return
        if vc.is_playing():
            vc.stop()
        PLAYBACK_START_TIMES[interaction.guild.id] = time.time()
        factor = auto_adjust_volume(url)
        final_volume = get_default_volume() * factor
        source = discord.FFmpegPCMAudio(
            url,
            **{'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        )
        vc.play(discord.PCMVolumeTransformer(source, volume=final_volume))
        PLAYBACK_INFO[interaction.guild.id] = (name, final_volume)
        embed = create_radio_embed(name, final_volume, interaction.guild.id)
        view = RadioControlView()
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(label="⏯️ 播放/停止", style=discord.ButtonStyle.success, custom_id="play_stop", row=0)
    async def play_stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        vc = interaction.guild.voice_client
        if not vc:
            if interaction.user.voice and interaction.user.voice.channel:
                vc = await interaction.user.voice.channel.connect()
            else:
                await interaction.edit_original_response(content="请先加入语音频道。", embed=None, view=None)
                return
        if vc.is_playing():
            vc.stop()
            await interaction.edit_original_response(content="播放已暂停。", embed=None, view=RadioControlView())
        else:
            playlist = get_playlist()
            if not playlist:
                await interaction.edit_original_response(content="播放列表为空。", embed=None, view=None)
                return
            current_index = get_current_index()
            record = playlist[current_index]
            url = record['url']
            name = record['name']
            PLAYBACK_START_TIMES[interaction.guild.id] = time.time()
            factor = auto_adjust_volume(url)
            final_volume = get_default_volume() * factor
            source = discord.FFmpegPCMAudio(
                url,
                **{'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
            )
            vc.play(discord.PCMVolumeTransformer(source, volume=final_volume))
            PLAYBACK_INFO[interaction.guild.id] = (name, final_volume)
            embed = create_radio_embed(name, final_volume, interaction.guild.id)
            await interaction.edit_original_response(embed=embed, view=RadioControlView())

    @discord.ui.button(label="⏭️ 下一个电台", style=discord.ButtonStyle.secondary, custom_id="next_station", row=0)
    async def next_station(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        playlist = get_playlist()
        if not playlist:
            await interaction.edit_original_response(content="播放列表为空。", embed=None, view=None)
            return
        current_index = get_current_index()
        new_index = (current_index + 1) % len(playlist)
        set_current_index(new_index)
        record = playlist[new_index]
        url = record['url']
        name = record['name']
        vc = interaction.guild.voice_client
        if not vc:
            if interaction.user.voice and interaction.user.voice.channel:
                vc = await interaction.user.voice.channel.connect()
            else:
                await interaction.edit_original_response(content="请先加入语音频道。", embed=None, view=None)
                return
        if vc.is_playing():
            vc.stop()
        PLAYBACK_START_TIMES[interaction.guild.id] = time.time()
        factor = auto_adjust_volume(url)
        final_volume = get_default_volume() * factor
        source = discord.FFmpegPCMAudio(
            url,
            **{'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        )
        vc.play(discord.PCMVolumeTransformer(source, volume=final_volume))
        PLAYBACK_INFO[interaction.guild.id] = (name, final_volume)
        embed = create_radio_embed(name, final_volume, interaction.guild.id)
        view = RadioControlView()
        await interaction.edit_original_response(embed=embed, view=view)
