from dataclasses import dataclass
from datetime import date

from django.test import SimpleTestCase, TestCase

from ecoles import finance
from ecoles.models import Payment

from .helpers import make_school, make_student


@dataclass
class Item:
    label: str
    amount: int
    due_date: date
    id: int = 0


ITEMS = [
    Item("Inscription", 30000, date(2026, 9, 1), 1),
    Item("1re tranche", 70000, date(2026, 10, 1), 2),
    Item("2e tranche", 60000, date(2027, 1, 10), 3),
]


class ComputeBalanceTests(SimpleTestCase):
    def test_nothing_paid_after_first_due_dates(self):
        balance = finance.compute_balance(ITEMS, 0, 0, today=date(2026, 10, 15))
        self.assertEqual(balance.total, 160000)
        self.assertEqual(balance.due_to_date, 100000)
        self.assertEqual(balance.overdue, 100000)
        self.assertEqual(balance.status, "en_retard")
        self.assertEqual([line.state for line in balance.lines], ["en_retard", "en_retard", "a_venir"])

    def test_payments_settle_installments_in_order(self):
        balance = finance.compute_balance(ITEMS, 0, 50000, today=date(2026, 10, 15))
        self.assertEqual([line.paid for line in balance.lines], [30000, 20000, 0])
        self.assertEqual(balance.overdue, 50000)
        self.assertEqual(balance.next_line.label, "1re tranche")

    def test_advance_payment_is_up_to_date(self):
        balance = finance.compute_balance(ITEMS, 0, 120000, today=date(2026, 10, 15))
        self.assertEqual(balance.overdue, 0)
        self.assertEqual(balance.status, "a_jour")
        self.assertEqual(balance.lines[2].state, "partiel")

    def test_fully_paid(self):
        balance = finance.compute_balance(ITEMS, 0, 160000, today=date(2026, 10, 15))
        self.assertEqual(balance.status, "solde")
        self.assertEqual(balance.remaining, 0)

    def test_discount_comes_off_the_last_installments(self):
        balance = finance.compute_balance(ITEMS, 80000, 0, today=date(2026, 10, 15))
        self.assertEqual([line.amount for line in balance.lines], [30000, 50000, 0])
        self.assertEqual(balance.total, 80000)

    def test_due_today_is_payable_not_late(self):
        balance = finance.compute_balance(ITEMS, 0, 30000, today=date(2026, 10, 1))
        self.assertEqual(balance.lines[1].state, "exigible")
        self.assertEqual(balance.overdue, 70000)

    def test_totals_do_not_let_advances_hide_arrears(self):
        totals = finance.Totals()
        totals.add(finance.compute_balance(ITEMS, 0, 160000, today=date(2026, 10, 15)))  # avance
        totals.add(finance.compute_balance(ITEMS, 0, 0, today=date(2026, 10, 15)))  # rien payé
        self.assertEqual(totals.due_to_date, 200000)
        self.assertEqual(totals.recovery_rate, 50)
        self.assertEqual(totals.late_students, 1)


class BalanceQueryTests(TestCase):
    def test_bulk_and_single_balances_match_and_ignore_cancelled(self):
        school, year, classroom = make_school()
        _, enrollment = make_student(school, year, classroom)
        Payment.objects.create(school=school, enrollment=enrollment, amount=30000)
        cancelled = Payment.objects.create(school=school, enrollment=enrollment, amount=10000)
        cancelled.cancel(None, "erreur de saisie")
        [(row_enrollment, bulk)] = finance.enrollments_with_balances(
            enrollment.__class__.objects.filter(pk=enrollment.pk)
        )
        single = finance.balance_for(enrollment)
        self.assertEqual(bulk.paid, 30000)
        self.assertEqual(single.paid, 30000)
        self.assertEqual(bulk.total, single.total)
