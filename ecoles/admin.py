"""
Back-office de l'opérateur (vous) : créer les écoles clientes, leurs comptes,
suivre les abonnements. Accessible sur /admin avec un compte superutilisateur.
"""
from django.contrib import admin
from django.db.models import Count, Q
from django.utils import timezone

from .models import (
    Classroom,
    Enrollment,
    FeeSchedule,
    Installment,
    OnlineTransaction,
    Payment,
    Reminder,
    School,
    SchoolYear,
    StaffMember,
    Student,
)


class StaffInline(admin.TabularInline):
    model = StaffMember
    extra = 0
    autocomplete_fields = ["user"]


class YearInline(admin.TabularInline):
    model = SchoolYear
    extra = 0


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = [
        "name", "city", "country", "plan", "active_students", "annual_amount", "subscription_until",
        "subscription_ok", "is_active",
    ]
    list_filter = ["country", "plan", "is_active", "is_demo"]
    search_fields = ["name", "city", "phone", "email"]
    prepopulated_fields = {"slug": ["name"]}
    inlines = [StaffInline, YearInline]
    fieldsets = [
        ("Établissement", {"fields": ["name", "slug", "country", "currency", "city", "address", "phone", "email"]}),
        ("Abonnement ScolaPay", {"fields": ["plan", "price_per_student", "subscription_until", "is_active", "is_demo"]}),
        ("Paiements et relances", {
            "classes": ["collapse"],
            "fields": ["payment_instructions", "reminder_template", "receipt_footer",
                       "online_payment_provider", "cinetpay_api_key", "cinetpay_site_id"],
        }),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _students=Count(
                "years__enrollments",
                filter=Q(years__is_current=True, years__enrollments__is_active=True),
            )
        )

    @admin.display(description="élèves (année en cours)", ordering="_students")
    def active_students(self, obj):
        return obj._students

    @admin.display(description="montant annuel")
    def annual_amount(self, obj):
        return f"{obj._students * obj.price_per_student:,}".replace(",", " ")

    @admin.display(description="à jour", boolean=True)
    def subscription_ok(self, obj):
        return bool(obj.subscription_until and obj.subscription_until >= timezone.localdate())


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ["user", "school", "role"]
    list_filter = ["role", "school"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "school__name"]
    autocomplete_fields = ["user", "school"]


class InstallmentInline(admin.TabularInline):
    model = Installment
    extra = 1


@admin.register(FeeSchedule)
class FeeScheduleAdmin(admin.ModelAdmin):
    list_display = ["name", "school", "year"]
    list_filter = ["school"]
    inlines = [InstallmentInline]


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ["name", "school", "year", "schedule"]
    list_filter = ["school"]
    search_fields = ["name"]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["full_name", "matricule", "school", "parent_name", "parent_phone"]
    list_filter = ["school"]
    search_fields = ["last_name", "first_name", "matricule", "parent_phone"]
    readonly_fields = ["token"]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["student", "classroom", "year", "discount", "is_active"]
    list_filter = ["year__school", "is_active"]
    search_fields = ["student__last_name", "student__first_name"]
    raw_id_fields = ["student", "classroom"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["receipt_label", "school", "enrollment", "amount", "method", "paid_on", "cancelled_at"]
    list_filter = ["school", "method"]
    search_fields = ["reference", "enrollment__student__last_name"]
    date_hierarchy = "paid_on"
    raw_id_fields = ["enrollment"]
    readonly_fields = ["receipt_number", "token", "cancelled_at", "cancelled_by"]

    def has_delete_permission(self, request, obj=None):
        return False  # on annule un paiement, on ne le supprime jamais (traçabilité)


@admin.register(OnlineTransaction)
class OnlineTransactionAdmin(admin.ModelAdmin):
    list_display = ["reference", "school", "amount", "provider", "status", "created_at"]
    list_filter = ["provider", "status", "school"]
    search_fields = ["reference", "provider_reference"]
    readonly_fields = ["last_response"]
    raw_id_fields = ["enrollment", "payment"]


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ["enrollment", "channel", "amount_due", "sent_by", "created_at"]
    list_filter = ["channel", "school"]
    raw_id_fields = ["enrollment"]


admin.site.register(SchoolYear)
