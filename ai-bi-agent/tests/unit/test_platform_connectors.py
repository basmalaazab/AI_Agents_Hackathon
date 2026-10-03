"""Tests for HubSpot and Stripe response normalization and pagination."""
from types import SimpleNamespace

from app.connectors import hubspot_connector, stripe_connector
from app.connectors.hubspot_connector import HubSpotConnector
from app.connectors.stripe_connector import StripeConnector


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        pass

    def json(self):
        return self.body


def test_hubspot_fetch_maps_contacts_and_follows_cursor(monkeypatch):
    monkeypatch.setattr(
        hubspot_connector,
        "get_settings",
        lambda: SimpleNamespace(hubspot_access_token="hubspot-test-token"),
    )
    requests = []

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, url, headers, params):
            requests.append((url, headers, dict(params)))
            if "after" not in params:
                return FakeResponse(
                    {
                        "results": [
                            {
                                "id": "42",
                                "properties": {
                                    "email": "alex@example.com",
                                    "firstname": "Alex",
                                    "lastname": "Rivers",
                                    "phone": "+15550000000",
                                    "city": "Cairo",
                                    "country": "EG",
                                },
                            }
                        ],
                        "paging": {"next": {"after": "43"}},
                    }
                )
            return FakeResponse({"results": [], "paging": {}})

    monkeypatch.setattr(hubspot_connector.httpx, "Client", FakeClient)
    records = HubSpotConnector("hubspot_main").fetch("customer")

    assert records[0]["customer_id"] == "42"
    assert records[0]["email"] == "alex@example.com"
    assert requests[1][2]["after"] == "43"
    assert requests[0][1]["Authorization"] == "Bearer hubspot-test-token"


def test_stripe_fetch_maps_payment_intents_and_follows_cursor(monkeypatch):
    monkeypatch.setattr(
        stripe_connector,
        "get_settings",
        lambda: SimpleNamespace(stripe_secret_key="sk_test_example"),
    )
    requests = []

    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["auth"] == ("sk_test_example", "")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, url, params):
            requests.append((url, dict(params)))
            if "starting_after" not in params:
                return FakeResponse(
                    {
                        "data": [
                            {
                                "id": "pi_paid",
                                "created": 1700000000,
                                "amount": 1250,
                                "amount_received": 1250,
                                "currency": "usd",
                                "customer": "cus_1",
                                "status": "succeeded",
                            },
                            {
                                "id": "pi_pending",
                                "created": 1700000001,
                                "amount": 500,
                                "amount_received": 0,
                                "currency": "usd",
                                "customer": None,
                                "status": "processing",
                            },
                            {
                                "id": "pi_refunded",
                                "created": 1700000002,
                                "amount": 2500,
                                "amount_received": 2500,
                                "currency": "usd",
                                "customer": "cus_2",
                                "status": "succeeded",
                                "latest_charge": {
                                    "amount_refunded": 2500,
                                    "refunded": True,
                                },
                            },
                        ],
                        "has_more": True,
                    }
                )
            return FakeResponse({"data": [], "has_more": False})

    monkeypatch.setattr(stripe_connector.httpx, "Client", FakeClient)
    records = StripeConnector("stripe_main").fetch("order")

    assert len(records) == 2
    assert records[0]["order_id"] == "pi_paid"
    assert records[0]["total_amount"] == "12.50"
    assert records[0]["customer_id"] == "cus_1"
    assert records[1]["status"] == "refunded"
    assert records[1]["total_amount"] == "0.00"
    assert requests[1][1]["starting_after"] == "pi_refunded"


def test_stripe_maps_product_default_price():
    product = StripeConnector._map_product(
        {
            "id": "prod_1",
            "name": "Starter",
            "description": "Monthly plan",
            "default_price": {
                "unit_amount": 999,
                "currency": "usd",
            },
        }
    )

    assert product["product_id"] == "prod_1"
    assert product["unit_price"] == "9.99"
    assert product["currency"] == "USD"
