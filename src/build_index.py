# -*- coding: utf-8 -*-
"""
建库脚本：把 data/raw/ 下的PDF变成可检索的向量库

流程：解析PDF -> 清洗水印 -> 切分片段 -> 调用Embedding接口转向量 -> 存入Chroma

运行方式（在项目根目录）：
    .venv/Scripts/python.exe src/build_index.py
"""
import sys
import time
from pathlib import Path

from openai import OpenAI
from pypdf import PdfReader

from config import (
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DATA_DIR,
    EMBEDDING_MODEL,
    SILICONFLOW_API_KEY,
    SILICONFLOW_BASE_URL,
)

# 这些关键词出自资料页脚的水印广告行，清洗时整行删除
WATERMARK_KEYWORDS = ["软考达人", "ruankaoda", "手机端题库", "PC题库", "免费分享",
                      "历年相关试题", "blog.csdn.net", "微信搜索"]


def read_pdf(pdf_path: Path) -> list[tuple[int, str]]:
    """读取一个PDF，返回 [(页码, 清洗后的该行文本), ...]"""
    reader = PdfReader(str(pdf_path))
    lines: list[tuple[int, str]] = []
    for page_no, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        for raw_line in text.split("\n"):
            line = raw_line.strip()
            if not line:
                continue
            if any(kw in line for kw in WATERMARK_KEYWORDS):
                continue  # 跳过水印行
            lines.append((page_no, line))
    return lines


def split_into_chunks(lines: list[tuple[int, str]], source: str) -> list[dict]:
    """把行文本按 CHUNK_SIZE 切分成片段，相邻片段保留重叠，并记录页码范围"""
    chunks: list[dict] = []
    buf = ""
    start_page = 1

    def emit(end_page: int) -> None:
        if buf.strip():
            chunks.append(
                {
                    "text": buf.strip(),
                    "source": source,
                    "page_start": start_page,
                    "page_end": end_page,
                }
            )

    for page_no, line in lines:
        candidate = buf + ("\n" if buf else "") + line
        if len(candidate) <= CHUNK_SIZE:
            buf = candidate
            continue
        # 当前缓冲已接近上限：收尾为一片段
        emit(page_no)
        # 下一片段以上一片段末尾的 CHUNK_OVERLAP 个字符开头（防止答案被切断）
        buf = buf[-CHUNK_OVERLAP:] + "\n" + line if buf else line
        start_page = page_no
    emit(lines[-1][0] if lines else 1)
    return chunks


def get_embedding_client() -> OpenAI:
    """SiliconFlow 的接口完全兼容 OpenAI 格式，直接用 openai 库连接"""
    if not SILICONFLOW_API_KEY or SILICONFLOW_API_KEY == "请替换":
        print("错误：请先在 .env 文件里填入 SILICONFLOW_API_KEY（SiliconFlow官网获取）")
        sys.exit(1)
    return OpenAI(api_key=SILICONFLOW_API_KEY, base_url=SILICONFLOW_BASE_URL)


def embed_texts(client: OpenAI, texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """分批调用Embedding接口（一批32条，避免请求过大被拒）"""
    vectors: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        vectors.extend(item.embedding for item in resp.data)
        print(f"  已向量化 {min(i + batch_size, len(texts))}/{len(texts)} 个片段", flush=True)
    return vectors


def main() -> None:
    pdfs = sorted(DATA_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"错误：{DATA_DIR} 下没有找到任何PDF")
        sys.exit(1)
    print(f"找到 {len(pdfs)} 个PDF文件")

    # 1. 解析 + 切分
    all_chunks: list[dict] = []
    for pdf in pdfs:
        lines = read_pdf(pdf)
        chunks = split_into_chunks(lines, pdf.name)
        print(f"  {pdf.name}: 切出 {len(chunks)} 个片段")
        all_chunks.extend(chunks)
    print(f"合计 {len(all_chunks)} 个片段")

    # 2. 向量化
    client = get_embedding_client()
    t0 = time.time()
    vectors = embed_texts(client, [c["text"] for c in all_chunks])
    print(f"向量化耗时 {time.time() - t0:.1f} 秒")

    # 3. 存入向量库
    import chromadb

    db = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = db.get_or_create_collection("ruankao_docs")
    collection.add(
        ids=[f"{c['source']}#{i}" for i, c in enumerate(all_chunks)],
        embeddings=vectors,
        documents=[c["text"] for c in all_chunks],
        metadatas=[
            {"source": c["source"], "page_start": c["page_start"], "page_end": c["page_end"]}
            for c in all_chunks
        ],
    )
    print(f"向量库已保存到 {CHROMA_DIR}，共 {collection.count()} 条记录")

    # 4. 打印一个片段示例，肉眼检查切分质量
    print("\n--- 片段示例（检查切分是否合理） ---")
    print(all_chunks[len(all_chunks) // 2]["text"][:300])


if __name__ == "__main__":
    main()
