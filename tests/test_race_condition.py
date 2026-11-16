import asyncio
import pytest
from pages.product_page import ProductPage
from pages.checkout_page import CheckoutPage
from utils.sync_barrier import ConcurrencyBarrier

async def run_concurrent_checkout_audit(page_a, page_b, target_url: str) -> tuple[bool, bool]:
    """Helper to synchronize two users on a given checkout URL and return their order outcomes."""
    barrier = ConcurrencyBarrier(party_count=2)

    async def simulate_user_purchase(page, user_name: str) -> bool:
        product_page = ProductPage(page)
        checkout_page = CheckoutPage(page)

        await product_page.navigate(url=target_url)
        displayed_stock = await product_page.get_displayed_stock()
        assert displayed_stock == 1, f"{user_name} did not see initial stock of 1."

        await barrier.wait_for_all(user_name)
        await product_page.click_buy_now()

        return await checkout_page.is_order_confirmed()

    user_a_won, user_b_won = await asyncio.gather(
        simulate_user_purchase(page_a, "User_A"),
        simulate_user_purchase(page_b, "User_B")
    )
    return user_a_won, user_b_won


@pytest.mark.asyncio
async def test_vulnerable_endpoint_exposes_overselling_bug(dual_user_contexts, auditor):
    """
    Audit 1 (Vulnerable Endpoint): Demonstrates how our framework catches a TOCTOU
    race condition when backend lacks concurrency locking (expected to fail on buggy build).
    """
    auditor.reset_inventory()
    page_a, page_b = dual_user_contexts

    user_a_won, user_b_won = await run_concurrent_checkout_audit(
        page_a, page_b, target_url="http://127.0.0.1:8000/"
    )

    successful_orders = sum([user_a_won, user_b_won])
    final_state = auditor.get_backend_state()

    assert successful_orders == 1, (
        f"RACE CONDITION DETECTED! Expected 1 successful order, but {successful_orders} succeeded. "
        f"Orders recorded: {final_state['orders']}"
    )


@pytest.mark.asyncio
async def test_mutex_locked_endpoint_prevents_overselling(dual_user_contexts, auditor):
    """
    Audit 2 (Fixed Endpoint): Verifies that when backend enforces mutex locking (/safe),
    only 1 user wins the last stock item while the concurrent user is gracefully rejected.
    """
    auditor.reset_inventory()
    page_a, page_b = dual_user_contexts

    user_a_won, user_b_won = await run_concurrent_checkout_audit(
        page_a, page_b, target_url="http://127.0.0.1:8000/safe"
    )

    successful_orders = sum([user_a_won, user_b_won])
    final_state = auditor.get_backend_state()

    assert successful_orders == 1, (
        f"Expected exactly 1 successful order under mutex lock, got {successful_orders}."
    )
    assert final_state["stock"] == 0, (
        f"Expected final backend stock to be 0, got {final_state['stock']}."
    )
    assert len(final_state["orders"]) == 1, (
        f"Expected 1 order in database, found {len(final_state['orders'])}."
    )