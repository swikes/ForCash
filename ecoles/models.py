from django.conf import settings
from django.db import models, transaction
from django.db.models import F
from django.utils import timezone

from .utils import (
    COUNTRY_CHOICES,
    CURRENCIES,
    CURRENCY_CHOICES,
    new_reference,
    new_token,
    normalize_phone,
)

DEFAULT_REMINDER_TEMPLATE = (
    "Bonjour {parent}, sauf erreur de notre part, un montant de {montant} reste à régler "
    "pour la scolarité de {eleve} ({classe}), échéance du {echeance}. "
    "Détail et paiement : {lien} . Merci pour votre confiance. — {ecole}"
)


class School(models.Model):
    PLAN_ESSENTIAL = "essentiel"
    PLAN_RECOVERY = "recouvrement"
    PLAN_CHOICES = [
        (PLAN_ESSENTIAL, "Essentiel"),
        (PLAN_RECOVERY, "Recouvrement+"),
    ]
    PROVIDER_CHOICES = [
        ("", "Désactivé (paiement direct sur vos numéros marchands)"),
        ("demo", "Démonstration (aucun argent réel)"),
        ("cinetpay", "CinetPay (Orange, MTN, Moov, Wave…)"),
    ]

    name = models.CharField("nom de l'établissement", max_length=150)
    slug = models.SlugField("identifiant", unique=True)
    country = models.CharField("pays", max_length=2, choices=COUNTRY_CHOICES, default="CI")
    currency = models.CharField("monnaie", max_length=3, choices=CURRENCY_CHOICES, default="XOF")
    city = models.CharField("ville", max_length=80, blank=True)
    address = models.CharField("adresse", max_length=200, blank=True)
    phone = models.CharField("téléphone", max_length=40, blank=True)
    email = models.EmailField("e-mail", blank=True)
    payment_instructions = models.TextField(
        "comment payer",
        blank=True,
        help_text="Affiché aux parents. Ex. : Wave 07 00 00 00 00 — Orange Money 07 00 00 00 01 "
        "(indiquez le nom et la classe de l'élève en motif).",
    )
    reminder_template = models.TextField(
        "message de relance",
        default=DEFAULT_REMINDER_TEMPLATE,
        help_text="Variables : {parent} {eleve} {classe} {montant} {echeance} {ecole} {lien}",
    )
    receipt_footer = models.CharField("mention en bas des reçus", max_length=200, blank=True)

    online_payment_provider = models.CharField(
        "paiement en ligne", max_length=20, choices=PROVIDER_CHOICES, blank=True
    )
    cinetpay_api_key = models.CharField("CinetPay — apikey", max_length=200, blank=True)
    cinetpay_site_id = models.CharField("CinetPay — site_id", max_length=50, blank=True)

    # Abonnement ScolaPay (géré par vous, l'opérateur, depuis /admin)
    plan = models.CharField("formule", max_length=20, choices=PLAN_CHOICES, default=PLAN_ESSENTIAL)
    price_per_student = models.PositiveIntegerField("prix par élève et par an", default=500)
    subscription_until = models.DateField("abonnement payé jusqu'au", null=True, blank=True)
    is_demo = models.BooleanField("école de démonstration", default=False)
    is_active = models.BooleanField("active", default=True)
    receipt_counter = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "école"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def currency_symbol(self):
        return CURRENCIES.get(self.currency, CURRENCIES["XOF"])[0]

    @property
    def current_year(self):
        return self.years.filter(is_current=True).first()

    def next_receipt_number(self):
        """Numéro de reçu séquentiel, sans trou ni doublon, même en concurrence."""
        with transaction.atomic():
            School.objects.filter(pk=self.pk).update(receipt_counter=F("receipt_counter") + 1)
            return School.objects.values_list("receipt_counter", flat=True).get(pk=self.pk)


class StaffMember(models.Model):
    DIRECTOR = "directeur"
    CASHIER = "caissier"
    ROLE_CHOICES = [(DIRECTOR, "Direction / fondateur"), (CASHIER, "Caisse / secrétariat")]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="staff")
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="staff")
    role = models.CharField("rôle", max_length=20, choices=ROLE_CHOICES, default=CASHIER)

    class Meta:
        verbose_name = "membre du personnel"
        verbose_name_plural = "personnel"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    @property
    def is_director(self):
        return self.role == self.DIRECTOR


class SchoolYear(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="years")
    name = models.CharField("année scolaire", max_length=20, help_text="Ex. : 2026-2027")
    start_date = models.DateField("rentrée")
    end_date = models.DateField("fin d'année")
    is_current = models.BooleanField("année en cours", default=False)

    class Meta:
        verbose_name = "année scolaire"
        verbose_name_plural = "années scolaires"
        ordering = ["-start_date"]
        constraints = [models.UniqueConstraint(fields=["school", "name"], name="annee_unique_par_ecole")]

    def __str__(self):
        return self.name

    def make_current(self):
        with transaction.atomic():
            SchoolYear.objects.filter(school=self.school).exclude(pk=self.pk).update(is_current=False)
            self.is_current = True
            self.save(update_fields=["is_current"])


class FeeSchedule(models.Model):
    """Barème : la liste des échéances payées par les élèves d'une ou plusieurs classes."""

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="schedules")
    year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name="schedules")
    name = models.CharField("nom du barème", max_length=80, help_text="Ex. : Primaire, Collège, 3e/Tle")

    class Meta:
        verbose_name = "barème"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def total(self):
        return sum(item.amount for item in self.installments.all())


class Installment(models.Model):
    schedule = models.ForeignKey(FeeSchedule, on_delete=models.CASCADE, related_name="installments")
    label = models.CharField("libellé", max_length=80, help_text="Ex. : Inscription, 1re tranche")
    amount = models.PositiveIntegerField("montant")
    due_date = models.DateField("date limite")

    class Meta:
        verbose_name = "échéance"
        ordering = ["due_date", "id"]

    def __str__(self):
        return f"{self.label} ({self.amount})"


class Classroom(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="classrooms")
    year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name="classrooms")
    name = models.CharField("classe", max_length=50, help_text="Ex. : CM2 A, 6e B, Tle D")
    schedule = models.ForeignKey(
        FeeSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="classrooms",
        verbose_name="barème",
    )
    position = models.PositiveSmallIntegerField("ordre d'affichage", default=0)

    class Meta:
        verbose_name = "classe"
        ordering = ["position", "name"]
        constraints = [
            models.UniqueConstraint(fields=["year", "name"], name="classe_unique_par_annee"),
        ]

    def __str__(self):
        return self.name


class Student(models.Model):
    GENDER_CHOICES = [("F", "Fille"), ("M", "Garçon")]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="students")
    matricule = models.CharField(max_length=40, blank=True)
    last_name = models.CharField("nom", max_length=80)
    first_name = models.CharField("prénoms", max_length=120)
    gender = models.CharField("sexe", max_length=1, choices=GENDER_CHOICES, blank=True)
    birth_date = models.DateField("date de naissance", null=True, blank=True)
    parent_name = models.CharField("parent / tuteur", max_length=120, blank=True)
    parent_phone = models.CharField("téléphone du parent", max_length=40, blank=True)
    parent_phone2 = models.CharField("autre téléphone", max_length=40, blank=True)
    notes = models.TextField("notes internes", blank=True)
    token = models.CharField(max_length=40, unique=True, default=new_token, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "élève"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.last_name.upper()} {self.first_name}".strip()

    @property
    def whatsapp_phone(self):
        return normalize_phone(self.parent_phone, self.school.country) or normalize_phone(
            self.parent_phone2, self.school.country
        )


class Enrollment(models.Model):
    """Inscription d'un élève dans une classe pour une année scolaire."""

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name="enrollments")
    classroom = models.ForeignKey(Classroom, on_delete=models.RESTRICT, related_name="enrollments", verbose_name="classe")
    discount = models.PositiveIntegerField(
        "remise", default=0, help_text="Bourse, réduction fratrie… déduite des dernières échéances."
    )
    discount_reason = models.CharField("motif de la remise", max_length=120, blank=True)
    is_active = models.BooleanField("inscrit", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "inscription"
        constraints = [models.UniqueConstraint(fields=["student", "year"], name="une_inscription_par_an")]

    def __str__(self):
        return f"{self.student} — {self.classroom} ({self.year})"

    @property
    def school(self):
        return self.student.school


class PaymentQuerySet(models.QuerySet):
    def valid(self):
        return self.filter(cancelled_at__isnull=True)


class Payment(models.Model):
    CASH = "especes"
    ONLINE = "en_ligne"
    METHOD_CHOICES = [
        (CASH, "Espèces"),
        ("wave", "Wave"),
        ("orange_money", "Orange Money"),
        ("mtn_momo", "MTN MoMo"),
        ("moov_money", "Moov Money"),
        (ONLINE, "Paiement en ligne"),
        ("virement", "Virement / versement bancaire"),
        ("cheque", "Chèque"),
        ("autre", "Autre"),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="payments")
    # RESTRICT : impossible de supprimer une inscription qui a des paiements, sauf
    # suppression de l'école entière.
    enrollment = models.ForeignKey(Enrollment, on_delete=models.RESTRICT, related_name="payments")
    amount = models.PositiveIntegerField("montant")
    method = models.CharField("mode de paiement", max_length=20, choices=METHOD_CHOICES, default=CASH)
    reference = models.CharField(
        "référence", max_length=80, blank=True, help_text="N° de transaction mobile money, n° de chèque…"
    )
    paid_on = models.DateField("date du paiement", default=timezone.localdate)
    note = models.CharField("observation", max_length=200, blank=True)
    receipt_number = models.PositiveIntegerField("n° de reçu", editable=False)
    token = models.CharField(max_length=40, unique=True, default=new_token, editable=False)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True, editable=False)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+", editable=False
    )
    cancel_reason = models.CharField("motif d'annulation", max_length=200, blank=True)

    objects = PaymentQuerySet.as_manager()

    class Meta:
        verbose_name = "paiement"
        ordering = ["-paid_on", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["school", "receipt_number"], name="recu_unique_par_ecole"),
        ]

    def __str__(self):
        return f"Reçu {self.receipt_label} — {self.amount}"

    @property
    def receipt_label(self):
        return f"{self.receipt_number:06d}"

    @property
    def is_cancelled(self):
        return self.cancelled_at is not None

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = self.school.next_receipt_number()
        super().save(*args, **kwargs)

    def cancel(self, user, reason):
        self.cancelled_at = timezone.now()
        self.cancelled_by = user
        self.cancel_reason = reason
        self.save(update_fields=["cancelled_at", "cancelled_by", "cancel_reason"])


class Reminder(models.Model):
    CHANNEL_CHOICES = [("whatsapp", "WhatsApp"), ("sms", "SMS"), ("appel", "Appel")]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="reminders")
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="reminders")
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default="whatsapp")
    amount_due = models.PositiveIntegerField("montant réclamé")
    message = models.TextField(blank=True)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "relance"
        ordering = ["-created_at"]


class OnlineTransaction(models.Model):
    PENDING = "en_attente"
    ACCEPTED = "accepte"
    REFUSED = "refuse"
    STATUS_CHOICES = [(PENDING, "En attente"), (ACCEPTED, "Accepté"), (REFUSED, "Refusé")]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="transactions")
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="transactions")
    reference = models.CharField(max_length=40, unique=True, default=new_reference)
    provider = models.CharField(max_length=20)
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name="transaction")
    provider_reference = models.CharField(max_length=120, blank=True)
    last_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "transaction en ligne"
        verbose_name_plural = "transactions en ligne"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} ({self.get_status_display()})"
