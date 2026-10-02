"""Outils sans dépendance : pays, monnaies, téléphones, montants en lettres."""
import re
import secrets
from urllib.parse import quote

# code ISO -> (nom, indicatif, longueur du numéro national, préfixe 0 à retirer ?)
# Le « 0 » initial fait partie du numéro en Côte d'Ivoire, au Bénin et au Congo :
# il est conservé dans le format international (+225 07 07 07 07 07).
COUNTRIES = {
    "CI": ("Côte d'Ivoire", "225", 10, False),
    "SN": ("Sénégal", "221", 9, False),
    "CM": ("Cameroun", "237", 9, False),
    "BJ": ("Bénin", "229", 10, False),
    "TG": ("Togo", "228", 8, False),
    "BF": ("Burkina Faso", "226", 8, False),
    "ML": ("Mali", "223", 8, False),
    "NE": ("Niger", "227", 8, False),
    "GN": ("Guinée", "224", 9, False),
    "CG": ("Congo-Brazzaville", "242", 9, False),
    "CD": ("RD Congo", "243", 9, True),
    "MG": ("Madagascar", "261", 9, True),
}
COUNTRY_CHOICES = [(code, data[0]) for code, data in COUNTRIES.items()]

# code ISO 4217 -> (symbole affiché, libellé en toutes lettres au pluriel)
CURRENCIES = {
    "XOF": ("FCFA", "francs CFA"),
    "XAF": ("FCFA", "francs CFA"),
    "GNF": ("GNF", "francs guinéens"),
    "CDF": ("FC", "francs congolais"),
    "MGA": ("Ar", "ariary"),
    "USD": ("USD", "dollars"),
}
CURRENCY_CHOICES = [(code, f"{code} ({data[0]})") for code, data in CURRENCIES.items()]

DEFAULT_CURRENCY_BY_COUNTRY = {
    "CI": "XOF", "SN": "XOF", "BJ": "XOF", "TG": "XOF", "BF": "XOF", "ML": "XOF", "NE": "XOF",
    "CM": "XAF", "CG": "XAF", "GN": "GNF", "CD": "CDF", "MG": "MGA",
}


def new_token():
    """Jeton public non devinable (liens parents, reçus)."""
    return secrets.token_urlsafe(18)


def new_reference():
    """Référence de transaction alphanumérique, acceptée par les agrégateurs."""
    return "SP" + secrets.token_hex(10).upper()


def format_amount(value):
    """12500 -> '12 500' (espace fine insécable comme séparateur de milliers)."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return str(value)
    sign = "-" if value < 0 else ""
    return sign + f"{abs(value):,}".replace(",", " ")


def normalize_phone(raw, country="CI"):
    """
    Convertit un numéro saisi librement en format international sans « + »
    (ex. '07 07 07 07 07' -> '2250707070707'), utilisable dans un lien wa.me.
    Renvoie None si le numéro ne correspond pas au plan de numérotation.
    """
    if not raw:
        return None
    raw = str(raw).strip()
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return None
    _, dial, length, trunk_zero = COUNTRIES.get(country, COUNTRIES["CI"])
    if raw.startswith("+") or digits.startswith("00"):
        digits = digits[2:] if digits.startswith("00") else digits
        return digits if 8 <= len(digits) <= 15 else None
    if digits.startswith(dial) and len(digits) == len(dial) + length:
        return digits
    if len(digits) == length:
        return dial + digits
    if trunk_zero and digits.startswith("0") and len(digits) == length + 1:
        return dial + digits[1:]
    return None


def whatsapp_url(phone, message):
    """Lien « clic pour discuter » : ouvre WhatsApp avec le message pré-rempli."""
    text = quote(message, safe="")
    if phone:
        return f"https://wa.me/{phone}?text={text}"
    # Sans numéro valide, WhatsApp propose de choisir le contact.
    return f"https://wa.me/?text={text}"


def render_message(template, values):
    """Remplace {cle} par sa valeur ; les clés inconnues restent telles quelles."""
    return re.sub(
        r"\{(\w+)\}",
        lambda match: str(values.get(match.group(1), match.group(0))),
        template,
    )


_UNITS = [
    "zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
    "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize",
    "dix-sept", "dix-huit", "dix-neuf",
]
_TENS = {2: "vingt", 3: "trente", 4: "quarante", 5: "cinquante", 6: "soixante"}


def _below_100(n):
    if n < 20:
        return _UNITS[n]
    tens, unit = divmod(n, 10)
    if tens in (7, 9):  # soixante-dix…, quatre-vingt-dix…
        base = "soixante" if tens == 7 else "quatre-vingt"
        rest = 10 + unit
        if tens == 7 and unit == 1:
            return "soixante et onze"
        return f"{base}-{_UNITS[rest]}"
    if tens == 8:
        return "quatre-vingts" if unit == 0 else f"quatre-vingt-{_UNITS[unit]}"
    word = _TENS[tens]
    if unit == 0:
        return word
    if unit == 1:
        return f"{word} et un"
    return f"{word}-{_UNITS[unit]}"


def _below_1000(n):
    hundreds, rest = divmod(n, 100)
    parts = []
    if hundreds == 1:
        parts.append("cent")
    elif hundreds > 1:
        parts.append(f"{_UNITS[hundreds]} cent{'s' if rest == 0 else ''}")
    if rest:
        parts.append(_below_100(rest))
    return " ".join(parts)


def number_to_french(n):
    """
    Écrit un entier en toutes lettres (orthographe traditionnelle), comme sur
    les reçus : 250000 -> 'deux cent cinquante mille'.
    """
    n = int(n)
    if n < 0:
        return "moins " + number_to_french(-n)
    if n == 0:
        return "zéro"
    parts = []
    for value, singular, plural in ((10**9, "milliard", "milliards"), (10**6, "million", "millions")):
        count, n = divmod(n, value)
        if count:
            parts.append(f"{number_to_french(count)} {singular if count == 1 else plural}")
    thousands, n = divmod(n, 1000)
    if thousands == 1:
        parts.append("mille")
    elif thousands > 1:
        # « vingt » et « cent » restent invariables devant « mille ».
        words = _below_1000(thousands)
        if words.endswith("cents"):
            words = words[:-1]
        if words.endswith("quatre-vingts"):
            words = words[:-1]
        parts.append(f"{words} mille")
    if n:
        parts.append(_below_1000(n))
    return " ".join(parts)


def amount_in_words(amount, currency="XOF"):
    label = CURRENCIES.get(currency, CURRENCIES["XOF"])[1]
    words = number_to_french(amount)
    if amount in (0, 1):
        label = label.replace("francs", "franc").replace("dollars", "dollar")
    # « un million de francs », mais « un million deux cent mille francs ».
    if words.endswith(("million", "millions", "milliard", "milliards")):
        return f"{words} de {label}"
    return f"{words} {label}"
