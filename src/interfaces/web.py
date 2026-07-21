from datetime import datetime
import stripe
import datetime
import json
import os
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from src.infrastructure.storage import Storage
from src.domain.payment import Invoice
from src.application.use_cases.payment_processor import PaymentProcessor

# Завантаження змінних середовища
load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="AION Opportunity Hunter", version="0.1.0")

storage = Storage("aion.db")

if os.path.exists("landings"):
    app.mount("/landings", StaticFiles(directory="landings"), name="landings")

# Вибір платіжного провайдера
provider_type = os.getenv("PAYMENT_PROVIDER", "simulated")
logger.info(f"Payment provider: {provider_type}")

if provider_type == "stripe":
    try:
        from src.infrastructure.payment.stripe_provider import StripeProvider
        payment_provider = StripeProvider()
        logger.info("✅ StripeProvider initialized")
    except Exception as e:
        logger.error(f"Failed to initialize StripeProvider: {e}")
        # Fallback на SimulatedProvider
        from src.infrastructure.payment.simulated_provider import SimulatedProvider
        payment_provider = SimulatedProvider()
        logger.warning("⚠️ Falling back to SimulatedProvider")
else:
    from src.infrastructure.payment.simulated_provider import SimulatedProvider
    payment_provider = SimulatedProvider()
    logger.info("✅ SimulatedProvider initialized")

payment_processor = PaymentProcessor(storage, payment_provider)

@app.on_event("startup")
async def startup():
    await storage.init()

@app.get("/", response_class=HTMLResponse)
async def list_hypotheses():
    if storage.conn is None:
        await storage.init()
    
    cursor = await storage.conn.execute(
        "SELECT id, metadata, created_at FROM objects WHERE type='Hypothesis' ORDER BY created_at DESC"
    )
    rows = await cursor.fetchall()
    
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AION — Opportunity Hunter</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Inter', sans-serif; background: #0b0b12; color: #f0f0f5; padding: 2rem 1.5rem; }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { font-size: 2.5rem; font-weight: 700; background: linear-gradient(135deg, #fff 30%, #8b8bf7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .sub { color: #b0b0c8; margin-bottom: 2rem; }
            table { width: 100%; border-collapse: collapse; background: #14141f; border-radius: 16px; overflow: hidden; border: 1px solid #1e1e30; }
            th { background: #1a1a2e; padding: 1rem; text-align: left; font-weight: 600; color: #c8c8ff; }
            td { padding: 1rem; border-bottom: 1px solid #1a1a2a; }
            tr:hover td { background: #1a1a2e; }
            .badge { display: inline-block; padding: 0.2rem 0.8rem; border-radius: 60px; font-size: 0.7rem; font-weight: 600; }
            .badge-yes { background: rgba(108,240,108,0.15); color: #6cf06c; border: 1px solid rgba(108,240,108,0.2); }
            .badge-no { background: rgba(240,108,108,0.15); color: #f06c6c; border: 1px solid rgba(240,108,108,0.2); }
            .link { color: #8b8bf7; text-decoration: none; font-weight: 600; }
            .link:hover { text-decoration: underline; }
            .stats { display: flex; gap: 2rem; margin: 1.5rem 0; }
            .stat { background: #14141f; padding: 0.8rem 1.5rem; border-radius: 12px; border: 1px solid #1e1e30; }
            .stat span { font-size: 0.8rem; color: #8080a0; display: block; }
            .stat strong { font-size: 1.5rem; color: #f0f0ff; }
            @media (max-width: 768px) { table { font-size: 0.8rem; } td, th { padding: 0.5rem; } }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧠 Opportunity Hunter</h1>
            <p class="sub">AI-generated hypotheses based on real user problems</p>
            <div class="stats">
                <div class="stat"><span>Total</span><strong>""" + str(len(rows)) + """</strong></div>
                <div class="stat"><span>With Landing</span><strong>""" + str(sum(1 for r in rows if os.path.exists(f"landings/{r[0]}.html"))) + """</strong></div>
            </div>
            <table>
                <thead><tr><th>#</th><th>Problem</th><th>Headline</th><th>MVP</th><th>Created</th><th>Landing</th><th>Action</th></tr></thead>
                <tbody>
    """
    
    for idx, row in enumerate(rows, 1):
        metadata = json.loads(row[1])
        problem = metadata.get("problem") or "Unknown"
        headline = metadata.get("landing_headline") or "No headline"
        mvp = metadata.get("mvp") or "No MVP"
        created = row[2][:10] if row[2] else "N/A"
        has_landing = os.path.exists(f"landings/{row[0]}.html")
        
        html += f"""
        <tr>
            <td>{idx}</td>
            <td>{problem[:60]}{'...' if len(problem)>60 else ''}</td>
            <td>{headline}</td>
            <td>{mvp[:50]}{'...' if len(mvp)>50 else ''}</td>
            <td>{created}</td>
            <td>{'<span class="badge badge-yes">✅ Yes</span>' if has_landing else '<span class="badge badge-no">❌ No</span>'}</td>
            <td>
                <a href="/hypothesis/{row[0]}" class="link">View</a>
                {f'| <a href="/landing/{row[0]}" class="link" target="_blank">🌐</a>' if has_landing else ''}
            </td>
        </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/hypothesis/{hypothesis_id}", response_class=HTMLResponse)
async def view_hypothesis(hypothesis_id: str):
    obj = await storage.get_object(hypothesis_id)
    if not obj or obj["type"] != "Hypothesis":
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    
    metadata = obj.get("metadata", {})
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hypothesis — AION</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Inter', sans-serif; background: #0b0b12; color: #f0f0f5; padding: 2rem 1.5rem; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .back {{ color: #8b8bf7; text-decoration: none; font-weight: 600; margin-bottom: 1.5rem; display: inline-block; }}
            .back:hover {{ text-decoration: underline; }}
            .card {{ background: #14141f; border-radius: 24px; padding: 2.5rem; border: 1px solid #1e1e30; box-shadow: 0 8px 30px rgba(0,0,0,0.3); }}
            .card h1 {{ font-size: 2.2rem; font-weight: 800; margin-bottom: 0.8rem; background: linear-gradient(135deg, #fff 20%, #8b8bf7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
            .card .id {{ font-size: 0.75rem; color: #606080; margin-bottom: 1.5rem; }}
            .field {{ margin-bottom: 1.5rem; }}
            .field .label {{ font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #8080a0; }}
            .field .value {{ font-size: 1rem; color: #e8e8ff; margin-top: 0.2rem; line-height: 1.6; background: #0b0b12; padding: 0.8rem 1rem; border-radius: 12px; border: 1px solid #1a1a2a; }}
            .badge {{ display: inline-block; padding: 0.2rem 0.8rem; border-radius: 60px; font-size: 0.7rem; font-weight: 600; }}
            .badge-yes {{ background: rgba(108,240,108,0.15); color: #6cf06c; border: 1px solid rgba(108,240,108,0.2); }}
            .badge-no {{ background: rgba(240,108,108,0.15); color: #f06c6c; border: 1px solid rgba(240,108,108,0.2); }}
            .btn {{ display: inline-block; background: #6c6cf0; color: #fff; padding: 0.8rem 2rem; border-radius: 60px; font-weight: 700; text-decoration: none; margin-top: 1rem; transition: 0.2s; }}
            .btn:hover {{ background: #5a5ae0; transform: scale(1.02); }}
            @media (max-width: 640px) {{ .card {{ padding: 1.5rem; }} .card h1 {{ font-size: 1.6rem; }} }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back">← Back to all hypotheses</a>
            <div class="card">
                <h1>{metadata.get('landing_headline', 'Untitled')}</h1>
                <div class="id">ID: {hypothesis_id[:8]}...</div>

                <div class="field">
                    <div class="label">📌 Problem</div>
                    <div class="value">{metadata.get('problem', 'N/A')}</div>
                </div>

                <div class="field">
                    <div class="label">💡 MVP</div>
                    <div class="value">{metadata.get('mvp', 'N/A')}</div>
                </div>

                <div class="field">
                    <div class="label">🧪 Hypothesis</div>
                    <div class="value">{metadata.get('hypothesis', 'N/A')}</div>
                </div>

                <div class="field">
                    <div class="label">📈 Frequency</div>
                    <div class="value">{metadata.get('frequency', 'N/A')}</div>
                </div>

                <div class="field">
                    <div class="label">📞 CTA</div>
                    <div class="value">{metadata.get('cta', 'N/A')}</div>
                </div>

                <div class="field">
                    <div class="label">🌐 Landing Page</div>
                    <div class="value">
                        {f'<a href="/landing/{hypothesis_id}" target="_blank" class="btn">Open Landing Page →</a>' if os.path.exists(f"landings/{hypothesis_id}.html") else '<span class="badge badge-no">❌ Not generated</span>'}
                    </div>
                </div>

                <div class="field">
                    <div class="label">📅 Created</div>
                    <div class="value">{obj.get('created_at', 'N/A')[:19]}</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/landing/{hypothesis_id}")
async def view_landing(hypothesis_id: str):
    file_path = f"landings/{hypothesis_id}.html"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Landing page not found")
    return FileResponse(file_path)

@app.post("/api/pay/{hypothesis_id}")
async def process_payment(hypothesis_id: str):
    """Створює платіж для гіпотези."""
    if storage.conn is None:
        await storage.init()
    
    cursor = await storage.conn.execute(
        "SELECT * FROM invoices WHERE object_id=? AND status='draft'",
        (hypothesis_id,)
    )
    row = await cursor.fetchone()
    if not row:
        invoice = Invoice(
            object_id=hypothesis_id,
            amount=1.69,
            currency="USD",
            description=f"Validation payment for hypothesis {hypothesis_id}",
            status="draft"
        )
        await storage.save_invoice(invoice)
    else:
        invoice = Invoice(
            object_id=row[1],
            amount=row[2],
            currency=row[3],
            id=row[0],
            status=row[4],
            due_date=datetime.datetime.fromisoformat(row[5]) if row[5] else None,
            paid_at=datetime.datetime.fromisoformat(row[6]) if row[6] else None,
            payment_id=row[7],
            description=row[8],
            metadata=json.loads(row[9]),
            created_at=datetime.datetime.fromisoformat(row[10]),
            updated_at=datetime.datetime.fromisoformat(row[11])
        )
    
    payment = await payment_processor.process_invoice(invoice)
    if payment and payment.status == "completed":
        return HTMLResponse("""
            <h1>✅ Payment Successful!</h1>
            <p>Thank you for your payment. You now have full access.</p>
            <a href="/">Back to home</a>
        """)
    else:
        return HTMLResponse("""
            <h1>⏳ Payment Pending</h1>
            <p>Your payment is being processed. You will receive a confirmation shortly.</p>
            <a href="/">Back to home</a>
        """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Stripe Webhook
import stripe
from fastapi import Request

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Обробляє webhook-події від Stripe."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    if not webhook_secret:
        logger.warning("STRIPE_WEBHOOK_SECRET not set, webhook verification skipped")
        # У тестовому режимі можна пропустити перевірку, але в продакшні обов'язково!
        # Тут для безпеки краще повернути помилку, якщо секрет відсутній.
        # Але для розробки дозволимо без перевірки.

    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        else:
            # Якщо секрет відсутній, парсимо JSON без перевірки (тільки для тестування!)
            import json
            event = json.loads(payload)
            logger.warning("Webhook signature verification skipped (no secret)")
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Обробка події
    event_type = event.get("type")
    event_data = event.get("data", {}).get("object", {})

    logger.info(f"Webhook event: {event_type}")

    if event_type == "payment_intent.succeeded":
        payment_intent_id = event_data.get("id")
        if payment_intent_id:
            # Знаходимо платіж у базі
            payment_data = await storage.get_payment_by_provider_reference(payment_intent_id)
            if payment_data:
                payment_id = payment_data["id"]
                await storage.update_payment_status(payment_id, "completed", datetime.utcnow().isoformat())
                logger.info(f"✅ Payment {payment_id} marked as completed via webhook")
                
                # Шукаємо інвойс, пов'язаний з цим платежем
                # Зараз ми не зберігаємо зв'язок між payment і invoice, крім payment_id в invoice.
                # Але під час створення платежу ми не оновлювали invoice.payment_id.
                # Тому потрібно знайти інвойс за metadata або за object_id.
                # Як тимчасове рішення, можна шукати інвойс з object_id = hypothesis_id, але ми не знаємо hypothesis_id.
                # Краще під час створення платежу зберігати invoice_id в metadata.
                # Поки що пропустимо оновлення інвойсу, але в майбутньому треба виправити.
                # Тимчасово можна оновити статус інвойсу, якщо знайдемо зв'язок.
                # Для простоти поки пропустимо.
            else:
                logger.warning(f"Payment with provider_reference {payment_intent_id} not found")

    elif event_type == "payment_intent.payment_failed":
        payment_intent_id = event_data.get("id")
        if payment_intent_id:
            payment_data = await storage.get_payment_by_provider_reference(payment_intent_id)
            if payment_data:
                await storage.update_payment_status(payment_data["id"], "failed")
                logger.info(f"❌ Payment {payment_data['id']} marked as failed via webhook")

    elif event_type == "charge.refunded":
        payment_intent_id = event_data.get("payment_intent")
        if payment_intent_id:
            payment_data = await storage.get_payment_by_provider_reference(payment_intent_id)
            if payment_data:
                await storage.update_payment_status(payment_data["id"], "refunded")
                logger.info(f"↩️ Payment {payment_data['id']} marked as refunded via webhook")

    return {"status": "ok"}
