"""
Crée une école de démonstration réaliste pour vos rendez-vous commerciaux.

    python manage.py demo                 # mot de passe aléatoire affiché
    python manage.py demo --password XXX  # mot de passe choisi
"""
import random
import secrets
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from ecoles.models import (
    Classroom,
    Enrollment,
    FeeSchedule,
    Installment,
    Payment,
    Reminder,
    School,
    SchoolYear,
    StaffMember,
    Student,
)

LAST_NAMES = [
    "KOUASSI", "KONÉ", "TRAORÉ", "YAO", "KOUAMÉ", "N'GUESSAN", "COULIBALY", "OUATTARA", "BAMBA",
    "DIABATÉ", "KONAN", "AKA", "BROU", "TOURÉ", "DIALLO", "SORO", "DOUMBIA", "FOFANA", "CISSÉ",
    "SYLLA", "KRA", "EHUI", "DJÉ", "ASSI", "GNAGNE", "TANOH", "AMON", "BLÉ", "GUÉI", "ZADI",
    "SANGARÉ", "KOFFI", "ADOU", "ACHI", "DIBY", "SERY", "OKOU", "N'DRI", "YAPI", "AHOUA",
]
GIRL_NAMES = [
    "Aya", "Adjoua", "Affoué", "Amenan", "Akissi", "Ahou", "Mariam", "Fatou", "Aminata", "Awa",
    "Kadi", "Salimata", "Christelle", "Grâce", "Esther", "Ange-Marie", "Prisca", "Larissa", "Inès",
    "Nadège", "Djeneba", "Ruth", "Emmanuella", "Océane", "Marie-Laure",
]
BOY_NAMES = [
    "Kouadio", "Kouakou", "Konan", "Yao", "Koffi", "Ibrahim", "Moussa", "Seydou", "Abdoulaye",
    "Jean-Marc", "Emmanuel", "Junior", "Prince", "Ange", "Cédric", "Franck", "Serge", "Ismaël",
    "Hervé", "Didier", "Yannick", "Lassina", "Mohamed", "Josué", "Brice",
]
PARENT_FIRST = ["Jean", "Marie", "Paul", "Awa", "Bakary", "Alice", "Joseph", "Mariam", "Pierre", "Rose",
                "Issa", "Odile", "Martin", "Fanta", "Gilbert", "Clarisse", "Siaka", "Bernadette"]

SCHEDULES = {
    # nom : [(libellé, montant, (mois, jour) relatif à la rentrée)]
    "Maternelle": [("Inscription", 30000, (9, 1)), ("1re tranche", 60000, (10, 1)),
                   ("2e tranche", 50000, (1, 10)), ("3e tranche", 40000, (3, 31))],
    "Primaire": [("Inscription", 35000, (9, 1)), ("1re tranche", 70000, (10, 1)),
                 ("2e tranche", 60000, (1, 10)), ("3e tranche", 45000, (3, 31))],
    "Collège": [("Inscription", 45000, (9, 1)), ("1re tranche", 100000, (10, 1)),
                ("2e tranche", 80000, (1, 10)), ("3e tranche", 60000, (3, 31))],
}
CLASSES = [
    ("PS", "Maternelle"), ("MS", "Maternelle"), ("GS", "Maternelle"),
    ("CP1", "Primaire"), ("CP2", "Primaire"), ("CE1", "Primaire"), ("CE2", "Primaire"),
    ("CM1", "Primaire"), ("CM2", "Primaire"),
    ("6e", "Collège"), ("5e", "Collège"), ("4e", "Collège"), ("3e", "Collège"),
]
METHODS = [("especes", 45), ("wave", 25), ("orange_money", 15), ("mtn_momo", 10), ("moov_money", 5)]


class Command(BaseCommand):
    help = "Crée (ou recrée) l'école de démonstration « Groupe Scolaire Les Étoiles »."

    def add_arguments(self, parser):
        parser.add_argument("--password", help="Mot de passe des comptes de démo (sinon aléatoire).")
        parser.add_argument("--seed", type=int, default=2026, help="Graine aléatoire (données reproductibles).")

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(options["seed"])
        password = options["password"] or secrets.token_urlsafe(9)
        today = timezone.localdate()
        start_year = today.year if today.month >= 8 else today.year - 1

        User = get_user_model()
        User.objects.filter(username__in=["directeur.demo", "caisse.demo"]).delete()
        School.objects.filter(slug="demo-les-etoiles").delete()

        school = School.objects.create(
            name="Groupe Scolaire Les Étoiles (démo)",
            slug="demo-les-etoiles",
            country="CI",
            currency="XOF",
            city="Abidjan — Cocody",
            address="Riviera 3, près du carrefour",
            phone="27 22 00 00 00",
            payment_instructions=(
                "Wave ou Orange Money au 07 00 00 00 00 (Groupe Scolaire Les Étoiles).\n"
                "Motif : nom + classe de l'élève. Ou à la caisse, du lundi au vendredi, 7h30–16h."
            ),
            receipt_footer="Les sommes versées ne sont pas remboursables.",
            online_payment_provider="demo",
            plan=School.PLAN_RECOVERY,
            price_per_student=1000,
            subscription_until=date(start_year + 1, 8, 31),
            is_demo=True,
        )
        director = User.objects.create_user(
            "directeur.demo", password=password, first_name="Awa", last_name="KONÉ (démo)"
        )
        cashier = User.objects.create_user(
            "caisse.demo", password=password, first_name="Serge", last_name="YAO (démo)"
        )
        StaffMember.objects.create(user=director, school=school, role=StaffMember.DIRECTOR)
        StaffMember.objects.create(user=cashier, school=school, role=StaffMember.CASHIER)

        year = SchoolYear.objects.create(
            school=school,
            name=f"{start_year}-{start_year + 1}",
            start_date=date(start_year, 9, 1),
            end_date=date(start_year + 1, 7, 15),
            is_current=True,
        )

        def due(month_day):
            month, day = month_day
            return date(start_year if month >= 8 else start_year + 1, month, day)

        schedules = {}
        for name, items in SCHEDULES.items():
            schedule = FeeSchedule.objects.create(school=school, year=year, name=name)
            for label, amount, month_day in items:
                Installment.objects.create(schedule=schedule, label=label, amount=amount, due_date=due(month_day))
            schedules[name] = (schedule, [(label, amount, due(md)) for label, amount, md in items])

        planned = []  # (date, inscription, montant, mode)
        late_enrollments = []
        counter = 0
        for position, (class_name, schedule_name) in enumerate(CLASSES):
            schedule, items = schedules[schedule_name]
            classroom = Classroom.objects.create(
                school=school, year=year, name=class_name, schedule=schedule, position=position
            )
            for _ in range(rng.randint(17, 24)):
                counter += 1
                girl = rng.random() < 0.5
                last_name = rng.choice(LAST_NAMES)
                student = Student.objects.create(
                    school=school,
                    matricule=f"{start_year}-{counter:04d}",
                    last_name=last_name,
                    first_name=rng.choice(GIRL_NAMES if girl else BOY_NAMES),
                    gender="F" if girl else "M",
                    parent_name=f"{last_name} {rng.choice(PARENT_FIRST)}",
                    parent_phone=f"07 00 {rng.randint(10, 99)} {rng.randint(10, 99)} {rng.randint(10, 99)}",
                )
                discount = 0
                reason = ""
                if rng.random() < 0.08:
                    discount, reason = rng.choice([(20000, "Réduction fratrie"), (50000, "Bourse d'excellence")])
                enrollment = Enrollment.objects.create(
                    student=student, year=year, classroom=classroom, discount=discount, discount_reason=reason
                )
                planned.extend(self.plan_payments(rng, enrollment, items, discount, today))
                if rng.random() < 0.35:
                    late_enrollments.append(enrollment)

        planned.sort(key=lambda item: item[0])
        for paid_on, enrollment, amount, method in planned:
            reference = "" if method == "especes" else f"{method[:2].upper()}{rng.randint(10**7, 10**8 - 1)}"
            Payment.objects.create(
                school=school,
                enrollment=enrollment,
                amount=amount,
                method=method,
                reference=reference,
                paid_on=paid_on,
                recorded_by=cashier,
            )

        for enrollment in late_enrollments[:25]:
            Reminder.objects.create(
                school=school,
                enrollment=enrollment,
                channel="whatsapp",
                amount_due=rng.choice([35000, 45000, 70000]),
                message="Relance de démonstration",
                sent_by=cashier,
            )

        self.stdout.write(self.style.SUCCESS(f"École de démo créée : {counter} élèves, {len(planned)} paiements."))
        self.stdout.write("Connexion direction : directeur.demo")
        self.stdout.write("Connexion caisse    : caisse.demo")
        self.stdout.write(f"Mot de passe        : {password}")

    def plan_payments(self, rng, enrollment, items, discount, today):
        """Simule trois profils de parents : ponctuel, en retard, mauvais payeur."""
        profile = rng.choices(["ponctuel", "retard", "mauvais"], weights=[55, 32, 13])[0]
        amounts = [amount for _, amount, _ in items]
        left = discount
        for index in range(len(amounts) - 1, -1, -1):  # remise sur les dernières tranches
            cut = min(left, amounts[index])
            amounts[index] -= cut
            left -= cut
        payments = []
        for index, ((_, _, due_date), amount) in enumerate(zip(items, amounts)):
            if amount <= 0 or due_date > today + timedelta(days=20):
                continue
            if profile == "ponctuel":
                day = due_date - timedelta(days=rng.randint(0, 20))
                parts = [amount]
            elif profile == "retard":
                day = due_date + timedelta(days=rng.randint(-3, 30))
                parts = [amount] if rng.random() < 0.5 else [amount // 2 // 1000 * 1000]
            else:
                if index > 0 or rng.random() < 0.4:
                    continue
                day = due_date + timedelta(days=rng.randint(0, 40))
                parts = [amount]
            day = max(day, enrollment.year.start_date - timedelta(days=30))
            for part in parts:
                if part > 0 and day <= today:
                    method = rng.choices([m for m, _ in METHODS], weights=[w for _, w in METHODS])[0]
                    payments.append((day, enrollment, part, method))
        return payments
