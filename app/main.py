import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Wire up our actual engine components
from app.parser import SlimJimParser
from app.compiler import SlimJimCompiler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("slimjim")

app = FastAPI(title="Slim Jim", version="1.0.0")

# Singletons initialized for the lifecycle of the app
pdf_parser = SlimJimParser()
pdf_compiler = SlimJimCompiler()

class RenderRequest(BaseModel):
    html: str
    preset: str = "a4"

# Ensure this matches the exact route your tests are calling!
@app.post("/v1/generate-pdf", response_class=StreamingResponse, status_code=status.HTTP_200_OK)
async def render_pdf(payload: RenderRequest):
    try:
        # Run the real isolation pass
        sanitized_soup = pdf_parser.sanitize_and_normalize(payload.html)
        
        # Run the real layout engine execution pass
        pdf_stream = pdf_compiler.build_pdf_stream(sanitized_soup, page_size_preset=payload.preset)
        
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=document.pdf"}
        )
    except Exception as e:
        logger.error(f"Pipeline Execution Panic: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pipeline execution halted due to corrupt asset payloads or unrenderable tree constraints."
        )