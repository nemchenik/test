from __future__ import annotations

import ast
import base64
import gzip
from pathlib import Path

bootstrap_path = Path(__file__).with_name("batch36_house_plan_facade_video_bootstrap.py")
bootstrap_source = bootstrap_path.read_text(encoding="utf-8")
tree = ast.parse(bootstrap_source, filename=str(bootstrap_path))

payload = None
for node in tree.body:
    if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "PAYLOAD" for target in node.targets
    ):
        payload = ast.literal_eval(node.value)
        break

if not isinstance(payload, str):
    raise RuntimeError("PAYLOAD was not found in batch36 bootstrap")

source = gzip.decompress(base64.b64decode(payload)).decode("utf-8")

old_inputs = '''        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(static_card),
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(plan_slide),
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(facade_slide),
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(static_card),
'''
new_inputs = '''        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(static_card),
        "-i", str(plan_slide),
        "-i", str(facade_slide),
        "-i", str(static_card),
'''
old_map = '''        "-map", "[outv]", "-an",
'''
new_map = '''        "-map", "[outv]", "-t", "6.65", "-an",
'''

if old_inputs not in source:
    raise RuntimeError("Expected looping image input block was not found")
if old_map not in source:
    raise RuntimeError("Expected output map block was not found")

source = source.replace(old_inputs, new_inputs, 1).replace(old_map, new_map, 1)
virtual_path = Path(__file__).with_name("batch36_house_plan_facade_video.py")
namespace = {"__name__": "__main__", "__file__": str(virtual_path)}
exec(compile(source, str(virtual_path), "exec"), namespace)
