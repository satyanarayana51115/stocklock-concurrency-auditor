import asyncio
import ctypes
import pytest
import pytest_asyncio
from playwright.async_api import async_playwright
from utils.stock_auditor import StockAuditor

def get_screen_dimensions() -> tuple[int, int]:
    """Dynamically detect the active monitor's logical width and height."""
    try:
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    except Exception:
        return 1536, 864

@pytest.fixture(scope="session")
def auditor():
    """Provide the backend StockAuditor instance."""
    return StockAuditor(base_url="http://127.0.0.1:8000")

@pytest_asyncio.fixture
async def dual_user_contexts():
    """
    Launch two side-by-side browser windows covering the exact top half of the screen
    (Left 50% for User A, Right 50% for User B) with zero gaps.
    """
    screen_w, screen_h = get_screen_dimensions()
    half_w = screen_w // 2
    half_h = int(screen_h * 0.52)

    async with async_playwright() as p:
        # Left Browser Window: 0 to 50% width
        browser_a = await p.chromium.launch(
            headless=False,
            slow_mo=250,
            args=[f"--window-position=0,0", f"--window-size={half_w},{half_h}"]
        )
        # Right Browser Window: 50% to 100% width
        browser_b = await p.chromium.launch(
            headless=False,
            slow_mo=250,
            args=[f"--window-position={half_w},0", f"--window-size={half_w},{half_h}"]
        )
        
        context_a = await browser_a.new_context(no_viewport=True)
        context_b = await browser_b.new_context(no_viewport=True)

        await context_a.tracing.start(screenshots=True, snapshots=True)
        await context_b.tracing.start(screenshots=True, snapshots=True)

        page_a = await context_a.new_page()
        page_b = await context_b.new_page()

        yield page_a, page_b

        # Hold final order confirmation/rejection state on screen for 5 seconds
        await asyncio.sleep(5)

        await context_a.tracing.stop(path="reports/trace_user_a.zip")
        await context_b.tracing.stop(path="reports/trace_user_b.zip")

        await context_a.close()
        await context_b.close()
        await browser_a.close()
        await browser_b.close()