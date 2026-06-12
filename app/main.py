from io import BytesIO
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse

from .schemas import PDFGenerationRequest

app = FastAPI(
    title="Slim Jim",
    description="A Lean HTML-to-PDF Converter Service",
    version="1.0.0"
)

@app.post(
    "/v1/generate-pdf",
    response_class=StreamingResponse,
    summary="Convert raw HTML into a streaming PDF binary",
    status_code=status.HTTP_200_OK
)
async def generate_pdf(payload: PDFGenerationRequest) -> StreamingResponse:
    try:
        dummy_buffer = BytesIO()
        dummy_buffer.write(b"%PDF-1.4 Baseline Placeholder Stream")
        dummy_buffer.seek(0)
        
        return StreamingResponse(
            dummy_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=document.pdf",
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compile PDF document stream: {str(e)}"
        )