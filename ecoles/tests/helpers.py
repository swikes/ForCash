from datetime import date

from django.contrib.auth import get_user_model

from ecoles.models import (
    Classroom,
    Enrollment,
    FeeSchedule,
    Installment,
    School,
    SchoolYear,
    StaffMember,
    Student,
)

PASSWORD = "Mot-de-passe-test-2026"


def make_school(slug="ecole-a", **kwargs):
    defaults = {"name": f"École {slug}", "country": "CI", "currency": "XOF"}
    defaults.update(kwargs)
    school = School.objects.create(slug=slug, **defaults)
    year = SchoolYear.objects.create(
        school=school, name="2026-2027", start_date=date(2026, 9, 1), end_date=date(2027, 7, 15), is_current=True
    )
    schedule = FeeSchedule.objects.create(school=school, year=year, name="Primaire")
    for label, amount, due in [
        ("Inscription", 30000, date(2026, 9, 1)),
        ("1re tranche", 70000, date(2026, 10, 1)),
        ("2e tranche", 60000, date(2027, 1, 10)),
    ]:
        Installment.objects.create(schedule=schedule, label=label, amount=amount, due_date=due)
    classroom = Classroom.objects.create(school=school, year=year, name="CM2 A", schedule=schedule)
    return school, year, classroom


def make_user(school, username, role=StaffMember.DIRECTOR):
    user = get_user_model().objects.create_user(username, password=PASSWORD)
    StaffMember.objects.create(user=user, school=school, role=role)
    return user


def make_student(school, year, classroom, last_name="KOUASSI", phone="07 07 07 07 07", discount=0):
    student = Student.objects.create(
        school=school, last_name=last_name, first_name="Aya", parent_name="KOUASSI Jean", parent_phone=phone
    )
    enrollment = Enrollment.objects.create(student=student, year=year, classroom=classroom, discount=discount)
    return student, enrollment
