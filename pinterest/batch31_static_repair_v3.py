from pathlib import Path

source_path = Path(__file__).with_name("batch31_static_repair_v2.py")
source = source_path.read_text(encoding="utf-8")
old = "data = b28.fetch_bytes(record.image_url)"
new = "data = v3.fetch_bytes(record.image_url)"
if old not in source:
    raise RuntimeError("Expected download call was not found in v2 generator")
source = source.replace(old, new, 1)
namespace = {
    "__name__": "__main__",
    "__file__": str(source_path),
}
exec(compile(source, str(source_path), "exec"), namespace)
