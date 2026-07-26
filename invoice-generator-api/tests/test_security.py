import pytest

from main import generate_invoice_html, generate_pdf_reportlab, required_secret


API_HEADERS = {"X-API-Key": "test-invoice-api-key-that-is-at-least-32-characters"}


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("post", "/invoices", {"client_name": "Private", "items": [{"description": "Work", "quantity": 1, "unit_price": 1}]}),
        ("get", "/invoices", None),
        ("get", "/invoices/1", None),
        ("get", "/invoices/1/html", None),
        ("get", "/invoices/1/pdf", None),
        ("put", "/invoices/1", {"status": "paid"}),
        ("delete", "/invoices/1", None),
    ],
)
def test_invoice_routes_reject_anonymous_requests(client, method, path, json):
    response = client.request(method, path, json=json)
    assert response.status_code == 401


def test_valid_key_allows_invoice_listing(client):
    response = client.get("/invoices", headers=API_HEADERS)
    assert response.status_code == 200
    assert response.json() == {"invoices": []}


def test_html_renderer_escapes_stored_fields():
    invoice_data = {
            "invoice": {
                "invoice_number": "INV-1",
                "issue_date": "2026-01-01",
                "due_date": None,
                "status": "draft",
                "client_name": "<script>alert(1)</script>",
                "client_email": None,
                "client_address": None,
                "currency": "USD",
                "subtotal": 1.0,
                "tax_rate": 0.0,
                "tax_amount": 0.0,
                "total_amount": 1.0,
                "notes": "<img src=x onerror=alert(1)>",
            },
            "items": [{"description": "<svg onload=alert(1)>", "quantity": 1, "unit_price": 1.0, "line_total": 1.0}],
        }
    html = generate_invoice_html(invoice_data)
    assert "<script>" not in html
    assert "<img src=x" not in html
    assert "<svg onload" not in html
    assert "&lt;script&gt;" in html
    assert generate_pdf_reportlab(invoice_data).startswith(b"%PDF")


def test_cors_preflight_allows_configured_origin_without_api_key(client):
    response = client.options(
        "/invoices",
        headers={
            "Origin": "https://billing.example",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-API-Key",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://billing.example"


def test_required_secret_fails_closed(monkeypatch):
    monkeypatch.delenv("MISSING_INVOICE_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="MISSING_INVOICE_SECRET"):
        required_secret("MISSING_INVOICE_SECRET", 32)


def test_required_secret_rejects_documented_placeholder(monkeypatch):
    monkeypatch.setenv("PLACEHOLDER_INVOICE_SECRET", "replace-with-at-least-32-random-characters")
    with pytest.raises(RuntimeError, match="PLACEHOLDER_INVOICE_SECRET"):
        required_secret("PLACEHOLDER_INVOICE_SECRET", 32)
