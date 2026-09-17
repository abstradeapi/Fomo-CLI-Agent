from decimal import Decimal, InvalidOperation


def decimal_value(value):
    try:
        return Decimal(str(value or 0))
    except InvalidOperation:
        return Decimal(0)


def normalize_positions(payload):
    positions = {}
    for item in payload.get("balances", []):
        balance = item.get("balance") or {}
        token_result = item.get("tokenFilterResult") or {}
        token = token_result.get("token") or {}
        user_token = item.get("userToken") or {}
        valuation = item.get("valuation") or {}
        address = balance.get("tokenAddress") or token.get("address")
        network_id = token.get("networkId") or user_token.get("networkId")
        if not address or network_id is None:
            continue
        amount = decimal_value(balance.get("shiftedBalance"))
        price = decimal_value(token_result.get("priceUSD"))
        key = f"{network_id}:{address}"
        positions[key] = {
            "networkId": network_id,
            "tokenAddress": address,
            "symbol": token.get("symbol") or (token.get("info") or {}).get("symbol") or "Unknown",
            "amount": str(amount),
            "priceUsd": str(price),
            "valueUsd": str(amount * price),
            "costBasisUsd": str(decimal_value(user_token.get("currentCostBasisUsd"))),
            "realizedPnlUsd": str(decimal_value(user_token.get("currentRealizedPnlUsd"))),
            "includeInEquity": valuation.get("includeInEquity", True),
        }
    return positions


def compare_positions(previous, current):
    changes = {"opened": [], "increased": [], "reduced": [], "closed": []}
    for key in set(previous) | set(current):
        old = previous.get(key)
        new = current.get(key)
        old_amount = decimal_value(old.get("amount")) if old else Decimal(0)
        new_amount = decimal_value(new.get("amount")) if new else Decimal(0)
        if old_amount <= 0 < new_amount:
            changes["opened"].append({"position": new, "change": str(new_amount)})
        elif old_amount > 0 >= new_amount:
            changes["closed"].append({"position": old, "change": str(old_amount)})
        elif new_amount > old_amount:
            changes["increased"].append({"position": new, "change": str(new_amount - old_amount)})
        elif new_amount < old_amount:
            changes["reduced"].append({"position": new or old, "change": str(old_amount - new_amount)})
    return changes
