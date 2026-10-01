import asyncio
import sys
from playwright.async_api import async_playwright

CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe"
BASE = "http://127.0.0.1:5173/"
OUT_DIR = "C:/Users/Administrator/Desktop/project/intake-diagnostician/presentations/output"


async def shot(page, url, path, wait=2200):
    await page.goto(url, wait_until="networkidle")
    await page.wait_for_timeout(wait)
    await page.screenshot(path=path)
    print("OK", path)


async def main():
    session = sys.argv[1] if len(sys.argv) > 1 else ""
    suffix = f"&session={session}" if session else ""
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=CHROME, headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800}, device_scale_factor=2)
        await shot(page, f"{BASE}?session={session}", f"{OUT_DIR}/shot-followup.png")
        await shot(page, f"{BASE}?doctor=1{suffix}", f"{OUT_DIR}/shot-doctor.png")
        await browser.close()


asyncio.run(main())
