import requests

class StockAuditor:
    """
    Audits backend inventory state via API to detect overselling
    and Time-of-Check to Time-of-Use (TOCTOU) anomalies.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url

    def reset_inventory(self):
        """Reset product stock to 1 before running an audit."""
        res = requests.post(f"{self.base_url}/api/reset")
        res.raise_for_status()

    def get_backend_state(self) -> dict:
        """Fetch the ground-truth inventory count and order list from backend."""
        res = requests.get(f"{self.base_url}/api/stock")
        res.raise_for_status()
        return res.json()