"""
Le cœur du métier : qui doit combien, depuis quand.

Règles :
- l'échéancier d'un élève est celui du barème de sa classe ;
- la remise est déduite en partant de la dernière échéance (les premières
  tranches restent dues en entier) ;
- les paiements soldent les échéances dans l'ordre chronologique ;
- une échéance est « exigible » le jour de sa date limite, « en retard » après.
"""
from dataclasses import dataclass, field
from datetime import date

from django.db.models import Q, Sum
from django.utils import timezone

from .models import Enrollment

PAID = "paye"
PARTIAL = "partiel"
LATE = "en_retard"
DUE = "exigible"
UPCOMING = "a_venir"

STATE_LABELS = {
    PAID: "Payé",
    PARTIAL: "Partiel",
    LATE: "En retard",
    DUE: "À payer aujourd'hui",
    UPCOMING: "À venir",
}


@dataclass
class Line:
    label: str
    due_date: date
    amount: int
    paid: int
    state: str

    @property
    def remaining(self):
        return self.amount - self.paid

    @property
    def state_label(self):
        return STATE_LABELS[self.state]


@dataclass
class Balance:
    total: int
    paid: int
    due_to_date: int
    lines: list = field(default_factory=list)

    @property
    def overdue(self):
        """Montant exigible non payé (ce que l'on réclame aujourd'hui)."""
        return max(0, self.due_to_date - self.paid)

    @property
    def remaining(self):
        return self.total - self.paid

    @property
    def status(self):
        if self.total and self.paid >= self.total:
            return "solde"
        return "en_retard" if self.overdue > 0 else "a_jour"

    @property
    def status_label(self):
        return {"solde": "Soldé", "en_retard": "En retard", "a_jour": "À jour"}[self.status]

    @property
    def next_line(self):
        """Prochaine échéance non soldée (pour le message de relance)."""
        return next((line for line in self.lines if line.remaining > 0), None)

    @property
    def progress(self):
        return min(100, round(100 * self.paid / self.total)) if self.total else 100


def net_amounts(installments, discount):
    """Applique la remise en partant de la dernière échéance."""
    amounts = [item.amount for item in installments]
    left = discount
    for index in range(len(amounts) - 1, -1, -1):
        if left <= 0:
            break
        cut = min(left, amounts[index])
        amounts[index] -= cut
        left -= cut
    return amounts


def compute_balance(installments, discount, paid, today=None):
    today = today or timezone.localdate()
    installments = sorted(installments, key=lambda item: (item.due_date, item.id or 0))
    amounts = net_amounts(installments, discount)
    lines = []
    left_to_allocate = paid
    due_to_date = 0
    for item, amount in zip(installments, amounts):
        allocated = min(left_to_allocate, amount)
        left_to_allocate -= allocated
        if item.due_date <= today:
            due_to_date += amount
        if allocated >= amount:
            state = PAID
        elif item.due_date < today:
            state = LATE
        elif item.due_date == today:
            state = DUE
        elif allocated > 0:
            state = PARTIAL
        else:
            state = UPCOMING
        lines.append(Line(item.label, item.due_date, amount, allocated, state))
    return Balance(total=sum(amounts), paid=paid, due_to_date=due_to_date, lines=lines)


def enrollments_with_balances(queryset, today=None):
    """
    Calcule les soldes d'une liste d'inscriptions en 2 requêtes, quelle que
    soit la taille de l'école. Renvoie une liste de (inscription, solde).
    """
    enrollments = list(
        queryset.select_related("student", "classroom", "classroom__schedule").annotate(
            paid_total=Sum("payments__amount", filter=Q(payments__cancelled_at__isnull=True))
        )
    )
    schedule_ids = {e.classroom.schedule_id for e in enrollments if e.classroom.schedule_id}
    installments_by_schedule = {schedule_id: [] for schedule_id in schedule_ids}
    if schedule_ids:
        from .models import Installment

        for item in Installment.objects.filter(schedule_id__in=schedule_ids):
            installments_by_schedule[item.schedule_id].append(item)
    results = []
    for enrollment in enrollments:
        items = installments_by_schedule.get(enrollment.classroom.schedule_id, [])
        balance = compute_balance(items, enrollment.discount, enrollment.paid_total or 0, today)
        results.append((enrollment, balance))
    return results


def balance_for(enrollment: Enrollment, today=None):
    schedule = enrollment.classroom.schedule
    items = list(schedule.installments.all()) if schedule else []
    paid = enrollment.payments.valid().aggregate(total=Sum("amount"))["total"] or 0
    return compute_balance(items, enrollment.discount, paid, today)


@dataclass
class Totals:
    students: int = 0
    total: int = 0
    due_to_date: int = 0
    paid: int = 0
    overdue: int = 0
    late_students: int = 0
    collected_due: int = 0

    def add(self, balance):
        self.students += 1
        self.total += balance.total
        self.due_to_date += balance.due_to_date
        self.paid += balance.paid
        self.overdue += balance.overdue
        # Les avances d'un élève ne compensent pas le retard d'un autre.
        self.collected_due += min(balance.paid, balance.due_to_date)
        if balance.overdue > 0:
            self.late_students += 1

    @property
    def remaining(self):
        return self.total - self.paid

    @property
    def recovery_rate(self):
        """Part de l'exigible effectivement encaissée."""
        if not self.due_to_date:
            return 100
        return round(100 * self.collected_due / self.due_to_date)
