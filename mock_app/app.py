import asyncio
import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI()
DB_PATH = Path(__file__).parent / "database.json"
inventory_lock = asyncio.Lock()

def read_db():
    with open(DB_PATH, "r") as f:
        return json.load(f)

def write_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

def render_store_html(db: dict, api_endpoint: str, mode_label: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>StockLock Flash Sale - {mode_label}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 12px 20px; background: #f4f4f9; }}
            .card {{ background: white; padding: 20px 26px; border-radius: 12px; max-width: 520px; box-shadow: 0 4px 12px rgba(0,0,0,0.12); }}
            .badge {{ display: inline-block; padding: 6px 12px; font-size: 15px; font-weight: bold; border-radius: 6px; background: #e2e8f0; color: #1e293b; margin-bottom: 10px; }}
            h2 {{ font-size: 26px; margin: 8px 0 14px 0; color: #0f172a; }}
            .info-text {{ font-size: 21px; font-weight: 600; margin: 10px 0; color: #334155; }}
            #stock-count {{ font-size: 24px; font-weight: bold; color: #0284c7; }}
            button {{ background: #16a34a; color: white; border: none; padding: 14px 28px; font-size: 20px; font-weight: bold; cursor: pointer; border-radius: 8px; margin-top: 8px; }}
            button:disabled {{ background: #94a3b8; }}
            #status {{ margin-top: 16px; font-weight: bold; font-size: 22px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <span class="badge">{mode_label}</span>
            <h2 id="product-name">{db['product_name']}</h2>
            <p class="info-text">Price: ₹{db['price']}</p>
            <p class="info-text">Available Stock: <span id="stock-count">{db['stock']}</span></p>
            <button id="buy-btn" onclick="placeOrder()">Buy Now</button>
            <div id="status"></div>
        </div>

        <script>
            async function placeOrder() {{
                const btn = document.getElementById('buy-btn');
                const statusDiv = document.getElementById('status');
                btn.disabled = true;
                statusDiv.innerText = "Processing payment...";
                statusDiv.style.color = "#475569";

                const res = await fetch('{api_endpoint}', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ user: "Customer_" + Math.floor(Math.random() * 1000) }})
                }});
                const data = await res.json();
                statusDiv.innerText = data.message;
                statusDiv.style.color = data.success ? "#15803d" : "#dc2626";
                document.getElementById('stock-count').innerText = data.remaining_stock;
            }}
        </script>
    </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
async def home_vulnerable():
    """Render checkout page backed by an unlocked, race-condition-prone endpoint."""
    return render_store_html(read_db(), "/api/buy", "MODE: UNLOCKED (VULNERABLE)")

@app.get("/safe", response_class=HTMLResponse)
async def home_safe():
    """Render checkout page backed by a mutex-locked, concurrency-safe endpoint."""
    return render_store_html(read_db(), "/api/buy-safe", "MODE: MUTEX LOCKED (SAFE)")

@app.post("/api/buy")
async def buy_product_vulnerable(request: Request):
    """Vulnerable purchase endpoint without concurrency locking."""
    body = await request.json()
    user = body.get("user", "Unknown")

    db = read_db()
    current_stock = db["stock"]

    if current_stock > 0:
        await asyncio.sleep(0.5)
        db["stock"] = current_stock - 1
        db["orders"].append(user)
        write_db(db)
        return JSONResponse({"success": True, "message": f"Order Confirmed for {user}!", "remaining_stock": db["stock"]})
    return JSONResponse({"success": False, "message": "Out of Stock!", "remaining_stock": current_stock})

@app.post("/api/buy-safe")
async def buy_product_safe(request: Request):
    """Concurrency-safe purchase endpoint protected by an asynchronous mutex lock."""
    body = await request.json()
    user = body.get("user", "Unknown")

    async with inventory_lock:
        db = read_db()
        current_stock = db["stock"]

        if current_stock > 0:
            await asyncio.sleep(0.5)
            db["stock"] = current_stock - 1
            db["orders"].append(user)
            write_db(db)
            return JSONResponse({"success": True, "message": f"Order Confirmed for {user}!", "remaining_stock": db["stock"]})
        return JSONResponse({"success": False, "message": "Out of Stock!", "remaining_stock": current_stock})

@app.get("/api/stock")
async def get_stock():
    return read_db()

@app.post("/api/reset")
async def reset_stock():
    write_db({
        "product_name": "iPhone 17 Pro (Limited Edition)",
        "price": 120000,
        "stock": 1,
        "orders": []
    })
    return {"message": "Stock reset to 1"}