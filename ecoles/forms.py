from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.forms import inlineformset_factory

from .models import (
    Classroom,
    FeeSchedule,
    Installment,
    Payment,
    School,
    SchoolYear,
    StaffMember,
    Student,
)
from .utils import format_amount, normalize_phone

User = get_user_model()


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, **kwargs):
        super().__init__(format="%Y-%m-%d", **kwargs)


class StudentForm(forms.ModelForm):
    classroom = forms.ModelChoiceField(queryset=Classroom.objects.none(), label="Classe")
    discount = forms.IntegerField(label="Remise", min_value=0, initial=0, required=False)
    discount_reason = forms.CharField(label="Motif de la remise", max_length=120, required=False)
    is_active = forms.BooleanField(
        label="Toujours inscrit(e)",
        required=False,
        initial=True,
        help_text="Décochez si l'élève a quitté l'école : il disparaît des listes, ses paiements restent.",
    )

    class Meta:
        model = Student
        fields = [
            "last_name",
            "first_name",
            "matricule",
            "gender",
            "birth_date",
            "parent_name",
            "parent_phone",
            "parent_phone2",
            "notes",
        ]
        widgets = {"birth_date": DateInput(), "notes": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, school, year, enrollment=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school
        self.fields["classroom"].queryset = Classroom.objects.filter(year=year)
        if enrollment:
            self.fields["classroom"].initial = enrollment.classroom
            self.fields["discount"].initial = enrollment.discount
            self.fields["discount_reason"].initial = enrollment.discount_reason
            self.fields["is_active"].initial = enrollment.is_active
        else:
            del self.fields["is_active"]

    def clean_parent_phone(self):
        phone = self.cleaned_data["parent_phone"].strip()
        if phone and not normalize_phone(phone, self.school.country):
            raise forms.ValidationError("Numéro invalide pour ce pays (ex. : 07 07 07 07 07 en Côte d'Ivoire).")
        return phone

    def clean_matricule(self):
        matricule = self.cleaned_data["matricule"].strip()
        if matricule:
            duplicates = Student.objects.filter(school=self.school, matricule__iexact=matricule)
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise forms.ValidationError("Ce matricule est déjà utilisé par un autre élève.")
        return matricule

    def clean_discount(self):
        return self.cleaned_data.get("discount") or 0


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount", "method", "reference", "paid_on", "note"]
        widgets = {"paid_on": DateInput()}

    def __init__(self, *args, remaining, currency_symbol, **kwargs):
        super().__init__(*args, **kwargs)
        self.remaining = remaining
        self.currency_symbol = currency_symbol
        self.fields["method"].choices = [c for c in Payment.METHOD_CHOICES if c[0] != Payment.ONLINE]
        self.fields["amount"].widget.attrs.update({"inputmode": "numeric", "autofocus": True})

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Le montant doit être positif.")
        if amount > self.remaining:
            raise forms.ValidationError(
                f"Le montant dépasse le reste à payer ({format_amount(self.remaining)} {self.currency_symbol})."
            )
        return amount

    def clean(self):
        data = super().clean()
        method = data.get("method")
        if method and method not in (Payment.CASH, "autre") and not data.get("reference"):
            self.add_error("reference", "Indiquez la référence de la transaction (anti-fraude).")
        return data


class CancelPaymentForm(forms.Form):
    reason = forms.CharField(label="Motif de l'annulation", max_length=200)


class OnlinePaymentForm(forms.Form):
    amount = forms.IntegerField(label="Montant à payer", min_value=1)

    def __init__(self, *args, remaining, min_amount=100, step=1, **kwargs):
        super().__init__(*args, **kwargs)
        self.remaining = remaining
        self.min_amount = min_amount
        self.step = step
        self.fields["amount"].widget.attrs.update(
            {"inputmode": "numeric", "min": min(min_amount, remaining), "max": remaining, "step": step}
        )

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount > self.remaining:
            raise forms.ValidationError(f"Le reste à payer est de {format_amount(self.remaining)}.")
        if amount < self.min_amount and amount != self.remaining:
            raise forms.ValidationError(f"Montant minimum : {format_amount(self.min_amount)}.")
        if amount % self.step:
            raise forms.ValidationError(f"Le montant doit être un multiple de {self.step}.")
        return amount


class SchoolSettingsForm(forms.ModelForm):
    class Meta:
        model = School
        fields = [
            "name",
            "country",
            "currency",
            "city",
            "address",
            "phone",
            "email",
            "payment_instructions",
            "reminder_template",
            "receipt_footer",
            "online_payment_provider",
            "cinetpay_api_key",
            "cinetpay_site_id",
        ]
        widgets = {
            "payment_instructions": forms.Textarea(attrs={"rows": 3}),
            "reminder_template": forms.Textarea(attrs={"rows": 5}),
            "cinetpay_api_key": forms.PasswordInput(render_value=True),
        }

    def clean(self):
        data = super().clean()
        if data.get("online_payment_provider") == "cinetpay" and not (
            data.get("cinetpay_api_key") and data.get("cinetpay_site_id")
        ):
            self.add_error("cinetpay_site_id", "Renseignez l'apikey et le site_id fournis par CinetPay.")
        return data


class SchoolYearForm(forms.ModelForm):
    copy_from = forms.ModelChoiceField(
        queryset=SchoolYear.objects.none(),
        required=False,
        label="Copier les classes et barèmes de",
        help_text="Les dates des échéances sont décalées d'un an.",
    )
    make_current = forms.BooleanField(label="En faire l'année en cours", required=False, initial=True)

    class Meta:
        model = SchoolYear
        fields = ["name", "start_date", "end_date"]
        widgets = {"start_date": DateInput(), "end_date": DateInput()}

    def __init__(self, *args, school, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school
        self.fields["copy_from"].queryset = SchoolYear.objects.filter(school=school)

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if SchoolYear.objects.filter(school=self.school, name=name).exists():
            raise forms.ValidationError("Cette année scolaire existe déjà.")
        return name

    def clean(self):
        data = super().clean()
        if data.get("start_date") and data.get("end_date") and data["end_date"] <= data["start_date"]:
            self.add_error("end_date", "La fin d'année doit être après la rentrée.")
        return data


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["name", "schedule", "position"]

    def __init__(self, *args, year, **kwargs):
        super().__init__(*args, **kwargs)
        self.year = year
        self.fields["schedule"].queryset = FeeSchedule.objects.filter(year=year)

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        duplicates = Classroom.objects.filter(year=self.year, name__iexact=name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("Cette classe existe déjà pour cette année.")
        return name


class FeeScheduleForm(forms.ModelForm):
    class Meta:
        model = FeeSchedule
        fields = ["name"]


InstallmentFormSet = inlineformset_factory(
    FeeSchedule,
    Installment,
    fields=["label", "amount", "due_date"],
    widgets={"due_date": DateInput()},
    extra=4,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class StaffCreateForm(forms.Form):
    first_name = forms.CharField(label="Prénom", max_length=150)
    last_name = forms.CharField(label="Nom", max_length=150)
    username = forms.CharField(label="Identifiant de connexion", max_length=150)
    role = forms.ChoiceField(label="Rôle", choices=StaffMember.ROLE_CHOICES, initial=StaffMember.CASHIER)
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput, min_length=8)

    def clean_username(self):
        username = self.cleaned_data["username"].strip().lower()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Cet identifiant est déjà pris.")
        return username

    def clean(self):
        data = super().clean()
        if data.get("password"):
            user = User(username=data.get("username", ""), first_name=data.get("first_name", ""))
            try:
                validate_password(data["password"], user)
            except forms.ValidationError as error:
                self.add_error("password", error)
        return data


class ImportForm(forms.Form):
    file = forms.FileField(label="Fichier CSV (export Excel)")
    create_classes = forms.BooleanField(
        label="Créer automatiquement les classes manquantes", required=False, initial=True
    )


class EnrollmentTransferForm(forms.Form):
    """Réinscription : passer les élèves d'une classe de l'an dernier vers une classe de l'année en cours."""

    source = forms.ModelChoiceField(queryset=Classroom.objects.none(), label="Classe de l'an dernier")
    target = forms.ModelChoiceField(queryset=Classroom.objects.none(), label="Nouvelle classe")

    def __init__(self, *args, previous_year, current_year, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["source"].queryset = Classroom.objects.filter(year=previous_year)
        self.fields["target"].queryset = Classroom.objects.filter(year=current_year)

