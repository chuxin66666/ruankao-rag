# -*- coding: utf-8 -*-
"""验证问答助手界面：打开页面、提问、截图"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("http://localhost:8501")
    page.wait_for_load_state("networkidle")
    page.screenshot(path="shot_home.png")

    # 在输入框中提问并提交
    page.fill("textarea", "什么是多态？")
    page.keyboard.press("Enter")
    page.wait_for_selector("text=查看引用来源", timeout=60000)
    page.wait_for_timeout(1000)
    page.screenshot(path="shot_answer.png", full_page=True)

    browser.close()
print("截图完成")
