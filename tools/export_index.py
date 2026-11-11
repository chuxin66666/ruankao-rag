# -*- coding: utf-8 -*-
"""
导出离线索引：本地跑一遍建库流程，把「片段+向量」存成 data/index.json
云端启动直接加载该文件，无需解析PDF和调用Embedding接口（冷启动从分钟级降到秒级）

运行： .venv/Scripts/python.exe tools/export_index.py
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from build_index import embed_texts, get_embedding_client, read_pdf, split_into_chunks  # noqa: E402
from config import DATA_DIR  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "data" / "index.json"


def main() -> None:
    chunks: list[dict] = []
    for pdf in sorted(DATA_DIR.glob("*.pdf")):
        chunks.extend(split_into_chunks(read_pdf(pdf), pdf.name))
    print(f"共 {len(chunks)} 个片段，开始向量化…")

    t0 = time.time()
    vectors = embed_texts(get_embedding_client(), [c["text"] for c in chunks])
    print(f"向量化耗时 {time.time() - t0:.1f} 秒")

    # 向量保留6位小数，文件从8MB降到3MB左右，对检索排序几乎无影响
    payload = {
        "chunks": chunks,
        "embeddings": [[round(v, 6) for v in vec] for vec in vectors],
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"索引已导出到 {OUT}（{OUT.stat().st_size // 1024 // 1024} MB）")


if __name__ == "__main__":
    main()
