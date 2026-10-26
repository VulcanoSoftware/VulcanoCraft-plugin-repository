import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        # Load main page
        await page.goto('http://localhost:5000/')
        await page.wait_for_selector('.plugin-card')
        await asyncio.sleep(1)

        # 1. Take screenshot as guest showing pinned badge and update available badge
        await page.screenshot(path='/home/jules/verification/screenshots/pinned_guest_view.png')

        # Click update badge to show details modal
        await page.click('.update-available-badge')
        await page.wait_for_selector('#genericAlertModal.show')
        await asyncio.sleep(0.5)
        await page.screenshot(path='/home/jules/verification/screenshots/pinned_update_modal.png')

        # Close alert modal
        await page.click('#genericAlertOkBtn')
        await asyncio.sleep(0.5)

        # 2. Login via /login-page
        await page.goto('http://localhost:5000/login-page')
        await page.wait_for_selector('#loginUsername')
        await page.fill('#loginUsername', 'admin')
        await page.fill('#loginPassword', 'adminpass')
        await page.click('#loginBtn')
        await asyncio.sleep(1)

        # Return to home page
        await page.goto('http://localhost:5000/')
        await page.wait_for_selector('.plugin-card')
        await asyncio.sleep(1)

        # Take screenshot as logged-in owner/admin showing "Versie pinnen" / "Versie wijzigen" buttons
        await page.screenshot(path='/home/jules/verification/screenshots/pinned_admin_view.png')

        # 3. Click Pin Version button on WorldEdit
        pin_btn = page.locator('.pin-version-btn[data-url="https://modrinth.com/plugin/worldedit"]')
        await pin_btn.click()
        await page.wait_for_selector('#pinVersionModal.show')
        await asyncio.sleep(1)

        # Take screenshot of Pin Version Modal GUI
        await page.screenshot(path='/home/jules/verification/screenshots/pinned_modal_gui.png')

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
