from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from ecoles.models import Payment, School, StaffMember


class CommandTests(TestCase):
    def test_demo_is_rerunnable(self):
        call_command("demo", password="Demo-test-2026", stdout=StringIO())
        call_command("demo", password="Demo-test-2026", stdout=StringIO())
        school = School.objects.get(slug="demo-les-etoiles")
        self.assertTrue(school.is_demo)
        self.assertGreater(school.students.count(), 200)
        numbers = list(Payment.objects.filter(school=school).values_list("receipt_number", flat=True))
        self.assertEqual(sorted(numbers), list(range(1, len(numbers) + 1)))
        self.assertTrue(self.client.login(username="directeur.demo", password="Demo-test-2026"))

    def test_creer_ecole(self):
        out = StringIO()
        call_command(
            "creer_ecole", nom="Groupe Scolaire La Réussite", pays="SN", directeur="Fall.Awa",
            password="Un-mot-de-passe-solide", stdout=out,
        )
        school = School.objects.get(name="Groupe Scolaire La Réussite")
        self.assertEqual(school.currency, "XOF")
        self.assertEqual(school.country, "SN")
        staff = StaffMember.objects.get(school=school)
        self.assertEqual(staff.user, get_user_model().objects.get(username="fall.awa"))
        self.assertTrue(staff.is_director)
