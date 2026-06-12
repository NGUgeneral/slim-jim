import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# A clean, minimal 1x1 pixel base64 encoded PNG for testing valid graphics
VALID_BASE64_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

# A completely garbage, truncated base64 string designed to crash Pillow/ReportLab
CORRUPT_BASE64_IMAGE = "data:image/png;base64,dGhpc19pc19ub3RfYW5faW1hZ2VfZmlsZQ=="

class TestSlimJimPipeline:

    def test_render_golden_path_success(self):
        """
        GIVEN a structurally pristine warehouse label template HTML
        WHEN submitted to the /render endpoint with a thermal preset
        THEN expect an HTTP 200 status and valid PDF binary magic headers.
        """
        payload = {
            "preset": "label_4x6",
            "html": f"""
            <html>
                <body>
                    <h1>LOGISTICS PICK SHEET</h1>
                    <p>Order Reference: #NL-98234</p>
                    <br/>
                    <div data-barcode="SHIP-NL-98234"></div>
                    <div data-qrcode="https://slimjim.io/verify/98234"></div>
                    <img src="data:image/png;base64,{VALID_BASE64_PNG}" width="100" height="50" />
                </body>
            </html>
            """
        }
        
        response = client.post("/v1/generate-pdf", json=payload)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        
        # Verify the standard PDF File Signature / Magic Bytes (%PDF-1.4)
        binary_content = response.content
        assert binary_content.startswith(b"%PDF")

    def test_render_unsupported_image_gracefully_stripped(self):
        """
        GIVEN an image asset with an unsupported format (.webp)
        WHEN the document is processed
        THEN the parser must extract it cleanly, and the PDF should render without it.
        """
        payload = {
            "preset": "a4",
            "html": """
            <html>
                <body>
                    <p>This document contains an unsupport webp logo.</p>
                    <img src="data:image/webp;base64,UklGRhoAAABXRUJQVlA4TA0AAAAvAAAAEAcQERGIiP4H" />
                </body>
            </html>
            """
        }
        
        response = client.post("/v1/generate-pdf", json=payload)
        
        # The parser silently strips webp, meaning compilation moves along safely.
        assert response.status_code == 200
        assert response.content.startswith(b"%PDF")

    def test_render_corrupt_binary_triggers_hard_500_panic(self):
        """
        GIVEN a valid image type but structurally corrupted, un-decodable base64 content
        WHEN passed through to the downstream compiler
        THEN the compiler must trigger a hard crash, bubbling up to an HTTP 500.
        """
        payload = {
            "preset": "letter",
            "html": f"""
            <html>
                <body>
                    <h1>Invoice Breakdown</h1>
                    <img src="{CORRUPT_BASE64_IMAGE}" width="50" height="50" />
                </body>
            </html>
            """
        }
        
        response = client.post("/v1/generate-pdf", json=payload)
        
        print("CRASH TEST BODY DETECTED:", response.text[:500])

        # Enforce our strict fail-fast rule: no partial/weird PDFs allowed out.
        assert response.status_code == 500
        assert "Pipeline execution halted" in response.json()["detail"]