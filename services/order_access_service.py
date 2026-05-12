from services.order_service import get_order_by_id, get_order_detail, cancel_order


def get_customer_order_by_id(customer_id: int, order_id: int) -> dict:
    result = get_order_by_id(order_id)

    if not result.get("success"):
        return result

    order = result["data"]

    if order.get("customer_id") != customer_id:
        return {
            "success": False,
            "message": "Bu siparişi görüntüleme yetkiniz yok."
        }

    return result


def get_customer_order_detail(customer_id: int, order_id: int) -> dict:
    result = get_order_detail(order_id)

    if not result.get("success"):
        return result

    order = result["data"]

    if order.get("customer_id") != customer_id:
        return {
            "success": False,
            "message": "Bu sipariş detayını görüntüleme yetkiniz yok."
        }

    return result


def cancel_customer_order(customer_id: int, order_id: int) -> dict:
    result = get_order_by_id(order_id)

    if not result.get("success"):
        return result

    order = result["data"]

    if order.get("customer_id") != customer_id:
        return {
            "success": False,
            "message": "Bu siparişi iptal etme yetkiniz yok."
        }

    return cancel_order(order_id)