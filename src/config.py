# -*- coding: utf-8 -*-
"""全局配置：所有可调参数集中在这里，改一处全项目生效"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录（src 的上一级）
ROOT = Path(__file__).resolve().parent.parent

# 加载 .env 里的密钥
load_dotenv(ROOT / ".env")

# ---------- 路径 ----------
DATA_DIR = ROOT / "data" / "raw"        # 原始PDF放这里
CHROMA_DIR = ROOT / "chroma_db"         # 向量库存放位置

# ---------- 文档切分参数 ----------
CHUNK_SIZE = 500        # 每个片段约500个字符（语义完整性和检索精度的平衡点）
CHUNK_OVERLAP = 80      # 相邻片段重叠80字符，防止答案正好被切断

# ---------- 检索参数 ----------
TOP_K = 5               # 每次提问检索最相关的5个片段

# ---------- Embedding（SiliconFlow 提供，免费） ----------
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "")
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
EMBEDDING_MODEL = "BAAI/bge-m3"         # 中文效果好的开源模型，SiliconFlow免费托管

# ---------- 大模型（DeepSeek，生成答案） ----------
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
LLM_MODEL = "deepseek-chat"             # DeepSeek-V3，约1~2元/百万token
