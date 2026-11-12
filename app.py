# -*- coding: utf-8 -*-
"""
软件设计师智能问答助手 - Streamlit前端

本地运行：  .venv/Scripts/python.exe -m streamlit run app.py
"""
import sys
from pathlib import Path

import streamlit as st

# 让 app.py 能找到 src 目录下的模块
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import CHROMA_DIR  # noqa: E402
import qa  # noqa: E402

ask = qa.ask  # 别名，供下方问答逻辑使用


@st.cache_resource
def ensure_index() -> str:
    """启动时预加载知识库：有离线索引文件则秒载；否则（本地首次）现场建库"""
    if not qa.INDEX_JSON.exists() and not (CHROMA_DIR / "chroma.sqlite3").exists():
        from build_index import main as build_main

        build_main()
    qa.get_collection()  # 预加载，让首个问题也飞快
    return "就绪"


st.set_page_config(page_title="软考问答助手", page_icon="📚", layout="centered")

st.title("📚 软件设计师智能问答助手")
st.caption("基于历年真题与章节习题库 · 回答附引用出处 · 资料没有的内容会如实告知")

# 云端首次启动时自动建库（本地已有则秒过）；失败时显示错误但页面仍可用
with st.spinner("正在初始化知识库…"):
    try:
        ensure_index()
    except Exception as exc:  # noqa: BLE001
        st.error(f"知识库初始化失败：{type(exc).__name__}: {exc}")

# 侧边栏：项目说明
with st.sidebar:
    st.header("关于")
    st.info(
        "本助手使用 RAG（检索增强生成）技术：\n\n"
        "1. 把你的问题转为向量\n"
        "2. 在考试资料库中检索最相关的片段\n"
        "3. 由大模型基于片段生成答案并标注出处\n\n"
        "语料：软件设计师历年真题及章节习题（公开备考资料）"
    )
    if st.button("清除对话"):
        st.session_state.messages = []
        st.rerun()

# 用 session_state 保存对话历史（刷新页面不丢失）
if "messages" not in st.session_state:
    st.session_state.messages = []

# 渲染历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            with st.expander("📎 查看引用来源"):
                for i, s in enumerate(msg["sources"], start=1):
                    st.markdown(f"**[{i}] {s['source']}** 第{s['page_start']}-{s['page_end']}页")
                    st.caption(s["text"][:150].replace("\n", " ") + "…")

# 接收用户输入
question = st.chat_input("输入你的备考问题，例如：什么是多态？")
if question:
    with st.chat_message("user"):
        st.markdown(question)
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("assistant"):
        with st.spinner("正在检索资料并生成回答…"):
            result = ask(question)
        st.markdown(result["answer"])
        with st.expander("📎 查看引用来源"):
            for i, s in enumerate(result["sources"], start=1):
                st.markdown(f"**[{i}] {s['source']}** 第{s['page_start']}-{s['page_end']}页")
                st.caption(s["text"][:150].replace("\n", " ") + "…")
        st.caption(
            f"⏱ 检索 {result['retrieve_seconds']:.1f}s · 生成 {result['llm_seconds']:.1f}s · "
            f"token 输入{result['prompt_tokens']}/输出{result['completion_tokens']}"
        )
    st.session_state.messages.append(
        {"role": "assistant", "content": result["answer"], "sources": result["sources"]}
    )
