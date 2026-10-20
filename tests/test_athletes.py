from datetime import date
from pathlib import Path


def test_create_athlete_returns_201_with_category(client):
    birth_date = date(date.today().year - 30, 3, 2)

    response = client.post(
        "/athletes",
        json={
            "first_name": "Inès",
            "last_name": "Morel",
            "birth_date": birth_date.isoformat(),
            "sex": "F",
            "license_number": "DOS-000042",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "SENIOR"
    assert body["club"] is None


def test_create_athlete_rejects_duplicate_license(client, make_athlete):
    athlete = make_athlete()

    response = client.post(
        "/athletes",
        json={
            "first_name": "Hugo",
            "last_name": "Lemaire",
            "birth_date": "1995-05-20",
            "sex": "M",
            "license_number": athlete["license_number"],
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_get_athlete_returns_200_with_category(client, make_athlete):
    athlete = make_athlete("Durand")

    response = client.get(f"/athletes/{athlete['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == athlete["id"]
    assert body["last_name"] == "Durand"
    assert body["category"] == "SENIOR"


def test_get_athlete_unknown_returns_404(client):
    response = client.get("/athletes/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_get_athlete_invalid_id_returns_422(client):
    response = client.get("/athletes/abc")

    assert response.status_code == 422


def test_list_athletes_filters_by_club(client, make_athlete):
    make_athlete("Durand", club="AC Rivebelle")
    make_athlete("Petit", club="Stade Nordval")

    response = client.get("/athletes", params={"club": "AC Rivebelle"})

    assert response.status_code == 200
    assert [a["last_name"] for a in response.json()] == ["Durand"]


CSV_EXEMPLE = Path(__file__).parent.parent / "scripts" / "legacy" / "licencies_exemple.csv"


def _import_csv(client, content: bytes):
    return client.post("/athletes/import", content=content, headers={"Content-Type": "text/csv"})


def test_import_athletes_csv_creates_skips_and_reports_errors(client):
    response = _import_csv(client, CSV_EXEMPLE.read_bytes())

    assert response.status_code == 200
    body = response.json()
    assert (body["created"], body["skipped"]) == (17, 1)
    assert [e["line"] for e in body["errors"]] == [15, 16]
    assert len(client.get("/athletes").json()) == 17


def test_import_athletes_csv_reimport_skips_everything_known(client):
    content = CSV_EXEMPLE.read_bytes()
    _import_csv(client, content)

    response = _import_csv(client, content)

    assert response.status_code == 200
    body = response.json()
    assert (body["created"], body["skipped"]) == (0, 18)
    assert [e["line"] for e in body["errors"]] == [15, 16]


def test_import_athletes_csv_converts_dates_and_optional_fields(client):
    _import_csv(client, CSV_EXEMPLE.read_bytes())

    athletes = {a["license_number"]: a for a in client.get("/athletes").json()}

    assert athletes["DOS-900101"]["birth_date"] == "1998-03-14"
    assert athletes["DOS-900101"]["medical_certificate_valid_until"] == "2027-09-30"
    assert athletes["DOS-900104"]["medical_certificate_valid_until"] is None
    assert athletes["DOS-900109"]["club"] is None


def test_import_athletes_csv_missing_columns_returns_400(client):
    response = _import_csv(client, b"nom;prenom\nValette;Margaux\n")

    assert response.status_code == 400
    assert "date_naissance" in response.json()["error"]["message"]


def test_import_athletes_csv_empty_body_returns_422(client):
    response = _import_csv(client, b"")

    assert response.status_code == 422


def test_import_athletes_csv_rejects_non_utf8_with_400(client):
    response = _import_csv(client, "nom;prenom\nÉlias;X\n".encode("latin-1"))

    assert response.status_code == 400
