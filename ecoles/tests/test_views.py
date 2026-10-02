import json
from datetime import date
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from ecoles.models import (
    Classroom,
    Enrollment,
    FeeSchedule,
    OnlineTransaction,
    Payment,
    Reminder,
    SchoolYear,
    StaffMember,
    Student,
)

from .helpers import PASSWORD, make_school, make_student, make_user


@override_settings(ALLOWED_HOSTS=["testserver"])
class StaffViewsTests(TestCase):
    def setUp(self):
        self.school, self.year, self.classroom = make_school("ecole-a")
        self.director = make_user(self.school, "directeur.a")
        self.cashier = make_user(self.school, "caisse.a", role=StaffMember.CASHIER)
        self.student, self.enrollment = make_student(self.school, self.year, self.classroom)

        self.other_school, other_year, other_classroom = make_school("ecole-b")
        make_user(self.other_school, "directeur.b")
        self.other_student, self.other_enrollment = make_student(
            self.other_school, other_year, other_classroom, last_name="TRAORE"
        )

    def login(self, username="directeur.a"):
        self.client.login(username=username, password=PASSWORD)

    def test_login_required(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_all_main_pages_render(self):
        self.login()
        payment = Payment.objects.create(school=self.school, enrollment=self.enrollment, amount=30000)
        for name, args in [
            ("dashboard", []),
            ("student_list", []),
            ("student_create", []),
            ("student_detail", [self.enrollment.pk]),
            ("student_edit", [self.enrollment.pk]),
            ("payment_create", [self.enrollment.pk]),
            ("payment_receipt", [payment.pk]),
            ("cash_journal", []),
            ("reminders", []),
            ("classes", []),
            ("student_import", []),
            ("school_settings", []),
            ("schedule_edit", [self.classroom.schedule.pk]),
            ("year_create", []),
        ]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200)

    def test_schools_are_isolated(self):
        self.login()
        other_payment = Payment.objects.create(
            school=self.other_school, enrollment=self.other_enrollment, amount=1000
        )
        for name, args in [
            ("student_detail", [self.other_enrollment.pk]),
            ("payment_create", [self.other_enrollment.pk]),
            ("payment_receipt", [other_payment.pk]),
            ("schedule_edit", [self.other_enrollment.classroom.schedule.pk]),
        ]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 404)
        response = self.client.get(reverse("student_list"))
        self.assertContains(response, "KOUASSI")
        self.assertNotContains(response, "TRAORE")

    def test_record_payment_numbers_receipts_per_school(self):
        self.login("caisse.a")
        url = reverse("payment_create", args=[self.enrollment.pk])
        first = self.client.post(url, {"amount": 30000, "method": "especes", "paid_on": "2026-09-02"})
        second = self.client.post(
            url, {"amount": 20000, "method": "wave", "reference": "WV123", "paid_on": "2026-09-03"}
        )
        payments = list(Payment.objects.filter(school=self.school).order_by("receipt_number"))
        self.assertEqual([p.receipt_number for p in payments], [1, 2])
        self.assertRedirects(first, reverse("payment_receipt", args=[payments[0].pk]))
        self.assertRedirects(second, reverse("payment_receipt", args=[payments[1].pk]))
        self.assertEqual(payments[0].recorded_by, self.cashier)
        receipt = self.client.get(reverse("payment_receipt", args=[payments[0].pk]))
        self.assertContains(receipt, "trente mille francs CFA")
        self.assertContains(receipt, "<svg")  # QR code de vérification
        # Le reste affiché est celui après CE versement, pas le solde actuel.
        self.assertContains(receipt, "130 000 FCFA")

    def test_mobile_money_payment_requires_reference(self):
        self.login("caisse.a")
        response = self.client.post(
            reverse("payment_create", args=[self.enrollment.pk]),
            {"amount": 30000, "method": "orange_money", "paid_on": "2026-09-02"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Payment.objects.exists())

    def test_overpayment_is_refused(self):
        self.login("caisse.a")
        response = self.client.post(
            reverse("payment_create", args=[self.enrollment.pk]),
            {"amount": 999999, "method": "especes", "paid_on": "2026-09-02"},
        )
        self.assertContains(response, "dépasse le reste à payer")
        self.assertFalse(Payment.objects.exists())

    def test_only_director_can_cancel_a_receipt(self):
        payment = Payment.objects.create(school=self.school, enrollment=self.enrollment, amount=30000)
        url = reverse("payment_cancel", args=[payment.pk])
        self.login("caisse.a")
        self.assertEqual(self.client.post(url, {"reason": "test"}).status_code, 403)
        self.client.logout()
        self.login()
        self.client.post(url, {"reason": "Erreur de saisie"})
        payment.refresh_from_db()
        self.assertTrue(payment.is_cancelled)
        self.assertEqual(payment.cancelled_by, self.director)

    def test_cashier_cannot_grant_discount(self):
        self.login("caisse.a")
        self.client.post(
            reverse("student_edit", args=[self.enrollment.pk]),
            {"last_name": "KOUASSI", "first_name": "Aya", "parent_phone": "0707070707",
             "classroom": self.classroom.pk, "discount": 100000},
        )
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.discount, 0)

    def test_settings_are_director_only(self):
        self.login("caisse.a")
        self.assertEqual(self.client.get(reverse("school_settings")).status_code, 403)

    def test_create_student(self):
        self.login("caisse.a")
        response = self.client.post(
            reverse("student_create"),
            {"last_name": "BAMBA", "first_name": "Ibrahim", "parent_phone": "05 05 05 05 05",
             "classroom": self.classroom.pk, "discount": 0},
        )
        enrollment = Enrollment.objects.get(student__last_name="BAMBA")
        self.assertRedirects(response, reverse("student_detail", args=[enrollment.pk]))
        self.assertEqual(enrollment.student.school, self.school)

    def test_invalid_phone_is_rejected(self):
        self.login()
        response = self.client.post(
            reverse("student_create"),
            {"last_name": "BAMBA", "parent_phone": "123", "classroom": self.classroom.pk},
        )
        self.assertContains(response, "Numéro invalide")

    def test_cannot_enroll_into_another_schools_class(self):
        self.login()
        other_class = self.other_enrollment.classroom
        response = self.client.post(
            reverse("student_create"), {"last_name": "BAMBA", "classroom": other_class.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Student.objects.filter(last_name="BAMBA").exists())

    def test_whatsapp_reminder_is_logged_and_redirects(self):
        self.login("caisse.a")
        response = self.client.post(reverse("reminder_send", args=[self.enrollment.pk]), {"canal": "whatsapp"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("https://wa.me/2250707070707?text="))
        reminder = Reminder.objects.get()
        self.assertEqual(reminder.sent_by, self.cashier)
        self.assertIn(self.student.token, reminder.message)

    def test_reminders_list_only_late_students(self):
        self.login()
        _, paid_up = make_student(self.school, self.year, self.classroom, last_name="DIALLO")
        Payment.objects.create(school=self.school, enrollment=paid_up, amount=160000)
        response = self.client.get(reverse("reminders"))
        self.assertContains(response, "KOUASSI")
        self.assertNotContains(response, "DIALLO")

    def test_csv_import_semicolon_cp1252(self):
        self.login()
        content = (
            "Nom;Prénoms;Classe;Matricule;Téléphone;Remise\n"
            "KONÉ;Mariam;CM2 A;M-001;07 01 02 03 04;10 000\n"
            "YAO;Koffi;6e B;M-002;0102030405;0\n"
            ";Sans nom;CM2 A;;;\n"
        ).encode("cp1252")
        upload = SimpleUploadedFile("eleves.csv", content, content_type="text/csv")
        response = self.client.post(reverse("student_import"), {"file": upload, "create_classes": "on"})
        self.assertContains(response, "2 ajouté(s)")
        self.assertContains(response, "Ligne 4")
        kone = Enrollment.objects.get(student__matricule="M-001")
        self.assertEqual(kone.student.last_name, "KONÉ")
        self.assertEqual(kone.discount, 10000)
        self.assertTrue(Classroom.objects.filter(year=self.year, name="6e B").exists())

        # Ré-import du même fichier : mise à jour, pas de doublon.
        upload = SimpleUploadedFile("eleves.csv", content, content_type="text/csv")
        self.client.post(reverse("student_import"), {"file": upload, "create_classes": "on"})
        self.assertEqual(Student.objects.filter(school=self.school, matricule="M-001").count(), 1)

    def test_new_year_copies_classes_and_schedules(self):
        self.login()
        response = self.client.post(
            reverse("year_create"),
            {"name": "2027-2028", "start_date": "2027-09-01", "end_date": "2028-07-15",
             "copy_from": self.year.pk, "make_current": "on"},
        )
        self.assertRedirects(response, reverse("classes"))
        new_year = SchoolYear.objects.get(school=self.school, name="2027-2028")
        self.assertTrue(new_year.is_current)
        self.assertFalse(SchoolYear.objects.get(pk=self.year.pk).is_current)
        schedule = FeeSchedule.objects.get(year=new_year)
        self.assertEqual(schedule.installments.first().due_date, date(2027, 9, 1))
        self.assertEqual(Classroom.objects.get(year=new_year).schedule, schedule)

        # Réinscription des élèves de l'an dernier.
        target = Classroom.objects.get(year=new_year)
        self.client.post(
            reverse("reenroll"),
            {"source": self.classroom.pk, "target": target.pk, "eleves": [self.student.pk]},
        )
        self.assertTrue(Enrollment.objects.filter(student=self.student, year=new_year).exists())


@override_settings(ALLOWED_HOSTS=["testserver"])
class PublicViewsTests(TestCase):
    def setUp(self):
        self.school, self.year, self.classroom = make_school("ecole-a", online_payment_provider="demo")
        self.student, self.enrollment = make_student(self.school, self.year, self.classroom)

    def test_parent_portal_and_unknown_token(self):
        response = self.client.get(reverse("parent_portal", args=[self.student.token]))
        self.assertContains(response, "Aya KOUASSI")
        self.assertContains(response, "Payer maintenant")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
        self.assertEqual(self.client.get(reverse("parent_portal", args=["inconnu"])).status_code, 404)

    def test_public_receipt_of_cancelled_payment(self):
        payment = Payment.objects.create(school=self.school, enrollment=self.enrollment, amount=30000)
        self.assertContains(self.client.get(reverse("public_receipt", args=[payment.token])), "Reçu authentique")
        payment.cancel(None, "Doublon")
        self.assertContains(self.client.get(reverse("public_receipt", args=[payment.token])), "ANNULÉ")

    def test_demo_online_payment_end_to_end(self):
        response = self.client.post(reverse("parent_pay", args=[self.student.token]), {"amount": 30000})
        tx = OnlineTransaction.objects.get()
        self.assertRedirects(response, reverse("demo_checkout", args=[tx.reference]), fetch_redirect_response=False)
        self.client.post(reverse("demo_checkout", args=[tx.reference]), {"action": "valider"})
        response = self.client.get(reverse("payment_return", args=[tx.reference]))
        self.assertContains(response, "Paiement confirmé")
        tx.refresh_from_db()
        self.assertEqual(tx.status, OnlineTransaction.ACCEPTED)
        self.assertEqual(tx.payment.amount, 30000)
        self.assertEqual(tx.payment.method, Payment.ONLINE)
        # Le reçu d'un paiement en ligne (sans caissier) s'affiche.
        self.assertContains(self.client.get(reverse("public_receipt", args=[tx.payment.token])), "paiement en ligne")
        # Revenir sur la page ne crée pas un second paiement.
        self.client.get(reverse("payment_return", args=[tx.reference]))
        self.assertEqual(Payment.objects.count(), 1)

    def test_amount_above_balance_is_refused(self):
        self.client.post(reverse("parent_pay", args=[self.student.token]), {"amount": 999999})
        self.assertFalse(OnlineTransaction.objects.exists())


def fake_response(payload):
    response = mock.Mock()
    response.json.return_value = payload
    return response


@override_settings(ALLOWED_HOSTS=["testserver"])
class CinetPayTests(TestCase):
    def setUp(self):
        self.school, self.year, self.classroom = make_school(
            "ecole-a", online_payment_provider="cinetpay", cinetpay_api_key="KEY", cinetpay_site_id="123456"
        )
        self.student, self.enrollment = make_student(self.school, self.year, self.classroom)

    @mock.patch("ecoles.payments.requests.post")
    def test_full_flow_with_notification(self, post):
        post.return_value = fake_response(
            {"code": "201", "message": "CREATED", "data": {"payment_url": "https://checkout.cinetpay.com/p/abc"}}
        )
        response = self.client.post(reverse("parent_pay", args=[self.student.token]), {"amount": 30000})
        self.assertEqual(response["Location"], "https://checkout.cinetpay.com/p/abc")
        tx = OnlineTransaction.objects.get()
        sent = post.call_args.kwargs["json"]
        self.assertEqual(sent["transaction_id"], tx.reference)
        self.assertEqual(sent["amount"], 30000)
        self.assertEqual(sent["currency"], "XOF")
        self.assertTrue(sent["notify_url"].endswith(reverse("cinetpay_notify")))

        # Notification : on revérifie auprès de CinetPay avant de créditer.
        post.return_value = fake_response(
            {"code": "00", "message": "SUCCES", "data": {"status": "ACCEPTED", "amount": "30000", "operator_id": "MP123"}}
        )
        response = self.client.post(
            reverse("cinetpay_notify"), {"cpm_trans_id": tx.reference, "cpm_site_id": "123456"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post.call_args.args[0], "https://api-checkout.cinetpay.com/v2/payment/check")
        tx.refresh_from_db()
        self.assertEqual(tx.status, OnlineTransaction.ACCEPTED)
        self.assertEqual(tx.payment.reference, "MP123")

        # Notification en double : aucun nouveau paiement.
        self.client.post(reverse("cinetpay_notify"), {"cpm_trans_id": tx.reference, "cpm_site_id": "123456"})
        self.assertEqual(Payment.objects.count(), 1)

    @mock.patch("ecoles.payments.requests.post")
    def test_amount_must_be_multiple_of_five(self, post):
        self.client.post(reverse("parent_pay", args=[self.student.token]), {"amount": 30003})
        self.assertFalse(OnlineTransaction.objects.exists())
        post.assert_not_called()

    @mock.patch("ecoles.payments.requests.post")
    def test_refused_or_tampered_amount_is_not_credited(self, post):
        tx = OnlineTransaction.objects.create(
            school=self.school, enrollment=self.enrollment, provider="cinetpay", amount=30000
        )
        post.return_value = fake_response({"code": "00", "data": {"status": "ACCEPTED", "amount": "100"}})
        self.client.post(reverse("cinetpay_notify"), {"cpm_trans_id": tx.reference})
        tx.refresh_from_db()
        self.assertEqual(tx.status, OnlineTransaction.REFUSED)
        self.assertFalse(Payment.objects.exists())

    @mock.patch("ecoles.payments.requests.post")
    def test_pending_stays_pending(self, post):
        tx = OnlineTransaction.objects.create(
            school=self.school, enrollment=self.enrollment, provider="cinetpay", amount=30000
        )
        post.return_value = fake_response({"code": "662", "data": {"status": "WAITING_FOR_CUSTOMER"}})
        self.client.post(reverse("cinetpay_notify"), {"cpm_trans_id": tx.reference})
        tx.refresh_from_db()
        self.assertEqual(tx.status, OnlineTransaction.PENDING)
        self.assertIn("WAITING_FOR_CUSTOMER", json.loads(tx.last_response)["data"]["status"])

    def test_notify_ping_and_wrong_site(self):
        self.assertEqual(self.client.get(reverse("cinetpay_notify")).status_code, 200)
        tx = OnlineTransaction.objects.create(
            school=self.school, enrollment=self.enrollment, provider="cinetpay", amount=30000
        )
        response = self.client.post(reverse("cinetpay_notify"), {"cpm_trans_id": tx.reference, "cpm_site_id": "999"})
        self.assertEqual(response.status_code, 400)


@override_settings(ALLOWED_HOSTS=["testserver"])
class LeavingStudentTests(TestCase):
    def test_director_can_mark_student_as_left(self):
        school, year, classroom = make_school("ecole-a")
        make_user(school, "directeur.a")
        _, enrollment = make_student(school, year, classroom)
        self.client.login(username="directeur.a", password=PASSWORD)
        self.client.post(
            reverse("student_edit", args=[enrollment.pk]),
            {"last_name": "KOUASSI", "first_name": "Aya", "classroom": classroom.pk, "discount": 0},
        )
        enrollment.refresh_from_db()
        self.assertFalse(enrollment.is_active)
        self.assertNotContains(self.client.get(reverse("student_list")), "KOUASSI")
        self.assertNotContains(self.client.get(reverse("reminders")), "KOUASSI")
