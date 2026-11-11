# -*- coding: utf-8 -*-
"""
问答核心：检索 -> 组织提示词 -> 调大模型生成带引用的答案

两种用法：
    命令行提问：  .venv/Scripts/python.exe src/qa.py "什么是多态？"
    交互模式：    .venv/Scripts/python.exe src/qa.py
"""
import sys
import time

from openai import OpenAI

from config import (
    CHROMA_DIR,
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    EMBEDDING_MODEL,
    LLM_MODEL,
    SILICONFLOW_API_KEY,
    SILICONFLOW_BASE_URL,
    TOP_K,
)

# Embedding 走 SiliconFlow（免费），生成答案走 DeepSeek
embed_client = OpenAI(api_key=SILICONFLOW_API_KEY, base_url=SILICONFLOW_BASE_URL)
llm_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    """把问题变成向量，从向量库检索最相关的 top_k 个片段"""
    import chromadb

    qvec = embed_client.embeddings.create(model=EMBEDDING_MODEL, input=question).data[0].embedding
    db = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = db.get_or_create_collection("ruankao_docs")
    result = collection.query(query_embeddings=[qvec], n_results=top_k)
    hits = []
    for doc, meta, dist in zip(result["documents"][0], result["metadatas"][0], result["distances"][0]):
        hits.append({"text": doc, **meta, "distance": dist})
    return hits


PROMPT_TEMPLATE = """你是软件设计师考试备考助手。请严格根据下面的参考资料回答问题。

要求：
1. 只依据资料内容作答，资料中没有的就明确说"参考资料中未涉及"
2. 每个关键论断后面用 [编号] 标注它出自哪份资料
3. 回答要准确、简洁，适合备考复习

{context_block}

问题：{question}"""


def build_prompt(question: str, hits: list[dict]) -> str:
    """把检索到的片段编成带编号的资料块，塞进提示词"""
    blocks = []
    for i, h in enumerate(hits, start=1):
        blocks.append(f"[资料{i}] （出处：{h['source']} 第{h['page_start']}-{h['page_end']}页）\n{h['text']}")
    return PROMPT_TEMPLATE.format(context_block="\n\n".join(blocks), question=question)


def ask(question: str) -> dict:
    """完整问答流程，返回答案、引用来源、耗时和token用量（供README统计成本）"""
    t0 = time.time()
    hits = retrieve(question)
    t_retrieve = time.time() - t0

    prompt = build_prompt(question, hits)
    t1 = time.time()
    resp = llm_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "你是严谨的教学助手，回答必须基于给定资料。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,  # 低温度=更确定、更少胡编（备考场景要准确不要发散）
    )
    t_llm = time.time() - t1

    usage = resp.usage
    return {
        "answer": resp.choices[0].message.content,
        "sources": hits,
        "retrieve_seconds": t_retrieve,
        "llm_seconds": t_llm,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
    }


def print_result(question: str, r: dict) -> None:
    print(f"\n{'='*60}\n问题：{question}\n{'='*60}")
    print(r["answer"])
    print(f"\n--- 引用来源 ---")
    for i, s in enumerate(r["sources"], start=1):
        print(f"[{i}] {s['source']} 第{s['page_start']}-{s['page_end']}页 (相似度距离: {s['distance']:.3f})")
    print(f"\n耗时：检索 {r['retrieve_seconds']:.2f}s + 生成 {r['llm_seconds']:.2f}s | "
          f"token: 输入{r['prompt_tokens']} 输出{r['completion_tokens']}")


def main() -> None:
    if len(sys.argv) > 1:
        print_result(sys.argv[1], ask(sys.argv[1]))
        return
    print("软件设计师问答助手（输入 exit 退出）")
    while True:
        try:
            q = input("\n你的问题：").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in ("exit", "quit"):
            break
        if q:
            print_result(q, ask(q))


if __name__ == "__main__":
    main()
