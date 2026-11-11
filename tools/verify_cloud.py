# -*- coding: utf-8 -*-
"""对线上Demo做端到端验收：计时首屏加载、提问、拿到回答"""
import time

from playwright.sync_api import sync_playwright

URL = "https://ruankao-rag-fdncznbumk6wdrazxa2z5j.streamlit.app/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})

    t0 = time.time()
    page.goto(URL, timeout=180000, wait_until="domcontentloaded")
    # 等输入框出现（应用就绪）
    page.wait_for_selector("textarea", timeout=300000)
    t_first = time.time() - t0
    print(f"首屏就绪耗时: {t_first:.1f}s")
    page.screenshot(path="shot_cloud_home.png")

    # 提问并等回答渲染
    page.fill("textarea", "瀑布模型适用于什么场景？")
    page.keyboard.press("Enter")
    page.wait_for_selector("text=查看引用来源", timeout=120000)
    page.wait_for_timeout(1500)
    t_answer = time.time() - t0
    print(f"从打开到拿到回答: {t_answer:.1f}s")
    page.screenshot(path="shot_cloud_answer.png", full_page=True)

    browser.close()
print("线上验收完成")
