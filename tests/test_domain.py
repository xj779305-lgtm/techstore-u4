import pytest
from decimal import Decimal
from app.domain import (
    Money, OrderItem, OrderStatus,
    InvalidOrderData, InvalidOrderTransition, OrderItemLimitExceeded,
)
from app.specifications import ten_percent, five_percent, discount_rate
from cargar_csv import load_fixture


def test_money_negativo():
    with pytest.raises(InvalidOrderData):
        Money(Decimal("-1"))


def test_pedido_o001_inicia_draft():
    orders = load_fixture()
    assert orders["O001"].status.value == "DRAFT"
    assert orders["O001"].units == 4
    assert orders["O001"].total.amount == Decimal("2100.00")


def test_21_unidades_rechazadas():
    orders = load_fixture()
    order = orders["O009"]                       # ya tiene 19 unidades
    with pytest.raises(OrderItemLimitExceeded):
        order.add_item(OrderItem("SKU003", 2, Money(Decimal("120.00"))))
    assert order.units == 19                     # no se modificó


def test_20_unidades_exactas_permitidas():
    orders = load_fixture()
    order = orders["O008"]
    order.confirm()
    assert order.units == 20
    assert order.status == OrderStatus.CONFIRMED


def test_cliente_inactivo_no_confirma():
    orders = load_fixture()
    order = orders["O003"]
    with pytest.raises(InvalidOrderData):
        order.confirm()
    assert order.status == OrderStatus.DRAFT
    assert order.events == []


def test_pedido_vacio_no_confirma():
    orders = load_fixture()
    order = orders["O007"]
    with pytest.raises(InvalidOrderData):
        order.confirm()
    assert order.events == []


def test_descuento_vip_10_por_ciento():
    orders = load_fixture()
    order = orders["O001"]
    assert ten_percent.is_satisfied_by(order)
    assert discount_rate(order) == Decimal("0.10")


def test_promocion_activa_bloquea_descuento():
    orders = load_fixture()
    order = orders["O005"]
    assert not ten_percent.is_satisfied_by(order)
    assert not five_percent.is_satisfied_by(order)
    assert discount_rate(order) == Decimal("0")


def test_umbral_500_es_estricto():
    orders = load_fixture()
    order = orders["O010"]
    assert order.total.amount == Decimal("500.00")
    assert not ten_percent.is_satisfied_by(order)


def test_envio_sin_guia_rechazado():
    orders = load_fixture()
    order = orders["O012"]
    order.confirm()
    with pytest.raises(InvalidOrderData):
        order.ship("")
    assert order.status == OrderStatus.CONFIRMED
    assert [e.name for e in order.events] == ["OrderConfirmed"]


def test_confirmacion_doble_no_duplica_evento():
    orders = load_fixture()
    order = orders["O013"]
    order.confirm()
    with pytest.raises(InvalidOrderTransition):
        order.confirm()
    assert [e.name for e in order.events] == ["OrderConfirmed"]


def test_cancelar_desde_shipped_rechazado():
    orders = load_fixture()
    order = orders["O014"]
    order.confirm()
    order.ship("GUIA123")
    with pytest.raises(InvalidOrderTransition):
        order.cancel("Cliente lo pidió")
    assert order.status == OrderStatus.SHIPPED


def test_entrega_y_devolucion_validas():
    orders = load_fixture()
    entregado = orders["O016"]
    entregado.confirm()
    entregado.ship("GUIA123")
    entregado.deliver()
    assert entregado.status == OrderStatus.DELIVERED

    devuelto = orders["O015"]
    devuelto.confirm()
    devuelto.ship("GUIA123")
    devuelto.return_order()
    assert devuelto.status == OrderStatus.RETURNED

def test_cliente_no_vip_sin_descuento():
    orders = load_fixture()
    order = orders["O002"]
    assert not order.customer.is_vip
    assert not ten_percent.is_satisfied_by(order)
    assert not five_percent.is_satisfied_by(order)
    assert discount_rate(order) == Decimal("0")


def test_descuento_5_por_ciento():
    orders = load_fixture()
    order = orders["O006"]
    assert order.total.amount == Decimal("18000.00")
    assert not ten_percent.is_satisfied_by(order)
    assert five_percent.is_satisfied_by(order)
    assert discount_rate(order) == Decimal("0.05")


def test_menos_de_4_unidades_sin_descuento_10():
    orders = load_fixture()
    order = orders["O011"]
    assert order.units == 3
    assert not ten_percent.is_satisfied_by(order)
    assert discount_rate(order) == Decimal("0")