import pytest
from fastapi.testclient import TestClient
from app import api
from cargar_csv import load_fixture


@pytest.fixture(autouse=True)
def datos_limpios():
    """Recarga los pedidos antes de cada prueba."""
    api.orders.clear()
    api.orders.update(load_fixture())


client = TestClient(api.app)


def test_pedido_inexistente_404():
    response = client.post("/orders/NOEXISTE/confirm")
    assert response.status_code == 404


def test_confirmar_pedido_200():
    response = client.post("/orders/O013/confirm")
    assert response.status_code == 200
    assert response.json()["status"] == "CONFIRMED"


def test_confirmar_dos_veces_409():
    client.post("/orders/O013/confirm")
    response = client.post("/orders/O013/confirm")
    assert response.status_code == 409


def test_confirmar_sin_articulos_422():
    response = client.post("/orders/O007/confirm")
    assert response.status_code == 422


def test_enviar_sin_guia_422():
    client.post("/orders/O012/confirm")
    response = client.post("/orders/O012/ship", json={"tracking_number": ""})
    assert response.status_code == 422


def test_cancelar_desde_shipped_409():
    client.post("/orders/O014/confirm")
    client.post("/orders/O014/ship", json={"tracking_number": "GUIA123"})
    response = client.post("/orders/O014/cancel", json={"reason": "Cliente lo pidió"})
    assert response.status_code == 409


def test_consultar_pedido_200():
    response = client.get("/orders/O001")
    assert response.status_code == 200
    assert response.json()["id"] == "O001"