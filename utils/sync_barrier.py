import asyncio

class ConcurrencyBarrier:
    """
    Synchronizes multiple concurrent browser sessions so they execute
    a critical action (such as clicking 'Buy Now') at the exact same instant.
    """
    def __init__(self, party_count: int):
        self.party_count = party_count
        self._barrier = asyncio.Barrier(party_count)

    async def wait_for_all(self, user_label: str):
        """Hold execution until all simulated users reach the barrier."""
        print(f"[SYNC] {user_label} is ready and waiting at the checkout barrier...")
        await self._barrier.wait()
        print(f"[EXEC] Barrier released! {user_label} executing action simultaneously.")