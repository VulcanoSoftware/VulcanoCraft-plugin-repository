import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Listen for console messages and print them
        page.on("console", lambda msg: print(f"CONSOLE ({msg.type}): {msg.text}"))

        # Go to the login page
        await page.goto("http://localhost:5000/login-page")

        # Wait for the login form to be visible and fill it
        await page.wait_for_selector('#loginUsername')
        await page.fill('#loginUsername', "admin")
        await page.fill('#loginPassword', "admin123")

        # Click the login button
        await page.click('#loginBtn')

        # Wait for navigation to the main page and for the sidebar to be visible
        await page.wait_for_url("http://localhost:5000/")
        await page.wait_for_selector("#category-sidebar", timeout=10000)

        # Take a screenshot of the main page
        await page.screenshot(path="/home/jules/verification/screenshot.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
