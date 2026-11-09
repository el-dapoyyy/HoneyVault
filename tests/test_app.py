"""Pengujian integrasi aplikasi: rute dan alur utama.

Pengujian ini memakai Flask test client sehingga tidak memerlukan server yang
berjalan.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from honeyvault import create_app
from honeyvault import storage


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def restore_dataset():
    """Memastikan pengujian tidak mengubah dataset aktif."""
    original = storage.load_customers()
    yield
    storage.save_customers(original)


def test_dashboard_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Dashboard pelanggan" in response.data


def test_simulation_page_renders(client):
    response = client.get("/simulation")
    assert response.status_code == 200
    assert b"Adaptive Decoy" in response.data


def test_evaluation_page_renders(client):
    response = client.get("/evaluation")
    assert response.status_code == 200
    assert b"Evaluasi kuantitatif" in response.data


def test_post_simulation_generates_decoys(client):
    response = client.post("/simulation", data={"method": "adaptive", "count": "5"})
    assert response.status_code == 200
    assert b"DEC-001" in response.data


def test_post_evaluation_reports_metrics(client):
    response = client.post("/evaluation", data={"count": "20", "seed": "42"})
    assert response.status_code == 200
    assert b"Wasserstein" in response.data


def test_add_customer_redirects_and_adds_row(client):
    before = len(storage.load_customers())
    response = client.post("/customers/add", data={
        "name": "Pelanggan Uji",
        "category": "Premium",
        "balance": "5000000",
    })
    assert response.status_code == 302
    assert len(storage.load_customers()) == before + 1


def test_add_customer_rejects_invalid_category(client):
    before = len(storage.load_customers())
    client.post("/customers/add", data={
        "name": "Pelanggan Uji",
        "category": "SuperPremium",
        "balance": "5000000",
    })
    assert len(storage.load_customers()) == before


def test_add_customer_rejects_non_numeric_balance(client):
    before = len(storage.load_customers())
    client.post("/customers/add", data={
        "name": "Pelanggan Uji",
        "category": "Premium",
        "balance": "bukan-angka",
    })
    assert len(storage.load_customers()) == before


def test_add_customer_rejects_negative_balance(client):
    before = len(storage.load_customers())
    client.post("/customers/add", data={
        "name": "Pelanggan Uji",
        "category": "Premium",
        "balance": "-5000",
    })
    assert len(storage.load_customers()) == before


def test_reset_restores_seed_dataset(client):
    storage.save_customers([{"id": "C001", "name": "X", "category": "Regular", "balance": 1}])
    client.post("/customers/reset")
    assert len(storage.load_customers()) == 8
