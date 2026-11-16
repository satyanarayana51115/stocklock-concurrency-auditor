import pytest
import pytest_asyncio
from playwright.async_api import async_playwright
from utils.stock_auditor import StockAuditor

@pytest.fixture(scope="session")
def auditor():
    """Provide the backend StockAuditor instance."""
    return StockAuditor(base_url="http://127.0.0.1:8000")

@pytest_asyncio.fixture
async def dual_user_contexts():
    """
    Launch a browser and create two completely isolated browser contexts
    (simulating User A and User B with separate sessions/cookies).
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        
        context_a = await browser.new_context()
        context_b = await browser.new_context()

        # Start Playwright tracing for post-mortem concurrency debugging
        await context_a.tracing.start(screenshots=True, snapshots=True)
        await context_b.tracing.start(screenshots=True, snapshots=True)

        page_a = await context_a.new_page()
        page_b = await context_b.new_page()

        yield page_a, page_b

        # Save execution traces into the reports directory
        await context_a.tracing.stop(path="reports/trace_user_a.zip")
        await context_b.tracing.stop(path="reports/trace_user_b.zip")

        await context_a.close()
        await context_b.close()
        await browser.close()