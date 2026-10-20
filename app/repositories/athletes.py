from __future__ import annotations

import csv
import io
import sqlite3
from datetime import date, datetime
from typing import TypedDict

from pydantic import ValidationError

from app.categories import age_category
from app.errors import ApiError, ConflictError
from app.repositories.common import fetch_or_404
from app.schemas import AthleteCreate, AthleteOut

# Export CSV de la fédération : séparateur « ; », dates jj/mm/aaaa.
CSV_REQUIRED_COLUMNS = ("nom", "prenom", "date_naissance", "sexe", "licence")
CSV_FIELD_COLUMNS = {
    "last_name": "nom",
    "first_name": "prenom",
    "birth_date": "date_naissance",
    "sex": "sexe",
    "club": "club",
    "license_number": "licence",
    "medical_certificate_valid_until": "certificat_valide_jusqu",
}


class ImportLineError(TypedDict):
    line: int
    message: str


class ImportResult(TypedDict):
    created: int
    skipped: int
    errors: list[ImportLineError]


def _to_athlete(row: sqlite3.Row) -> AthleteOut:
    birth_date = date.fromisoformat(row["birth_date"])
    certificate = row["medical_certificate_valid_until"]
    return AthleteOut(
        id=row["id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        birth_date=birth_date,
        sex=row["sex"],
        club=row["club"],
        license_number=row["license_number"],
        medical_certificate_valid_until=date.fromisoformat(certificate) if certificate else None,
        category=age_category(birth_date),
    )


def list_athletes(conn: sqlite3.Connection, club: str | None = None) -> list[AthleteOut]:
    sql = "SELECT * FROM athletes"
    params: tuple[str, ...] = ()
    if club is not None:
        sql += " WHERE club = ?"
        params = (club,)
    sql += " ORDER BY last_name, first_name, id"
    return [_to_athlete(row) for row in conn.execute(sql, params)]


def get_athlete(conn: sqlite3.Connection, athlete_id: int) -> AthleteOut:
    row = fetch_or_404(
        conn,
        "SELECT * FROM athletes WHERE id = ?",
        (athlete_id,),
        f"Athlète {athlete_id} introuvable",
    )
    return _to_athlete(row)


def create_athlete(conn: sqlite3.Connection, data: AthleteCreate) -> AthleteOut:
    existing = conn.execute(
        "SELECT id FROM athletes WHERE license_number = ?", (data.license_number,)
    ).fetchone()
    if existing is not None:
        raise ConflictError(f"Licence {data.license_number} déjà enregistrée")

    certificate = data.medical_certificate_valid_until
    cursor = conn.execute(
        "INSERT INTO athletes (first_name, last_name, birth_date, sex, club, license_number,"
        " medical_certificate_valid_until) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            data.first_name,
            data.last_name,
            data.birth_date.isoformat(),
            data.sex.value,
            data.club,
            data.license_number,
            certificate.isoformat() if certificate else None,
        ),
    )
    row = conn.execute("SELECT * FROM athletes WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _to_athlete(row)


def _parse_csv_date(column: str, value: str) -> date | None:
    value = value.strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError:
        raise ValueError(f"{column} : date invalide « {value} » (attendu jj/mm/aaaa)") from None


def _athlete_from_csv_row(row: dict[str, str | None]) -> AthleteCreate:
    def cell(column: str) -> str:
        return (row.get(column) or "").strip()

    return AthleteCreate.model_validate(
        {
            "last_name": cell("nom"),
            "first_name": cell("prenom"),
            "birth_date": _parse_csv_date("date_naissance", cell("date_naissance")),
            "sex": cell("sexe"),
            "club": cell("club") or None,
            "license_number": cell("licence"),
            "medical_certificate_valid_until": _parse_csv_date(
                "certificat_valide_jusqu", cell("certificat_valide_jusqu")
            ),
        }
    )


def _validation_message(error: ValidationError) -> str:
    return " ; ".join(
        f"{CSV_FIELD_COLUMNS.get(str(e['loc'][0]), e['loc'][0])} : {e['msg']}"
        for e in error.errors()
    )


def import_athletes_csv(conn: sqlite3.Connection, content: bytes) -> ImportResult:
    """Importe un export CSV : une licence déjà connue est ignorée, une ligne invalide est
    signalée avec son numéro (en-tête = ligne 1) sans bloquer les suivantes."""
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ApiError("Le fichier CSV doit être encodé en UTF-8") from None

    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=";")
    missing = [c for c in CSV_REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise ApiError(f"Colonnes manquantes dans l'en-tête CSV : {', '.join(missing)}")

    result: ImportResult = {"created": 0, "skipped": 0, "errors": []}
    for row in reader:
        try:
            data = _athlete_from_csv_row(row)
        except ValueError as exc:  # ValidationError en hérite
            message = _validation_message(exc) if isinstance(exc, ValidationError) else str(exc)
            result["errors"].append({"line": reader.line_num, "message": message})
            continue
        try:
            create_athlete(conn, data)
        except ConflictError:
            result["skipped"] += 1
        else:
            result["created"] += 1
    return result
