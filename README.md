Discord Radio Bot
一个基于 discord.py 2.x 开发的 Discord 机器人，可播放电台流并自动调节音量，同时支持嵌入式消息展示当前播放信息和实时控制操作（上一个、播放/停止、下一个）。
本项目采用模块化设计，分为数据库操作、音频处理、UI 组件和命令扩展等部分。

项目结构
bash
复制
your_project/
├── bot.py           # 主入口，初始化 Bot、加载扩展及后台任务
├── db.py            # 数据库操作模块，用于存储播放列表和设置
├── music.py         # 音频处理模块，实现自动音量均衡等功能
├── views.py         # UI 组件模块，包含嵌入式消息、下拉菜单、播放控制面板等
└── commands/        
    ├── __init__.py  # 空文件，标识 commands 包
    ├── basic.py     # 基本语音命令（join, leave, stop）
    └── playlist.py  # 播放列表管理命令（play, add_station, delete_station, set_volume, select）
环境要求
Python 3.8 或更高版本
discord.py 2.x
PyNaCl
FFmpeg（请确保 FFmpeg 已安装并在系统 PATH 中可调用）
安装依赖
在项目目录下执行以下命令安装必要的依赖：

bash
复制
pip install -U discord.py PyNaCl
另外，请安装 FFmpeg（例如，在 Ubuntu 上执行 sudo apt install ffmpeg）。

配置
设置环境变量 DISCORD_TOKEN，将其值设置为你的 Discord Bot Token。例如，在 Linux 或 macOS 下：

bash
复制
export DISCORD_TOKEN="your_bot_token_here"
或者在 Windows 命令提示符下：

bash
复制
set DISCORD_TOKEN=your_bot_token_here
运行
在项目根目录下运行：

bash
复制
python bot.py
如果需要后台运行，可以使用 tmux 创建一个新会话并运行 Bot，详细步骤参考 tmux 使用指南。

功能说明
播放电台
使用 /play 命令输入电台名称和音频流 URL，机器人将播放该电台，并自动存入播放列表。

播放列表管理

使用 /add_station 命令手动添加电台
使用 /delete_station 命令删除播放列表中的电台
使用 /select 命令通过下拉菜单选择播放已存电台
播放控制面板
嵌入式消息（Embed）展示当前播放的电台信息，包括播放时长（每分钟更新）、音量调整情况（以分贝显示），并提供上一个、播放/停止、下一个按钮供实时控制。

自动音量均衡
使用 FFmpeg 的 volumedetect 滤镜检测流媒体的平均音量，并自动计算调整因子，使不同电台的输出音量尽量一致。

自动断线
当语音频道内连续 5 分钟无人时，机器人会自动断开连接。
