from playwright.async_api import Page

class CheckoutPage:
    def __init__(self, page: Page):
        self.page = page
        self.status_message = page.locator("#status")

    async def wait_for_order_result(self) -> str:
        """Wait until payment processing finishes and return the final order status."""
        await self.page.wait_for_function(
            """() => {
                const el = document.getElementById('status');
                return el && el.innerText !== '' && el.innerText !== 'Processing payment...';
            }""",
            timeout=10000
        )
        return await self.status_message.inner_text()

    async def is_order_confirmed(self) -> bool:
        """Verify if the user's order succeeded."""
        result = await self.wait_for_order_result()
        return "Order Confirmed" in result