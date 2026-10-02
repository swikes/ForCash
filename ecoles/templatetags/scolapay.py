from django import template

from ..utils import format_amount

register = template.Library()


@register.filter
def money(value, symbol="FCFA"):
    """{{ montant|money:school.currency_symbol }} -> « 125 000 FCFA »."""
    return f"{format_amount(value)} {symbol}" if symbol else format_amount(value)


@register.filter
def amount(value):
    return format_amount(value)


@register.filter
def percent_of(value, total):
    try:
        return min(100, round(100 * int(value) / int(total))) if int(total) else 0
    except (TypeError, ValueError):
        return 0
