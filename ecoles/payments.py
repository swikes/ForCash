"""
Paiement en ligne par mobile money.

Principe de sécurité : on ne croit JAMAIS ce que le navigateur ou la
notification racontent. Un paiement n'est enregistré qu'après avoir
re-vérifié la transaction directement auprès de l'agrégateur, avec les
identifiants de l'école. L'argent arrive sur le compte marchand de l'école :
ScolaPay ne détient jamais les fonds (pas besoin d'agrément d'établissement
de paiement).

Pour ajouter un agrégateur (PayDunya, FedaPay, Wave Business…), écrire une
classe avec `start()` et `check()` puis l'ajouter à PROVIDERS.
"""
import json
import logging
import re
from dataclasses import dataclass

import requests
from django.conf import settings
from django.db import transaction
from django.urls import reverse

from .models import OnlineTransaction, Payment

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    """Erreur affichable au parent (message en français)."""


@dataclass
class CheckResult:
    status: str  # OnlineTransaction.PENDING / ACCEPTED / REFUSED
    amount: int | None = None
    provider_reference: str = ""
    raw: str = ""


class DemoProvider:
    """Simule un opérateur : sert aux démonstrations commerciales, sans argent réel."""

    code = "demo"
    min_amount = 100
    amount_step = 1

    def start(self, request, tx):
        return reverse("demo_checkout", args=[tx.reference])

    def check(self, tx):
        try:
            data = json.loads(tx.last_response or "{}")
        except ValueError:
            data = {}
        status = {
            "ACCEPTED": OnlineTransaction.ACCEPTED,
            "REFUSED": OnlineTransaction.REFUSED,
        }.get(data.get("demo_status"), OnlineTransaction.PENDING)
        return CheckResult(status, tx.amount, data.get("operator_id", ""), tx.last_response)


class CinetPayProvider:
    """
    API Checkout CinetPay v2 (https://docs.cinetpay.com).
    À valider avec de petits montants avant la mise en production : CinetPay
    fait évoluer son API ; si votre compte vous donne des clés « sk_live_… »,
    adaptez start()/check() à la nouvelle version.
    """

    code = "cinetpay"
    init_url = "https://api-checkout.cinetpay.com/v2/payment"
    check_url = "https://api-checkout.cinetpay.com/v2/payment/check"
    min_amount = 100
    amount_step = 5  # CinetPay exige un multiple de 5

    def __init__(self, school):
        self.school = school

    def _post(self, url, payload):
        try:
            response = requests.post(url, json=payload, timeout=settings.PAYMENT_HTTP_TIMEOUT)
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("CinetPay injoignable : %s", exc)
            raise PaymentError("Le service de paiement est momentanément indisponible. Réessayez.") from exc

    def start(self, request, tx):
        student = tx.enrollment.student
        description = re.sub(r"[^A-Za-z0-9 ]", " ", f"Scolarite {student.last_name} {tx.reference}")
        payload = {
            "apikey": self.school.cinetpay_api_key,
            "site_id": self.school.cinetpay_site_id,
            "transaction_id": tx.reference,
            "amount": tx.amount,
            "currency": self.school.currency,
            "description": " ".join(description.split())[:100],
            "notify_url": request.build_absolute_uri(reverse("cinetpay_notify")),
            "return_url": request.build_absolute_uri(reverse("payment_return", args=[tx.reference])),
            "channels": "MOBILE_MONEY",
            "lang": "fr",
            "metadata": str(tx.enrollment_id),
            "customer_name": student.parent_name or student.last_name,
            "customer_surname": student.first_name,
            "customer_phone_number": student.parent_phone,
        }
        data = self._post(self.init_url, payload)
        payment_url = (data.get("data") or {}).get("payment_url")
        if str(data.get("code")) != "201" or not payment_url:
            logger.warning("CinetPay a refusé l'initialisation %s : %s", tx.reference, data)
            raise PaymentError("Le paiement n'a pas pu être initialisé. Contactez l'école.")
        return payment_url

    def check(self, tx):
        data = self._post(
            self.check_url,
            {
                "apikey": self.school.cinetpay_api_key,
                "site_id": self.school.cinetpay_site_id,
                "transaction_id": tx.reference,
            },
        )
        details = data.get("data") or {}
        provider_status = str(details.get("status", "")).upper()
        if provider_status == "ACCEPTED":
            status = OnlineTransaction.ACCEPTED
        elif provider_status in {"REFUSED", "CANCELED", "CANCELLED", "EXPIRED", "FAILED"}:
            status = OnlineTransaction.REFUSED
        else:
            status = OnlineTransaction.PENDING
        try:
            amount = int(float(details.get("amount")))
        except (TypeError, ValueError):
            amount = None
        reference = str(details.get("operator_id") or details.get("payment_method") or "")
        return CheckResult(status, amount, reference[:120], json.dumps(data)[:5000])


def get_provider(school):
    if school.online_payment_provider == "demo":
        return DemoProvider()
    if school.online_payment_provider == "cinetpay" and school.cinetpay_api_key and school.cinetpay_site_id:
        return CinetPayProvider(school)
    return None


def refresh_transaction(tx):
    """
    Interroge l'agrégateur puis, si le paiement est confirmé, enregistre le
    paiement (une seule fois, même si la notification arrive en double).
    """
    if tx.status != OnlineTransaction.PENDING:
        return tx
    provider = get_provider(tx.school)
    if provider is None or provider.code != tx.provider:
        return tx
    result = provider.check(tx)  # appel réseau hors transaction SQL
    with transaction.atomic():
        tx = OnlineTransaction.objects.select_for_update().get(pk=tx.pk)
        if tx.status != OnlineTransaction.PENDING:
            return tx
        if result.raw:
            tx.last_response = result.raw
        if result.status == OnlineTransaction.ACCEPTED:
            if result.amount is not None and result.amount < tx.amount:
                logger.error("Montant incohérent pour %s : %s < %s", tx.reference, result.amount, tx.amount)
                tx.status = OnlineTransaction.REFUSED
            else:
                tx.payment = Payment.objects.create(
                    school=tx.school,
                    enrollment=tx.enrollment,
                    amount=tx.amount,
                    method=Payment.ONLINE,
                    reference=(result.provider_reference or tx.reference)[:80],
                    note=f"Paiement en ligne ({tx.provider}) — transaction {tx.reference}",
                )
                tx.status = OnlineTransaction.ACCEPTED
        elif result.status == OnlineTransaction.REFUSED:
            tx.status = OnlineTransaction.REFUSED
        if result.provider_reference:
            tx.provider_reference = result.provider_reference
        tx.save()
    return tx
