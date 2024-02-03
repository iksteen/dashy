from playwright.async_api import Browser, Playwright, async_playwright

from dashy.services import ServiceProvider


class PlaywrightProvider(ServiceProvider[Browser]):
    playwright: Playwright
    browser: Browser

    async def start(self) -> Browser:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(handle_sigint=False)
        return self.browser

    async def stop(self) -> None:
        await self.browser.close()
        await self.playwright.stop()
