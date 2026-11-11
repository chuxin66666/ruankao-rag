# -*- coding: utf-8 -*-
"""从Gitee备考仓库下载软件设计师语料（一次性脚本，用完可删）"""
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://gitee.com/stepwen2/software_designer/raw/main/"
OUT = Path(__file__).resolve().parent.parent / "data" / "raw"

FILES = [
    # 官方大纲（语料骨架）
    "3. 官方教材+教辅/软件设计师考试大纲-官方最新版.pdf",
    # 近年真题带解析（用户已有2020年的）
    "2. 真题及解析（2009年-2024年上半年）/2021年11月软件设计师上午真题+答案解析.pdf",
    "2. 真题及解析（2009年-2024年上半年）/2021年11月软件设计师下午真题及答案解析.pdf",
    "2. 真题及解析（2009年-2024年上半年）/2022年11月软件设计师上午真题及答案解析.pdf",
    "2. 真题及解析（2009年-2024年上半年）/2022年11月软件设计师下午真题及答案解析.pdf",
    "2. 真题及解析（2009年-2024年上半年）/2023年上半年软件设计师上午真题及答案解析.pdf",
    "2. 真题及解析（2009年-2024年上半年）/2023年上半年软件设计师下午真题及参考答案.pdf",
    # 章节习题（知识密度高，问答效果好）
    "4. 全真模拟卷+练习题/练习题/第 1 章：数据结构与算法.pdf",
    "4. 全真模拟卷+练习题/练习题/第 3 章：操作系统习题集(含答案).pdf",
    "4. 全真模拟卷+练习题/练习题/第 4 章：软件工程.pdf",
    "4. 全真模拟卷+练习题/练习题/第 5 章：面向对象方法学.pdf",
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in FILES:
        url = BASE + urllib.parse.quote(path)
        local = OUT / Path(path).name
        if local.exists():
            print(f"跳过（已存在）: {local.name}")
            continue
        print(f"下载中: {Path(path).name} ...", end=" ", flush=True)
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                data = resp.read()
            if data[:4] != b"%PDF":
                print("失败：返回的不是PDF，可能被限速，稍后再试")
                continue
            local.write_bytes(data)
            print(f"OK ({len(data) // 1024} KB)")
        except Exception as exc:  # noqa: BLE001
            print(f"失败: {exc}")


if __name__ == "__main__":
    main()
