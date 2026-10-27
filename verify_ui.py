from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:5000/")
        page.wait_for_selector(".plugin-card")

        # Take a screenshot of the main page
        page.screenshot(path="/tmp/main_page.png", full_page=True)

        # Click pin version button on the first card if exists
        pin_btn = page.query_selector(".pin-version-btn")
        if pin_btn:
            pin_btn.click()
            page.wait_for_selector("#versionPinModal", state="visible")
            page.wait_for_timeout(1000)
            page.screenshot(path="/tmp/pin_modal.png")

        browser.close()

if __name__ == "__main__":
    run()
