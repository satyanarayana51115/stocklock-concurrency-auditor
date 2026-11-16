from playwright.async_api import Page

class ProductPage:
    def __init__(self, page: Page):
        self.page = page
        self.product_title = page.locator("#product-name")
        self.stock_count = page.locator("#stock-count")
        self.buy_button = page.locator("#buy-btn")
        self.status_message = page.locator("#status")

    async def navigate(self, url: str = "http://127.0.0.1:8000"):
        """Navigate to the flash sale product page."""
        await self.page.goto(url)
        await self.buy_button.wait_for(state="visible")

    async def get_displayed_stock(self) -> int:
        """Return the available stock count displayed on the UI."""
        text = await self.stock_count.inner_text()
        return int(text.strip())

    async def click_buy_now(self):
        """Trigger the purchase action."""
        await self.buy_button.click()