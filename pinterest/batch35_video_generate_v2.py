from pathlib import Path

source_path = Path(__file__).with_name("batch35_video_generate.py")
source = source_path.read_text(encoding="utf-8")

old = """    drawtext = (
        f"drawtext=fontfile={FONT_BOLD}:text='СМОТРЕТЬ ПРОЕКТ  →':"
        "fontcolor=white:fontsize=24:box=1:boxcolor=black@0.38:boxborderw=12:"
        "x='w-tw-28-6*sin(2*PI*t)':y='h-th-34':"
        "alpha='if(lt(t,0.4),t/0.4,if(gt(t,4.6),(5-t)/0.4,1))'"
    )
    return (
        f"zoompan={zoom}:d={FRAME_COUNT}:s=720x1080:fps={FPS},"
        "drawbox=x='-90+(w+180)*t/5':y=0:w=80:h=h:color=white@0.055:t=fill,"
        f"{drawtext},"
        "fade=t=in:st=0:d=0.25,fade=t=out:st=4.55:d=0.45,format=yuv420p"
    )
"""

new = """    drawtext = (
        f"drawtext=fontfile={FONT_BOLD}:text='СМОТРЕТЬ ПРОЕКТ  →':"
        "fontcolor=white:fontsize=24:box=1:boxcolor=black@0.38:boxborderw=12:"
        "x='w-tw-28':y='h-th-34':enable='between(t,0.35,4.65)'"
    )
    return (
        f"zoompan={zoom}:d={FRAME_COUNT}:s=720x1080:fps={FPS},"
        f"{drawtext},"
        "fade=t=in:st=0:d=0.25,fade=t=out:st=4.55:d=0.45,"
        "scale=in_range=pc:out_range=tv,format=yuv420p"
    )
"""

if old not in source:
    raise RuntimeError("Expected FFmpeg filter block was not found")

source = source.replace(old, new, 1)
namespace = {"__name__": "__main__", "__file__": str(source_path)}
exec(compile(source, str(source_path), "exec"), namespace)
