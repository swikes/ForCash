"""
Pages publiques, sans connexion : portail parent, vérification de reçu et
paiement en ligne. L'accès se fait par un jeton aléatoire non devinable,
envoyé au parent par WhatsApp.
"""
import json
import logging

from django.contrib import messages
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import finance
from .forms import OnlinePaymentForm
from .models import OnlineTransaction, Payment, Student
from .payments import PaymentError, get_provider, refresh_transaction
from .utils import amount_in_words

logger = logging.getLogger(__name__)


def noindex(response):
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


def portal_context(student):
    school = student.school
    year = school.current_year
    enrollment = student.enrollments.filter(year=year).select_related("classroom", "year").first() if year else None
    balance = finance.balance_for(enrollment) if enrollment else None
    previous = []
    for other in student.enrollments.exclude(pk=getattr(enrollment, "pk", None)).select_related("year", "classroom"):
        other_balance = finance.balance_for(other)
        if other_balance.remaining > 0:
            previous.append((other, other_balance))
    return school, enrollment, balance, previous


def parent_portal(request, token):
    student = get_object_or_404(Student.objects.select_related("school"), token=token, school__is_active=True)
    school, enrollment, balance, previous = portal_context(student)
    provider = get_provider(school)
    form = None
    if provider and enrollment and balance and balance.remaining > 0:
        suggested = balance.overdue or (balance.next_line.remaining if balance.next_line else balance.remaining)
        form = OnlinePaymentForm(
            initial={"amount": suggested},
            remaining=balance.remaining,
            min_amount=provider.min_amount,
            step=provider.amount_step,
        )
    payments = enrollment.payments.valid() if enrollment else Payment.objects.none()
    return noindex(
        render(
            request,
            "ecoles/parent_portal.html",
            {
                "student": student,
                "school": school,
                "enrollment": enrollment,
                "balance": balance,
                "previous": previous,
                "payments": payments,
                "form": form,
            },
        )
    )


@require_POST
def parent_pay(request, token):
    student = get_object_or_404(Student.objects.select_related("school"), token=token, school__is_active=True)
    school, enrollment, balance, _ = portal_context(student)
    provider = get_provider(school)
    if not (provider and enrollment and balance and balance.remaining > 0):
        messages.error(request, "Le paiement en ligne n'est pas disponible.")
        return redirect("parent_portal", token=token)
    form = OnlinePaymentForm(
        request.POST, remaining=balance.remaining, min_amount=provider.min_amount, step=provider.amount_step
    )
    if not form.is_valid():
        for error in form.errors.get("amount", []):
            messages.error(request, error)
        return redirect("parent_portal", token=token)
    tx = OnlineTransaction.objects.create(
        school=school, enrollment=enrollment, provider=provider.code, amount=form.cleaned_data["amount"]
    )
    try:
        return redirect(provider.start(request, tx))
    except PaymentError as error:
        tx.status = OnlineTransaction.REFUSED
        tx.save(update_fields=["status", "updated_at"])
        messages.error(request, str(error))
        return redirect("parent_portal", token=token)


def payment_return(request, reference):
    """Retour du parent après paiement : on revérifie le statut auprès de l'agrégateur."""
    tx = get_object_or_404(OnlineTransaction.objects.select_related("school", "enrollment__student"), reference=reference)
    try:
        tx = refresh_transaction(tx)
    except PaymentError as error:
        messages.warning(request, str(error))
    return noindex(render(request, "ecoles/payment_return.html", {"tx": tx, "school": tx.school}))


def demo_checkout(request, reference):
    """Fausse page d'opérateur pour les démonstrations commerciales."""
    tx = get_object_or_404(
        OnlineTransaction.objects.select_related("school", "enrollment__student"), reference=reference, provider="demo"
    )
    if tx.school.online_payment_provider != "demo":
        raise Http404
    if request.method == "POST" and tx.status == OnlineTransaction.PENDING:
        accepted = request.POST.get("action") == "valider"
        tx.last_response = json.dumps(
            {"demo_status": "ACCEPTED" if accepted else "REFUSED", "operator_id": f"DEMO-{tx.pk:06d}"}
        )
        tx.save(update_fields=["last_response", "updated_at"])
        return redirect("payment_return", reference=tx.reference)
    return noindex(render(request, "ecoles/demo_checkout.html", {"tx": tx, "school": tx.school}))


@csrf_exempt
def cinetpay_notify(request):
    """
    Notification serveur à serveur de CinetPay. On ne lit que l'identifiant de
    transaction, puis on revérifie le statut via l'API (jamais de confiance
    aveugle dans le contenu reçu).
    """
    if request.method != "POST":
        return HttpResponse("OK")  # CinetPay teste la disponibilité de l'URL
    reference = request.POST.get("cpm_trans_id", "").strip()
    if not reference:
        return HttpResponseBadRequest("cpm_trans_id manquant")
    tx = OnlineTransaction.objects.select_related("school").filter(reference=reference, provider="cinetpay").first()
    if tx is None:
        logger.warning("Notification CinetPay pour une transaction inconnue : %s", reference)
        return HttpResponse("OK")
    site_id = request.POST.get("cpm_site_id", "").strip()
    if site_id and site_id != tx.school.cinetpay_site_id:
        logger.warning("site_id inattendu pour %s : %s", reference, site_id)
        return HttpResponseBadRequest("site_id invalide")
    try:
        refresh_transaction(tx)
    except PaymentError:
        return HttpResponse("RETRY", status=503)
    return HttpResponse("OK")


def public_receipt(request, token):
    payment = get_object_or_404(
        Payment.objects.select_related("school", "enrollment__student", "enrollment__classroom", "enrollment__year"),
        token=token,
    )
    return noindex(
        render(
            request,
            "ecoles/receipt.html",
            {
                "payment": payment,
                "school": payment.school,
                "amount_words": amount_in_words(payment.amount, payment.school.currency),
                "staff_view": False,
                "portal_url": reverse("parent_portal", args=[payment.enrollment.student.token]),
            },
        )
    )
