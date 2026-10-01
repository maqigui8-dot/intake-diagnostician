import asyncio
from playwright.async_api import async_playwright

CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe"
OUT = "C:/Users/Administrator/Desktop/project/intake-diagnostician/presentations/output"
BASE = "http://127.0.0.1:5173/"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=CHROME, headless=True)
        # 视口比例 2.28:1，匹配 PPT 图片框 10.933 x 4.8 英寸
        page = await browser.new_page(viewport={"width": 1368, "height": 600}, device_scale_factor=2)

        await page.goto(f"{BASE}", wait_until="networkidle")
        await page.wait_for_timeout(1800)
        await page.screenshot(path=f"{OUT}/shot-baseline.png")
        print("baseline OK")

        await page.goto(f"{BASE}?session=ppt-test-1", wait_until="networkidle")
        await page.wait_for_timeout(1800)
        await page.screenshot(path=f"{OUT}/shot-followup.png")
        print("followup OK")

        await page.goto(f"{BASE}?view=doctor&session=ppt-test-1", wait_until="networkidle")
        await page.wait_for_timeout(1800)
        await page.screenshot(path=f"{OUT}/shot-doctor.png")
        print("doctor OK")

        await browser.close()


asyncio.run(main())
