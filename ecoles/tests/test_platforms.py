from io import StringIO

from django.core.management import call_command
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from ecoles.models import Payment, School
from scolapay.hosts import platform_hosts

from .helpers import PASSWORD, make_school, make_user

CODESPACE_HOST = "super-espace-8000.app.github.dev"


class PlatformHostsTests(SimpleTestCase):
    def test_nothing_detected_by_default(self):
        self.assertEqual(platform_hosts({}), ([], []))

    def test_codespaces(self):
        hosts, origins = platform_hosts(
            {"CODESPACE_NAME": "super-espace", "GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN": "app.github.dev"}
        )
        self.assertEqual(hosts, [CODESPACE_HOST])
        self.assertEqual(origins, [f"https://{CODESPACE_HOST}"])

    def test_render(self):
        hosts, origins = platform_hosts({"RENDER_EXTERNAL_HOSTNAME": "scolapay-demo.onrender.com"})
        self.assertEqual(hosts, ["scolapay-demo.onrender.com"])
        self.assertEqual(origins, ["https://scolapay-demo.onrender.com"])


class ForwardedLoginTests(TestCase):
    """Codespaces sert l'application en HTTPS via un proxy : la connexion doit passer le contrôle CSRF."""

    def setUp(self):
        school, _, _ = make_school()
        make_user(school, "directeur.a")

    def login_through_proxy(self):
        client = Client(enforce_csrf_checks=True, HTTP_HOST=CODESPACE_HOST)
        client.get(reverse("login"))
        return client.post(
            reverse("login"),
            {"username": "directeur.a", "password": PASSWORD, "csrfmiddlewaretoken": client.cookies["csrftoken"].value},
            HTTP_ORIGIN=f"https://{CODESPACE_HOST}",
        )

    @override_settings(ALLOWED_HOSTS=[CODESPACE_HOST], CSRF_TRUSTED_ORIGINS=[f"https://{CODESPACE_HOST}"])
    def test_login_works_with_detected_origin(self):
        self.assertRedirects(self.login_through_proxy(), reverse("dashboard"), fetch_redirect_response=False)

    @override_settings(ALLOWED_HOSTS=[CODESPACE_HOST], CSRF_TRUSTED_ORIGINS=[])
    def test_login_is_refused_without_it(self):
        self.assertEqual(self.login_through_proxy().status_code, 403)


class DemoIfMissingTests(TestCase):
    def test_keeps_data_and_resets_password(self):
        call_command("demo", password="Premier-mot-de-passe", stdout=StringIO())
        school = School.objects.get(slug="demo-les-etoiles")
        payments = Payment.objects.filter(school=school).count()

        out = StringIO()
        call_command("demo", password="Second-mot-de-passe", if_missing=True, stdout=out)
        self.assertIn("conservées", out.getvalue())
        self.assertEqual(School.objects.get(slug="demo-les-etoiles").pk, school.pk)
        self.assertEqual(Payment.objects.filter(school=school).count(), payments)
        self.assertFalse(self.client.login(username="directeur.demo", password="Premier-mot-de-passe"))
        self.assertTrue(self.client.login(username="caisse.demo", password="Second-mot-de-passe"))

    def test_creates_school_when_missing(self):
        call_command("demo", password="Un-mot-de-passe", if_missing=True, stdout=StringIO())
        self.assertTrue(School.objects.filter(slug="demo-les-etoiles").exists())
