"""
Import d'élèves depuis un fichier CSV exporté d'Excel.

Excel en français enregistre souvent en « CSV (séparateur : point-virgule) »
et en Windows-1252 : on accepte les deux séparateurs et les deux encodages.
Les colonnes sont reconnues par leur titre, avec ou sans accents.
"""
import csv
import io
import unicodedata
from dataclasses import dataclass, field

from django.db import transaction

from .models import Classroom, Enrollment, Student
from .utils import normalize_phone

COLUMN_ALIASES = {
    "last_name": {"nom", "nom de famille", "nom eleve"},
    "first_name": {"prenom", "prenoms", "prenom(s)"},
    "classroom": {"classe", "niveau", "salle"},
    "matricule": {"matricule", "numero", "n matricule", "id"},
    "gender": {"sexe", "genre"},
    "parent_name": {"parent", "nom du parent", "tuteur", "parent/tuteur", "nom parent"},
    "parent_phone": {"telephone", "tel", "contact", "telephone parent", "tel parent", "telephone 1", "contact parent"},
    "parent_phone2": {"telephone 2", "tel 2", "autre telephone", "contact 2"},
    "discount": {"remise", "reduction", "bourse"},
}

TEMPLATE_HEADER = ["Nom", "Prénoms", "Classe", "Matricule", "Sexe", "Parent", "Téléphone", "Téléphone 2", "Remise"]


def _simplify(text):
    text = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode()
    return " ".join(text.lower().replace("_", " ").replace(".", " ").split())


def decode(raw_bytes):
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode("latin-1")


@dataclass
class ImportReport:
    created: int = 0
    updated: int = 0
    classes_created: list = field(default_factory=list)
    errors: list = field(default_factory=list)  # (n° de ligne, message)
    warnings: list = field(default_factory=list)


def import_students(raw_bytes, school, year, create_classes=True):
    text = decode(raw_bytes)
    sample = text[:2048]
    delimiter = ";" if sample.count(";") >= sample.count(",") else ","
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    report = ImportReport()
    try:
        header = next(reader)
    except StopIteration:
        report.errors.append((1, "Le fichier est vide."))
        return report

    columns = {}
    for index, title in enumerate(header):
        simple = _simplify(title)
        for key, aliases in COLUMN_ALIASES.items():
            if simple in aliases and key not in columns:
                columns[key] = index
    missing = [label for key, label in (("last_name", "Nom"), ("classroom", "Classe")) if key not in columns]
    if missing:
        report.errors.append((1, f"Colonnes obligatoires introuvables : {', '.join(missing)}."))
        return report

    classrooms = {_simplify(c.name): c for c in Classroom.objects.filter(year=year)}

    with transaction.atomic():
        for line_number, row in enumerate(reader, start=2):
            if not any(cell.strip() for cell in row):
                continue

            def value(key):
                index = columns.get(key)
                return row[index].strip() if index is not None and index < len(row) else ""

            last_name, class_name = value("last_name"), value("classroom")
            if not last_name or not class_name:
                report.errors.append((line_number, "Nom ou classe manquant."))
                continue
            classroom = classrooms.get(_simplify(class_name))
            if classroom is None:
                if not create_classes:
                    report.errors.append((line_number, f"Classe inconnue : {class_name}."))
                    continue
                classroom = Classroom.objects.create(school=school, year=year, name=class_name)
                classrooms[_simplify(class_name)] = classroom
                report.classes_created.append(class_name)

            discount_text = value("discount").replace(" ", "").replace(" ", "").replace(" ", "")
            try:
                discount = int(float(discount_text.replace(",", "."))) if discount_text else 0
            except ValueError:
                report.errors.append((line_number, f"Remise illisible : {value('discount')}."))
                continue

            phone = value("parent_phone")
            if phone and not normalize_phone(phone, school.country):
                report.warnings.append((line_number, f"Téléphone à vérifier : {phone}."))

            gender = value("gender").upper()[:1]
            fields = {
                "last_name": last_name,
                "first_name": value("first_name"),
                "parent_name": value("parent_name"),
                "parent_phone": phone,
                "parent_phone2": value("parent_phone2"),
                "gender": gender if gender in ("F", "M") else "",
            }
            matricule = value("matricule")
            student = None
            if matricule:
                student = Student.objects.filter(school=school, matricule__iexact=matricule).first()
            if student:
                for name, field_value in fields.items():
                    if field_value:
                        setattr(student, name, field_value)
                student.save()
                report.updated += 1
            else:
                student = Student.objects.create(school=school, matricule=matricule, **fields)
                report.created += 1
            Enrollment.objects.update_or_create(
                student=student,
                year=year,
                defaults={"classroom": classroom, "discount": max(0, discount), "is_active": True},
            )
    return report


def template_csv():
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(TEMPLATE_HEADER)
    writer.writerow(["KOUASSI", "Aya Grâce", "CM2 A", "2026-001", "F", "KOUASSI Jean", "07 07 07 07 07", "", "0"])
    return "﻿" + buffer.getvalue()
