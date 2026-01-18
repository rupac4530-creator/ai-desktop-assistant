# automation/browser.py
"""Playwright browser automation with automatic headless fallback."""

import asyncio
import os
import time
import logging
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None

LOG_DIR = Path(__file__).parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)
(LOG_DIR / 'snapshots').mkdir(exist_ok=True)

logging.basicConfig(
    filename=str(LOG_DIR / 'multitask.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('browser')


class BrowserAutomation:
    """Browser automation with smart headful/headless handling."""

    def __init__(self, headless=None):
        # None = try headful first, True = force headless, False = force headful
        self.force_mode = headless
        self.browser = None
        self.context = None
        self.page = None
        self._playwright = None
        self.default_timeout = 20000
        self.is_headless = False
        self.fallback_used = False

    async def start(self, try_headful=True):
        """Start browser. If try_headful and it fails during first action, will retry headless."""
        if async_playwright is None:
            raise ImportError("playwright not installed")

        self._playwright = await async_playwright().start()
        
        # Determine mode
        if self.force_mode is True:
            headless = True
        elif self.force_mode is False:
            headless = False
        else:
            headless = not try_headful
        
        await self._launch(headless)
        return self

    async def _launch(self, headless):
        """Launch browser with given mode."""
        self.is_headless = headless
        # Stability flags to prevent Windows from killing/backgrounding the browser
        launch_args = [
            '--disable-gpu',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-background-timer-throttling',
            '--no-first-run',
            '--no-default-browser-check',
        ]
        self.browser = await self._playwright.chromium.launch(
            headless=headless,
            args=launch_args
        )
        self.context = await self.browser.new_context(viewport={'width': 1280, 'height': 800})
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.default_timeout)
        mode = "headless" if headless else "headful"
        logger.info(f"Browser launched ({mode})")
        print(f"[Browser] Started in {mode} mode")

    async def _restart_headless(self):
        """Restart in headless mode after headful failure."""
        print("[Browser] Headful mode failed. Switching to headless...")
        logger.warning("Headful mode failed, restarting in headless")
        self.fallback_used = True
        
        # Close existing
        try:
            if self.browser:
                await self.browser.close()
        except:
            pass
        
        # Relaunch headless
        await self._launch(headless=True)
        
        # Notify user
        try:
            from speech.local_tts import LocalTTS
            LocalTTS().speak("Switched to background mode")
        except:
            pass

    async def stop(self):
        """Close browser."""
        try:
            if self.browser:
                await self.browser.close()
            if self._playwright:
                await self._playwright.stop()
            logger.info("Browser stopped")
        except Exception as e:
            logger.error(f"Stop error: {e}")

    async def _safe_action(self, name, coro_func, retries=3):
        """Execute action with retries. On TargetClosed error, switch to headless."""
        for attempt in range(retries):
            try:
                result = await coro_func()
                logger.info(f"{name} succeeded")
                return result
            except Exception as e:
                err_str = str(e).lower()
                
                # If browser was closed externally (headful blocked), switch to headless
                if 'closed' in err_str or 'target' in err_str:
                    if not self.is_headless and attempt == 0:
                        await self._restart_headless()
                        continue  # Retry with headless
                
                logger.warning(f"{name} attempt {attempt+1} failed: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
        
        # Save failure screenshot if possible
        try:
            await self.page.screenshot(path=str(LOG_DIR / 'snapshots' / f'fail_{int(time.time())}.png'))
        except:
            pass
        
        raise Exception(f"{name} failed after {retries} attempts")

    async def screenshot(self, path=None):
        if path is None:
            path = str(LOG_DIR / 'snapshots' / f'screen_{int(time.time())}.png')
        await self.page.screenshot(path=path)
        logger.info(f"Screenshot: {path}")
        return path

    # --- YouTube Methods ---

    async def youtube_search(self, query):
        """Search YouTube and return result count."""
        async def _do():
            await self.page.goto('https://www.youtube.com', timeout=30000)
            await asyncio.sleep(3)
            
            # Handle cookie/consent dialogs (various regional forms)
            consent_selectors = [
                'button:has-text("Accept all")',
                'button:has-text("Accept")',
                'button:has-text("Agree")',
                'button:has-text("I agree")',
                '[aria-label="Accept all"]',
                '[aria-label="Accept the use of cookies"]',
            ]
            for sel in consent_selectors:
                try:
                    btn = self.page.locator(sel)
                    if await btn.count() > 0:
                        await btn.first.click()
                        await asyncio.sleep(2)
                        break
                except:
                    pass
            
            # Try multiple search selectors
            search = None
            search_selectors = ['input#search', 'input[name="search_query"]', '#search-input input']
            for sel in search_selectors:
                try:
                    search = await self.page.wait_for_selector(sel, timeout=10000)
                    if search:
                        break
                except:
                    continue
            
            if not search:
                raise Exception("Could not find YouTube search box")
                
            await search.fill(query)
            await search.press('Enter')
            
            await self.page.wait_for_selector('ytd-video-renderer', timeout=20000)
            await asyncio.sleep(1)
            results = await self.page.query_selector_all('ytd-video-renderer')
            return len(results)
        
        return await self._safe_action(f"youtube_search({query})", _do)

    async def youtube_click_result(self, n=1):
        """Click nth video result."""
        async def _do():
            sel = f'ytd-video-renderer:nth-child({n}) a#thumbnail'
            await self.page.wait_for_selector(sel, timeout=10000)
            await self.page.click(sel)
            await self.page.wait_for_selector('video', timeout=20000)
            await asyncio.sleep(3)
            return True
        return await self._safe_action(f"click_result({n})", _do)

    async def youtube_seek_to(self, seconds):
        """Seek video to timestamp."""
        async def _do():
            await self.page.wait_for_function(
                "() => document.querySelector('video')?.readyState >= 2",
                timeout=15000
            )
            await self.page.evaluate(f"document.querySelector('video').currentTime = {seconds}")
            await asyncio.sleep(1)
            return True
        return await self._safe_action(f"seek({seconds}s)", _do)

    async def youtube_pause(self):
        """Pause video."""
        async def _do():
            await self.page.evaluate("document.querySelector('video')?.pause()")
            return True
        return await self._safe_action("pause", _do)

    async def youtube_play(self):
        """Play video."""
        async def _do():
            await self.page.evaluate("document.querySelector('video')?.play()")
            return True
        return await self._safe_action("play", _do)


async def run_test():
    """Run acceptance test."""
    print("="*60)
    print("BROWSER AUTOMATION TEST")
    print("="*60)
    
    browser = BrowserAutomation()  # Auto-detect mode
    
    try:
        print("\n[1] Starting browser...")
        await browser.start(try_headful=True)
        
        print("\n[2] Searching YouTube...")
        count = await browser.youtube_search("biology 2024")
        print(f"    Found {count} results")
        
        print("\n[3] Clicking 3rd result...")
        await browser.youtube_click_result(3)
        
        print("\n[4] Seeking to 180s...")
        await browser.youtube_seek_to(180)
        
        print("\n[5] Pausing...")
        await browser.youtube_pause()
        
        print("\n[6] Screenshot...")
        path = str(LOG_DIR / 'snapshots' / 'multitask_result.png')
        await browser.screenshot(path)
        print(f"    Saved: {path}")
        
        mode = "HEADLESS (fallback)" if browser.fallback_used else "HEADFUL"
        print(f"\n{'='*60}")
        print(f"SUCCESS - Mode: {mode}")
        print(f"{'='*60}")
        return True
        
    except Exception as e:
        print(f"\nFAILED: {e}")
        return False
    finally:
        await browser.stop()


if __name__ == "__main__":
    asyncio.run(run_test())
