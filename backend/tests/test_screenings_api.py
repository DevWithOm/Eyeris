import io
from fastapi.testclient import TestClient
from PIL import Image
from backend.app.main import app

client = TestClient(app)

def test_api_v1_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "database_connected" in data

def test_post_screening_and_get_details():
    # Create an in-memory test image
    img = Image.new("RGB", (512, 512), color=(150, 50, 30))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    # 1. Post screening
    files = {"file": ("test_fundus.jpg", img_byte_arr, "image/jpeg")}
    response = client.post("/api/v1/screenings", files=files)
    assert response.status_code == 201
    screening_data = response.json()
    assert "case_id" in screening_data
    case_id = screening_data["case_id"]
    assert screening_data["status"] == "completed"

    # 2. Get screening by case_id
    detail_resp = client.get(f"/api/v1/screenings/{case_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["case_id"] == case_id
    assert detail_data["predicted_grade"] in [0, 1, 2, 3, 4]

    # 3. Get screening report
    report_resp = client.get(f"/api/v1/screenings/{case_id}/report")
    assert report_resp.status_code == 200
    report_data = report_resp.json()
    assert report_data["case_id"] == case_id
    assert "summary_markdown" in report_data

    # 4. Get screening explanation
    expl_resp = client.get(f"/api/v1/screenings/{case_id}/explanation")
    assert expl_resp.status_code == 200
    expl_data = expl_resp.json()
    assert expl_data["case_id"] == case_id
    assert "calibrated_confidence" in expl_data

def test_get_nonexistent_screening():
    response = client.get("/api/v1/screenings/EYE-NONEXISTENT")
    assert response.status_code == 404
