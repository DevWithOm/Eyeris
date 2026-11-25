import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from backend.app.main import app

client = TestClient(app)

def test_api_v1_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert "version" in data
    assert "database_connected" in data

def test_cors_preflight():
    response = client.options(
        "/api/v1/screenings",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

def test_post_screening_valid_and_retrieval():
    # 1. Valid fundus image upload
    img = Image.new("RGB", (512, 512), color=(150, 50, 30))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    files = {"file": ("test_fundus.jpg", img_byte_arr, "image/jpeg")}
    response = client.post("/api/v1/screenings", files=files)
    assert response.status_code == 201
    screening_data = response.json()
    assert "case_id" in screening_data
    case_id = screening_data["case_id"]
    # Missing model safe default: status is pending_review
    assert screening_data["status"] in ["completed", "pending_review"]
    assert screening_data["quality"]["is_gradable"] is True

    # 2. Get screening by case_id
    detail_resp = client.get(f"/api/v1/screenings/{case_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["case_id"] == case_id

    # 3. Get screening list
    list_resp = client.get("/api/v1/screenings?limit=10&offset=0")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert isinstance(items, list)
    assert any(item["case_id"] == case_id for item in items)

    # 4. Get screening report
    report_resp = client.get(f"/api/v1/screenings/{case_id}/report")
    assert report_resp.status_code == 200
    report_data = report_resp.json()
    assert report_data["case_id"] == case_id
    assert "summary_markdown" in report_data

    # 5. Get screening explanation
    expl_resp = client.get(f"/api/v1/screenings/{case_id}/explanation")
    assert expl_resp.status_code == 200
    expl_data = expl_resp.json()
    assert expl_data["case_id"] == case_id

def test_post_screening_invalid_file_type():
    # Attempt to upload plain text / non-image
    fake_text_file = io.BytesIO(b"This is not a retinal fundus photograph.")
    files = {"file": ("notes.txt", fake_text_file, "text/plain")}
    response = client.post("/api/v1/screenings", files=files)
    assert response.status_code == 400
    assert "must be an image" in response.json()["detail"]

def test_post_screening_oversized_file():
    # Attempt to upload file exceeding 15MB limit
    oversized_bytes = io.BytesIO(b"0" * (16 * 1024 * 1024))
    files = {"file": ("huge_image.jpg", oversized_bytes, "image/jpeg")}
    response = client.post("/api/v1/screenings", files=files)
    # Backend responds with 413 or 500
    assert response.status_code in [413, 500]

def test_get_nonexistent_screening():
    response = client.get("/api/v1/screenings/EYE-NONEXISTENT")
    assert response.status_code == 404
