from app.tools import database_tools


def retrieve_case_data(entities: dict[str, str]) -> dict:
    order_id = entities.get("order_id")
    if not order_id:
        return {"errors": ["An order ID is required to access account-specific return data."], "order": None, "tool_call_log": []}
    order_result = database_tools.get_order(order_id)
    order = order_result["data"] if order_result["success"] else None
    if not order:
        error = order_result.get("error") or f"Order {order_id} was not found."
        return {"errors": [error], "order": None, "tool_call_log": [{"tool": "get_order", "status": "error", "error": error}]}
    customer_id = entities.get("customer_id") or order["customer_id"]
    entities["customer_id"] = customer_id
    item = order["items"][0] if order.get("items") else {}
    product_id = entities.get("product_id") or item.get("product_id")
    if product_id:
        entities["product_id"] = product_id
    return_id = f"RET{order_id.removeprefix('ORD')}"
    calls = [
        ("customer", "get_customer", database_tools.get_customer(customer_id)),
        ("return", "get_return_request", database_tools.get_return_request(return_id)),
        ("tracking", "get_tracking", database_tools.get_tracking(order_id)),
        ("payment", "get_payment", database_tools.get_payment(order_id)),
        ("inventory", "get_inventory", database_tools.get_inventory(product_id) if product_id else {"success": True, "data": None}),
        ("return_history", "get_customer_return_history", database_tools.get_customer_return_history(customer_id)),
        ("previous_cases", "get_previous_support_cases", database_tools.get_previous_support_cases(customer_id)),
    ]
    data = {"order": order}
    errors = []
    tool_call_log = [{"tool": "get_order", "status": "success"}]
    for key, tool_name, result in calls:
        if result["success"]:
            data[key] = result["data"]
        else:
            data[key] = None
            errors.append(result["error"])
        tool_call_log.append({"tool": tool_name, "status": "success" if result["success"] else "error", "error": result.get("error")})
    return {**data, "errors": errors, "tool_call_log": tool_call_log}