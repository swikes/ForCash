"""Écrans du personnel de l'école (direction et caisse)."""
import csv
from datetime import timedelta

import qrcode
import qrcode.image.svg
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

from . import finance
from .access import staff_required
from .forms import (
    CancelPaymentForm,
    ClassroomForm,
    EnrollmentTransferForm,
    FeeScheduleForm,
    ImportForm,
    InstallmentFormSet,
    PaymentForm,
    SchoolSettingsForm,
    SchoolYearForm,
    StaffCreateForm,
    StudentForm,
)
from .importer import import_students, template_csv
from .models import (
    Classroom,
    Enrollment,
    FeeSchedule,
    Installment,
    Payment,
    Reminder,
    SchoolYear,
    StaffMember,
)
from .utils import amount_in_words, format_amount, render_message, whatsapp_url

User = get_user_model()


# --------------------------------------------------------------------------
# Outils communs
# --------------------------------------------------------------------------


def year_enrollments(request):
    return Enrollment.objects.filter(year=request.year, student__school=request.school, is_active=True)


def get_enrollment(request, pk):
    return get_object_or_404(
        Enrollment.objects.select_related("student", "classroom", "year"),
        pk=pk,
        student__school=request.school,
    )


def qr_svg(url):
    image = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=6, border=2)
    return mark_safe(image.to_string(encoding="unicode"))


def reminder_message(request, enrollment, balance):
    school = request.school
    student = enrollment.student
    next_line = balance.next_line
    amount = balance.overdue or (next_line.remaining if next_line else balance.remaining)
    return render_message(
        school.reminder_template,
        {
            "parent": student.parent_name or "cher parent",
            "eleve": f"{student.first_name} {student.last_name}".strip(),
            "classe": enrollment.classroom.name,
            "montant": f"{format_amount(amount)} {school.currency_symbol}",
            "echeance": next_line.due_date.strftime("%d/%m/%Y") if next_line else "",
            "ecole": school.name,
            "lien": request.build_absolute_uri(reverse("parent_portal", args=[student.token])),
        },
    ), amount


def remaining_after(payment, balance):
    """Reste à payer juste après ce versement (et non à la date de réimpression)."""
    paid_until = (
        payment.enrollment.payments.valid()
        .filter(
            Q(paid_on__lt=payment.paid_on)
            | Q(paid_on=payment.paid_on, receipt_number__lte=payment.receipt_number)
        )
        .aggregate(s=Sum("amount"))["s"]
        or 0
    )
    return max(0, balance.total - paid_until)


def receipt_message(request, payment, balance):
    student = payment.enrollment.student
    school = request.school
    return (
        f"Bonjour {student.parent_name or 'cher parent'}, {school.name} confirme la réception de "
        f"{format_amount(payment.amount)} {school.currency_symbol} pour {student.first_name} "
        f"{student.last_name} ({payment.enrollment.classroom.name}). Reçu n° {payment.receipt_label}. "
        f"Reste à payer : {format_amount(remaining_after(payment, balance))} {school.currency_symbol}. "
        f"Reçu vérifiable ici : {request.build_absolute_uri(reverse('public_receipt', args=[payment.token]))}"
    )


# --------------------------------------------------------------------------
# Tableau de bord
# --------------------------------------------------------------------------


@staff_required
def dashboard(request):
    today = timezone.localdate()
    rows = finance.enrollments_with_balances(year_enrollments(request), today)
    totals = finance.Totals()
    by_class = {}
    for enrollment, balance in rows:
        totals.add(balance)
        by_class.setdefault(enrollment.classroom, finance.Totals()).add(balance)
    classes = sorted(by_class.items(), key=lambda item: (item[0].position, item[0].name))

    payments = Payment.objects.valid().filter(school=request.school, enrollment__year=request.year)
    today_total = payments.filter(paid_on=today).aggregate(s=Sum("amount"))["s"] or 0
    week_total = payments.filter(paid_on__gt=today - timedelta(days=7)).aggregate(s=Sum("amount"))["s"] or 0
    month_total = payments.filter(paid_on__year=today.year, paid_on__month=today.month).aggregate(
        s=Sum("amount")
    )["s"] or 0
    by_method = (
        payments.filter(paid_on__year=today.year, paid_on__month=today.month)
        .values("method")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )
    method_labels = dict(Payment.METHOD_CHOICES)
    next_installment = (
        Installment.objects.filter(schedule__year=request.year, due_date__gt=today).order_by("due_date").first()
    )
    return render(
        request,
        "ecoles/dashboard.html",
        {
            "totals": totals,
            "classes": classes,
            "today_total": today_total,
            "week_total": week_total,
            "month_total": month_total,
            "by_method": [
                {**row, "label": method_labels.get(row["method"], row["method"])} for row in by_method
            ],
            "recent_payments": payments.select_related("enrollment__student", "enrollment__classroom")[:8],
            "next_installment": next_installment,
            "reminders_this_week": Reminder.objects.filter(
                school=request.school, created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            "no_schedule": Classroom.objects.filter(year=request.year, schedule__isnull=True).count(),
        },
    )


# --------------------------------------------------------------------------
# Élèves
# --------------------------------------------------------------------------


@staff_required
def student_list(request):
    queryset = year_enrollments(request)
    classroom_id = request.GET.get("classe", "")
    status = request.GET.get("statut", "")
    query = request.GET.get("q", "").strip()
    if classroom_id.isdigit():
        queryset = queryset.filter(classroom_id=int(classroom_id))
    if query:
        queryset = queryset.filter(
            Q(student__last_name__icontains=query)
            | Q(student__first_name__icontains=query)
            | Q(student__matricule__icontains=query)
            | Q(student__parent_name__icontains=query)
            | Q(student__parent_phone__icontains=query)
        )
    rows = finance.enrollments_with_balances(queryset)
    if status:
        rows = [row for row in rows if row[1].status == status]
    rows.sort(key=lambda row: (row[0].classroom.position, row[0].classroom.name, row[0].student.last_name))

    if request.GET.get("format") == "csv":
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="eleves-soldes.csv"'
        response.write("﻿")
        writer = csv.writer(response, delimiter=";")
        writer.writerow(
            ["Matricule", "Nom", "Prénoms", "Classe", "Parent", "Téléphone",
             "Total dû", "Payé", "Exigible non payé", "Reste à payer", "Statut"]
        )
        for enrollment, balance in rows:
            student = enrollment.student
            writer.writerow(
                [student.matricule, student.last_name, student.first_name, enrollment.classroom.name,
                 student.parent_name, student.parent_phone, balance.total, balance.paid,
                 balance.overdue, balance.remaining, balance.status_label]
            )
        return response

    totals = finance.Totals()
    for _, balance in rows:
        totals.add(balance)
    return render(
        request,
        "ecoles/student_list.html",
        {
            "rows": rows,
            "totals": totals,
            "classrooms": Classroom.objects.filter(year=request.year),
            "filters": {"classe": classroom_id, "statut": status, "q": query},
            "querystring": request.GET.urlencode(),
        },
    )


@staff_required
def student_create(request):
    form = StudentForm(request.POST or None, school=request.school, year=request.year)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            student = form.save(commit=False)
            student.school = request.school
            student.save()
            enrollment = Enrollment.objects.create(
                student=student,
                year=request.year,
                classroom=form.cleaned_data["classroom"],
                discount=form.cleaned_data["discount"],
                discount_reason=form.cleaned_data["discount_reason"],
            )
        messages.success(request, f"{student.full_name} est inscrit(e) en {enrollment.classroom}.")
        if "encore" in request.POST:
            return redirect("student_create")
        return redirect("student_detail", pk=enrollment.pk)
    return render(request, "ecoles/student_form.html", {"form": form, "title": "Nouvel élève"})


@staff_required
def student_edit(request, pk):
    enrollment = get_enrollment(request, pk)
    form = StudentForm(
        request.POST or None,
        instance=enrollment.student,
        school=request.school,
        year=enrollment.year,
        enrollment=enrollment,
    )
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.save()
            enrollment.classroom = form.cleaned_data["classroom"]
            if request.staff.is_director:  # seule la direction accorde des remises et radie
                enrollment.discount = form.cleaned_data["discount"]
                enrollment.discount_reason = form.cleaned_data["discount_reason"]
                enrollment.is_active = form.cleaned_data["is_active"]
            enrollment.save()
        messages.success(request, "Fiche mise à jour.")
        return redirect("student_detail", pk=enrollment.pk)
    if not request.staff.is_director:
        for name in ("discount", "discount_reason", "is_active"):
            form.fields[name].disabled = True
    return render(
        request,
        "ecoles/student_form.html",
        {"form": form, "title": f"Modifier — {enrollment.student.full_name}", "enrollment": enrollment},
    )


@staff_required
def student_detail(request, pk):
    enrollment = get_enrollment(request, pk)
    balance = finance.balance_for(enrollment)
    message, reminder_amount = reminder_message(request, enrollment, balance)
    other_years = []
    for other in enrollment.student.enrollments.exclude(pk=enrollment.pk).select_related("year", "classroom"):
        other_years.append((other, finance.balance_for(other)))
    return render(
        request,
        "ecoles/student_detail.html",
        {
            "enrollment": enrollment,
            "student": enrollment.student,
            "balance": balance,
            "payments": enrollment.payments.select_related("recorded_by"),
            "reminders": enrollment.reminders.select_related("sent_by")[:10],
            "reminder_text": message,
            "reminder_amount": reminder_amount,
            "portal_url": request.build_absolute_uri(reverse("parent_portal", args=[enrollment.student.token])),
            "other_years": other_years,
        },
    )


# --------------------------------------------------------------------------
# Paiements, reçus, caisse
# --------------------------------------------------------------------------


@staff_required
def payment_create(request, pk):
    enrollment = get_enrollment(request, pk)
    balance = finance.balance_for(enrollment)
    initial = {"amount": balance.overdue or (balance.next_line.remaining if balance.next_line else None)}
    form = PaymentForm(
        request.POST or None,
        initial=initial,
        remaining=balance.remaining,
        currency_symbol=request.school.currency_symbol,
    )
    if request.method == "POST" and form.is_valid():
        payment = form.save(commit=False)
        payment.school = request.school
        payment.enrollment = enrollment
        payment.recorded_by = request.user
        payment.save()
        messages.success(request, f"Paiement enregistré — reçu n° {payment.receipt_label}.")
        return redirect("payment_receipt", pk=payment.pk)
    return render(
        request,
        "ecoles/payment_form.html",
        {"form": form, "enrollment": enrollment, "balance": balance},
    )


@staff_required
def payment_receipt(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related("enrollment__student", "enrollment__classroom", "enrollment__year", "recorded_by"),
        pk=pk,
        school=request.school,
    )
    balance = finance.balance_for(payment.enrollment)
    verify_url = request.build_absolute_uri(reverse("public_receipt", args=[payment.token]))
    student = payment.enrollment.student
    return render(
        request,
        "ecoles/receipt.html",
        {
            "payment": payment,
            "balance": balance,
            "remaining_after": remaining_after(payment, balance),
            "amount_words": amount_in_words(payment.amount, request.school.currency),
            "qr": qr_svg(verify_url),
            "verify_url": verify_url,
            "whatsapp_link": whatsapp_url(
                None if request.school.is_demo else student.whatsapp_phone,
                receipt_message(request, payment, balance),
            ),
            "cancel_form": CancelPaymentForm(),
            "staff_view": True,
        },
    )


@staff_required(director=True)
@require_POST
def payment_cancel(request, pk):
    payment = get_object_or_404(Payment, pk=pk, school=request.school)
    form = CancelPaymentForm(request.POST)
    if payment.is_cancelled:
        messages.info(request, "Ce paiement est déjà annulé.")
    elif form.is_valid():
        payment.cancel(request.user, form.cleaned_data["reason"])
        messages.warning(request, f"Reçu n° {payment.receipt_label} annulé.")
    else:
        messages.error(request, "Indiquez le motif de l'annulation.")
    return redirect("payment_receipt", pk=payment.pk)


@staff_required
def cash_journal(request):
    today = timezone.localdate()
    start = parse_date(request.GET.get("du", "")) or today
    end = parse_date(request.GET.get("au", "")) or start
    if end < start:
        start, end = end, start
    payments = (
        Payment.objects.filter(school=request.school, paid_on__range=(start, end))
        .select_related("enrollment__student", "enrollment__classroom", "recorded_by")
        .order_by("paid_on", "receipt_number")
    )
    method = request.GET.get("mode", "")
    if method:
        payments = payments.filter(method=method)
    cashier = request.GET.get("caisse", "")
    if cashier.isdigit():
        payments = payments.filter(recorded_by_id=int(cashier))
    valid = payments.valid()
    method_labels = dict(Payment.METHOD_CHOICES)
    by_method = [
        {**row, "label": method_labels.get(row["method"], row["method"])}
        for row in valid.values("method").annotate(total=Sum("amount"), count=Count("id")).order_by("-total")
    ]
    if request.GET.get("format") == "csv":
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="journal-caisse-{start}-{end}.csv"'
        response.write("﻿")
        writer = csv.writer(response, delimiter=";")
        writer.writerow(["Date", "Reçu", "Élève", "Classe", "Montant", "Mode", "Référence", "Saisi par", "Annulé"])
        for p in payments:
            writer.writerow(
                [p.paid_on.strftime("%d/%m/%Y"), p.receipt_label, p.enrollment.student.full_name,
                 p.enrollment.classroom.name, p.amount, p.get_method_display(), p.reference,
                 p.recorded_by.get_username() if p.recorded_by else "en ligne",
                 p.cancel_reason if p.is_cancelled else ""]
            )
        return response
    return render(
        request,
        "ecoles/cash_journal.html",
        {
            "payments": payments,
            "total": valid.aggregate(s=Sum("amount"))["s"] or 0,
            "by_method": by_method,
            "start": start,
            "end": end,
            "methods": Payment.METHOD_CHOICES,
            "cashiers": User.objects.filter(staff__school=request.school),
            "filters": {"mode": method, "caisse": cashier},
            "querystring": request.GET.urlencode(),
        },
    )


# --------------------------------------------------------------------------
# Relances
# --------------------------------------------------------------------------


@staff_required
def reminders(request):
    queryset = year_enrollments(request)
    classroom_id = request.GET.get("classe", "")
    if classroom_id.isdigit():
        queryset = queryset.filter(classroom_id=int(classroom_id))
    rows = [row for row in finance.enrollments_with_balances(queryset) if row[1].overdue > 0]
    rows.sort(key=lambda row: -row[1].overdue)
    last_reminders = {}
    for reminder in Reminder.objects.filter(school=request.school, enrollment__year=request.year).order_by(
        "created_at"
    ):
        last_reminders[reminder.enrollment_id] = reminder
    items = []
    for enrollment, balance in rows:
        items.append(
            {
                "enrollment": enrollment,
                "balance": balance,
                "phone_ok": bool(enrollment.student.whatsapp_phone),
                "last_reminder": last_reminders.get(enrollment.pk),
            }
        )
    return render(
        request,
        "ecoles/reminders.html",
        {
            "items": items,
            "total_overdue": sum(row[1].overdue for row in rows),
            "classrooms": Classroom.objects.filter(year=request.year),
            "classe": classroom_id,
        },
    )


@staff_required
@require_POST
def reminder_send(request, pk):
    """Journalise la relance puis ouvre WhatsApp avec le message prêt à envoyer."""
    enrollment = get_enrollment(request, pk)
    balance = finance.balance_for(enrollment)
    message, amount = reminder_message(request, enrollment, balance)
    channel = request.POST.get("canal", "whatsapp")
    if channel not in dict(Reminder.CHANNEL_CHOICES):
        channel = "whatsapp"
    Reminder.objects.create(
        school=request.school,
        enrollment=enrollment,
        channel=channel,
        amount_due=amount,
        message=message,
        sent_by=request.user,
    )
    if channel != "whatsapp":
        messages.success(request, "Relance notée.")
        return redirect(request.POST.get("next") or reverse("student_detail", args=[enrollment.pk]))
    phone = None if request.school.is_demo else enrollment.student.whatsapp_phone
    return redirect(whatsapp_url(phone, message))


# --------------------------------------------------------------------------
# Classes et barèmes
# --------------------------------------------------------------------------


@staff_required
def classes(request):
    classrooms = (
        Classroom.objects.filter(year=request.year)
        .select_related("schedule")
        .annotate(students=Count("enrollments", filter=Q(enrollments__is_active=True)))
    )
    schedules = FeeSchedule.objects.filter(year=request.year).prefetch_related("installments")
    return render(request, "ecoles/classes.html", {"classrooms": classrooms, "schedules": schedules})


@staff_required(director=True)
def classroom_edit(request, pk=None):
    classroom = get_object_or_404(Classroom, pk=pk, school=request.school) if pk else None
    form = ClassroomForm(request.POST or None, instance=classroom, year=classroom.year if classroom else request.year)
    if request.method == "POST" and form.is_valid():
        classroom = form.save(commit=False)
        classroom.school = request.school
        if not classroom.pk:
            classroom.year = request.year
        classroom.save()
        messages.success(request, f"Classe « {classroom.name} » enregistrée.")
        return redirect("classes")
    return render(
        request,
        "ecoles/simple_form.html",
        {"form": form, "title": "Modifier la classe" if classroom else "Nouvelle classe", "back": reverse("classes")},
    )


@staff_required(director=True)
def schedule_edit(request, pk=None):
    schedule = get_object_or_404(FeeSchedule, pk=pk, school=request.school) if pk else None
    form = FeeScheduleForm(request.POST or None, instance=schedule)
    formset = InstallmentFormSet(request.POST or None, instance=schedule or FeeSchedule())
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            schedule = form.save(commit=False)
            schedule.school = request.school
            if not schedule.pk:
                schedule.year = request.year
            schedule.save()
            formset.instance = schedule
            formset.save()
        messages.success(request, f"Barème « {schedule.name} » enregistré.")
        return redirect("classes")
    return render(
        request,
        "ecoles/schedule_form.html",
        {"form": form, "formset": formset, "schedule": schedule},
    )


# --------------------------------------------------------------------------
# Import
# --------------------------------------------------------------------------


@staff_required
def student_import(request):
    form = ImportForm(request.POST or None, request.FILES or None)
    report = None
    if request.method == "POST" and form.is_valid():
        upload = form.cleaned_data["file"]
        if upload.size > 5 * 1024 * 1024:
            form.add_error("file", "Fichier trop volumineux (5 Mo maximum).")
        else:
            report = import_students(
                upload.read(), request.school, request.year, form.cleaned_data["create_classes"]
            )
            if report.created or report.updated:
                messages.success(
                    request, f"Import terminé : {report.created} élève(s) ajouté(s), {report.updated} mis à jour."
                )
    return render(request, "ecoles/import.html", {"form": form, "report": report})


@staff_required(needs_year=False)
def import_template(request):
    response = HttpResponse(template_csv(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="modele-import-eleves.csv"'
    return response


# --------------------------------------------------------------------------
# Paramètres (direction)
# --------------------------------------------------------------------------


@staff_required(director=True, needs_year=False)
def school_settings(request):
    form = SchoolSettingsForm(request.POST or None, instance=request.school)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Paramètres enregistrés.")
        return redirect("school_settings")
    return render(
        request,
        "ecoles/settings.html",
        {
            "form": form,
            "staff_members": StaffMember.objects.filter(school=request.school).select_related("user"),
            "years": SchoolYear.objects.filter(school=request.school),
            "notify_url": request.build_absolute_uri(reverse("cinetpay_notify")),
        },
    )


@staff_required(director=True, needs_year=False)
def staff_create(request):
    form = StaffCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        with transaction.atomic():
            user = User.objects.create_user(
                username=data["username"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
            )
            StaffMember.objects.create(user=user, school=request.school, role=data["role"])
        messages.success(request, f"Compte « {user.username} » créé.")
        return redirect("school_settings")
    return render(
        request,
        "ecoles/simple_form.html",
        {"form": form, "title": "Ajouter un membre du personnel", "back": reverse("school_settings")},
    )


@staff_required(director=True, needs_year=False)
@require_POST
def staff_toggle(request, pk):
    member = get_object_or_404(StaffMember.objects.select_related("user"), pk=pk, school=request.school)
    if member.user == request.user:
        messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
    else:
        member.user.is_active = not member.user.is_active
        member.user.save(update_fields=["is_active"])
        state = "réactivé" if member.user.is_active else "désactivé"
        messages.success(request, f"Compte « {member.user.username} » {state}.")
    return redirect("school_settings")


def shift_year(day):
    try:
        return day.replace(year=day.year + 1)
    except ValueError:  # 29 février
        return day.replace(year=day.year + 1, day=28)


@staff_required(director=True, needs_year=False)
def year_create(request):
    form = SchoolYearForm(request.POST or None, school=request.school)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            year = form.save(commit=False)
            year.school = request.school
            year.save()
            source = form.cleaned_data.get("copy_from")
            if source:
                schedule_map = {}
                for schedule in source.schedules.prefetch_related("installments"):
                    copy = FeeSchedule.objects.create(school=request.school, year=year, name=schedule.name)
                    schedule_map[schedule.pk] = copy
                    Installment.objects.bulk_create(
                        Installment(schedule=copy, label=i.label, amount=i.amount, due_date=shift_year(i.due_date))
                        for i in schedule.installments.all()
                    )
                for classroom in source.classrooms.all():
                    Classroom.objects.create(
                        school=request.school,
                        year=year,
                        name=classroom.name,
                        position=classroom.position,
                        schedule=schedule_map.get(classroom.schedule_id),
                    )
            if form.cleaned_data.get("make_current") or request.school.current_year is None:
                year.make_current()
        messages.success(request, f"Année {year.name} créée.")
        return redirect("classes" if year.is_current else "school_settings")
    return render(
        request,
        "ecoles/simple_form.html",
        {"form": form, "title": "Nouvelle année scolaire", "back": reverse("school_settings")},
    )


@staff_required(director=True, needs_year=False)
@require_POST
def year_activate(request, pk):
    year = get_object_or_404(SchoolYear, pk=pk, school=request.school)
    year.make_current()
    messages.success(request, f"{year.name} est maintenant l'année en cours.")
    return redirect("school_settings")


@staff_required(director=True)
def reenroll(request):
    """Passage en classe supérieure : réinscrit en un clic les élèves d'une classe de l'an dernier."""
    previous_year = (
        SchoolYear.objects.filter(school=request.school, start_date__lt=request.year.start_date)
        .order_by("-start_date")
        .first()
    )
    if previous_year is None:
        messages.info(request, "Aucune année précédente : rien à réinscrire.")
        return redirect("classes")
    form = EnrollmentTransferForm(request.POST or None, previous_year=previous_year, current_year=request.year)
    if request.method == "POST" and form.is_valid():
        source, target = form.cleaned_data["source"], form.cleaned_data["target"]
        selected = set(request.POST.getlist("eleves"))
        created = 0
        for enrollment in source.enrollments.filter(is_active=True).select_related("student"):
            if str(enrollment.student_id) not in selected:
                continue
            _, was_created = Enrollment.objects.get_or_create(
                student=enrollment.student, year=request.year, defaults={"classroom": target}
            )
            created += was_created
        messages.success(request, f"{created} élève(s) réinscrit(s) en {target}.")
        return redirect(f"{reverse('reenroll')}?source={source.pk}")
    source_id = request.GET.get("source") or request.POST.get("source")
    candidates = []
    if source_id and str(source_id).isdigit():
        source = Classroom.objects.filter(pk=int(source_id), year=previous_year).first()
        if source:
            already = set(
                Enrollment.objects.filter(year=request.year, student__in=source.enrollments.values("student"))
                .values_list("student_id", flat=True)
            )
            for enrollment, balance in finance.enrollments_with_balances(source.enrollments.filter(is_active=True)):
                candidates.append(
                    {"enrollment": enrollment, "balance": balance, "done": enrollment.student_id in already}
                )
            form.fields["source"].initial = source
    return render(
        request,
        "ecoles/reenroll.html",
        {"form": form, "previous_year": previous_year, "candidates": candidates},
    )
