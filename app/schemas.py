from pydantic import BaseModel, Field

class PDFGenerationRequest(BaseModel):
    html: str = Field(
        ..., 
        description="Raw semantic HTML string payload to be converted into a PDF.",
        json_schema_extra={
            "example": "<h1>Warehouse Sticker</h1><p>Item: Widget A</p>"
        }
    )