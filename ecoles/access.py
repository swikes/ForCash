"""
Cloisonnement des écoles : chaque vue du personnel passe par `staff_required`,
qui attache l'école de l'utilisateur à la requête. Toutes les requêtes en base
filtrent ensuite sur `request.school` : une école ne voit jamais les données
d'une autre.
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from .models import StaffMember


def get_staff(user):
    if not user.is_authenticated:
        return None
    try:
        return user.staff
    except StaffMember.DoesNotExist:
        return None


def staff_required(view=None, *, director=False, needs_year=True):
    def decorator(func):
        @login_required
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            staff = get_staff(request.user)
            if staff is None:
                if request.user.is_superuser:
                    return redirect("admin:index")
                return render(request, "ecoles/no_school.html", status=403)
            if not staff.school.is_active:
                return render(request, "ecoles/no_school.html", {"suspended": True}, status=403)
            if director and not staff.is_director:
                raise PermissionDenied("Réservé à la direction.")
            request.staff = staff
            request.school = staff.school
            request.year = staff.school.current_year
            if needs_year and request.year is None:
                if staff.is_director:
                    messages.info(request, "Commencez par créer l'année scolaire en cours.")
                    return redirect("year_create")
                return render(request, "ecoles/no_school.html", {"no_year": True}, status=403)
            return func(request, *args, **kwargs)

        return wrapper

    return decorator(view) if view else decorator
