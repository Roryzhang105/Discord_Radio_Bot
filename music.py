import subprocess
import re

def auto_adjust_volume(url: str, duration: int = 10, target_db: float = -10.0) -> float:
    """
    使用 ffmpeg 的 volumedetect 滤镜检测音频流的平均音量，
    返回一个调整因子，使得最终音量接近 target_db。
    """
    cmd = [
        "ffmpeg",
        "-i", url,
        "-t", str(duration),
        "-af", "volumedetect",
        "-f", "null",
        "-"
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = proc.stderr
        match = re.search(r"mean_volume:\s*(-?\d+(\.\d+)?) dB", output)
        if match:
            mean_db = float(match.group(1))
            factor = 10 ** ((target_db - mean_db) / 20)
            factor = max(0.1, min(3.0, factor))
            return factor
    except Exception as e:
        print("auto_adjust_volume error:", e)
    return 1.0
