"""
Ouvre le compte d'une nouvelle école cliente et de son directeur.

    python manage.py creer_ecole --nom "Groupe Scolaire La Réussite" --ville Yopougon \
        --directeur kone.awa --telephone "07 07 07 07 07"
"""
import secrets

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from ecoles.models import School, StaffMember
from ecoles.utils import COUNTRIES, DEFAULT_CURRENCY_BY_COUNTRY


class Command(BaseCommand):
    help = "Crée une école cliente et le compte de sa direction."

    def add_arguments(self, parser):
        parser.add_argument("--nom", required=True, help="Nom de l'établissement")
        parser.add_argument("--pays", default="CI", choices=sorted(COUNTRIES), help="Code pays (CI, SN, CM…)")
        parser.add_argument("--ville", default="")
        parser.add_argument("--telephone", default="")
        parser.add_argument("--directeur", required=True, help="Identifiant de connexion de la direction")
        parser.add_argument("--mot-de-passe", dest="password", help="Sinon un mot de passe aléatoire est généré")
        parser.add_argument("--prix", type=int, default=500, help="Prix par élève et par an")

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        username = options["directeur"].strip().lower()
        if User.objects.filter(username__iexact=username).exists():
            raise CommandError(f"L'identifiant « {username} » existe déjà.")

        base_slug = slugify(options["nom"])[:40] or "ecole"
        slug, index = base_slug, 2
        while School.objects.filter(slug=slug).exists():
            slug, index = f"{base_slug}-{index}", index + 1

        school = School.objects.create(
            name=options["nom"],
            slug=slug,
            country=options["pays"],
            currency=DEFAULT_CURRENCY_BY_COUNTRY.get(options["pays"], "XOF"),
            city=options["ville"],
            phone=options["telephone"],
            price_per_student=options["prix"],
        )
        password = options["password"] or secrets.token_urlsafe(9)
        user = User.objects.create_user(username, password=password)
        StaffMember.objects.create(user=user, school=school, role=StaffMember.DIRECTOR)

        self.stdout.write(self.style.SUCCESS(f"École « {school.name} » créée."))
        self.stdout.write(f"Identifiant : {username}")
        self.stdout.write(f"Mot de passe : {password}  (à changer à la première connexion)")
