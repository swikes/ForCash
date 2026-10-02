from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from django.views.generic import RedirectView

from . import public_views, views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="dashboard", permanent=False)),
    path(
        "connexion/",
        auth_views.LoginView.as_view(template_name="registration/login.html", redirect_authenticated_user=True),
        name="login",
    ),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "mot-de-passe/",
        auth_views.PasswordChangeView.as_view(
            template_name="registration/password_change.html", success_url=reverse_lazy("dashboard")
        ),
        name="password_change",
    ),
    path("tableau-de-bord/", views.dashboard, name="dashboard"),
    # Élèves
    path("eleves/", views.student_list, name="student_list"),
    path("eleves/nouveau/", views.student_create, name="student_create"),
    path("eleves/import/", views.student_import, name="student_import"),
    path("eleves/import/modele.csv", views.import_template, name="import_template"),
    path("eleves/reinscriptions/", views.reenroll, name="reenroll"),
    path("eleves/<int:pk>/", views.student_detail, name="student_detail"),
    path("eleves/<int:pk>/modifier/", views.student_edit, name="student_edit"),
    path("eleves/<int:pk>/paiement/", views.payment_create, name="payment_create"),
    path("eleves/<int:pk>/relance/", views.reminder_send, name="reminder_send"),
    # Caisse
    path("paiements/", views.cash_journal, name="cash_journal"),
    path("paiements/<int:pk>/recu/", views.payment_receipt, name="payment_receipt"),
    path("paiements/<int:pk>/annuler/", views.payment_cancel, name="payment_cancel"),
    path("relances/", views.reminders, name="reminders"),
    # Organisation
    path("classes/", views.classes, name="classes"),
    path("classes/nouvelle/", views.classroom_edit, name="classroom_create"),
    path("classes/<int:pk>/", views.classroom_edit, name="classroom_edit"),
    path("baremes/nouveau/", views.schedule_edit, name="schedule_create"),
    path("baremes/<int:pk>/", views.schedule_edit, name="schedule_edit"),
    path("parametres/", views.school_settings, name="school_settings"),
    path("parametres/personnel/nouveau/", views.staff_create, name="staff_create"),
    path("parametres/personnel/<int:pk>/activer/", views.staff_toggle, name="staff_toggle"),
    path("parametres/annees/nouvelle/", views.year_create, name="year_create"),
    path("parametres/annees/<int:pk>/activer/", views.year_activate, name="year_activate"),
    # Public (parents)
    path("p/<str:token>/", public_views.parent_portal, name="parent_portal"),
    path("p/<str:token>/payer/", public_views.parent_pay, name="parent_pay"),
    path("r/<str:token>/", public_views.public_receipt, name="public_receipt"),
    path("paiement/retour/<str:reference>/", public_views.payment_return, name="payment_return"),
    path("paiement/demo/<str:reference>/", public_views.demo_checkout, name="demo_checkout"),
    path("paiement/notification/cinetpay/", public_views.cinetpay_notify, name="cinetpay_notify"),
]
