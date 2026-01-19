from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width':1400,'height':900})
    page.goto('$releaseUrl', timeout=60000)
    page.wait_for_timeout(2000)
    page.screenshot(path=r'${releaseScreenshot}', full_page=True)
    browser.close()
