# Quick browser test without persistent context
import asyncio
from playwright.async_api import async_playwright
import os

async def simple_youtube_test():
    print("Starting simple browser test...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        try:
            print("[1] Going to YouTube...")
            await page.goto('https://www.youtube.com', timeout=30000)
            await asyncio.sleep(2)
            
            print("[2] Searching...")
            search = await page.wait_for_selector('input#search', timeout=10000)
            await search.fill('biology 2024')
            await search.press('Enter')
            await asyncio.sleep(3)
            
            print("[3] Clicking result...")
            await page.wait_for_selector('ytd-video-renderer', timeout=15000)
            await page.click('ytd-video-renderer:nth-child(3) a#thumbnail')
            await asyncio.sleep(5)
            
            print("[4] Seeking to 180s...")
            await page.wait_for_selector('video', timeout=15000)
            await page.evaluate('document.querySelector("video").currentTime = 180')
            await asyncio.sleep(2)
            
            print("[5] Pausing...")
            await page.evaluate('document.querySelector("video").pause()')
            
            print("[6] Screenshot...")
            os.makedirs('E:/ai_desktop_assistant/logs/snapshots', exist_ok=True)
            await page.screenshot(path='E:/ai_desktop_assistant/logs/snapshots/multitask_result.png')
            
            print("SUCCESS!")
            return True
            
        except Exception as e:
            print(f"ERROR: {e}")
            try:
                await page.screenshot(path='E:/ai_desktop_assistant/logs/snapshots/error.png')
            except:
                pass
            return False
        finally:
            await browser.close()

asyncio.run(simple_youtube_test())
