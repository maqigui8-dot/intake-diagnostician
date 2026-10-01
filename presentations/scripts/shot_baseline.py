import asyncio
from playwright.async_api import async_playwright

CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe"
OUT = "C:/Users/Administrator/Desktop/project/intake-diagnostician/presentations/output/shot-baseline.png"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=CHROME, headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800}, device_scale_factor=2)
        await page.goto("http://127.0.0.1:5173/", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=OUT)
        await browser.close()
        print("OK", OUT)


asyncio.run(main())
