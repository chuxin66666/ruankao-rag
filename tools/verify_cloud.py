# -*- coding: utf-8 -*-
"""对线上Demo做端到端验收：处理休眠唤醒、提问、截图、计时"""
import time

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://ruankao-rag-fdncznbumk6wdrazxa2z5j.streamlit.app/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})

    t0 = time.time()
    page.goto(URL, timeout=120000, wait_until="domcontentloaded")

    # 免费档休眠处理：等唤醒按钮出现再点击（按钮由前端JS渲染，需等待）
    try:
        page.wait_for_selector("text=get this app back up", timeout=60000)
        print(f"[{time.time()-t0:.0f}s] 应用处于休眠，点击唤醒…", flush=True)
        page.click("text=get this app back up")
    except PWTimeout:
        print(f"[{time.time()-t0:.0f}s] 未出现休眠页，直接等待应用加载", flush=True)

    page.wait_for_selector("textarea", timeout=360000)
    print(f"首屏就绪耗时: {time.time()-t0:.1f}s", flush=True)

    page.fill("textarea", "瀑布模型适用于什么场景？")
    page.keyboard.press("Enter")
    page.wait_for_selector("text=查看引用来源", timeout=180000)
    page.wait_for_timeout(1500)
    print(f"从打开到拿到回答: {time.time()-t0:.1f}s")
    page.screenshot(path="shot_cloud_final.png", full_page=True)

    browser.close()
print("线上验收完成")
