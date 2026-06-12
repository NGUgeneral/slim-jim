import base64
from io import BytesIO
from abc import ABC, abstractmethod
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter, A4
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import code128
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.lib.utils import ImageReader

class VectorElementHandler(ABC):
    @abstractmethod
    def compile(self, node, story: list) -> None:
        """Process a specific element node and mutate the ReportLab story."""
        pass


class BarcodeHandler(VectorElementHandler):
    def compile(self, node, story: list) -> None:
        barcode_value = node.get("data-barcode")
        if not barcode_value:
            return
        bc = code128.Code128(barcode_value, barWidth=1.2, barHeight=50)
        story.append(bc)


class QrCodeHandler(VectorElementHandler):
    def compile(self, node, story: list) -> None:
        qr_code_value = node.get("data-qrcode")
        if not qr_code_value:
            return
            
        w = float(node.get("width", 100))
        h = float(node.get("height", 100))
        
        qr = QrCodeWidget(qr_code_value)
        qr.barWidth = w
        qr.barHeight = h

        bounds = qr.getBounds()
        qr_w = bounds[2] - bounds[0]
        qr_h = bounds[3] - bounds[1]

        d = Drawing(qr_w, qr_h)
        d.add(qr)
        story.append(d)


class ImageHandler(VectorElementHandler):
    def compile(self, node, story: list) -> None:
        val = node.get("slimjim_value")
        if not val:
            return
            
        img_bytes = base64.b64decode(val)
        img_stream = BytesIO(img_bytes)

        reader = ImageReader(img_stream)
        pixel_w, pixel_h = reader.getSize()
        
        w = float(node.get("width", pixel_w))
        h = float(node.get("height", pixel_h))
        
        story.append(Image(img_stream, width=w, height=h))


class SlimJimCompiler:
    def __init__(self):
        self._presets = {
            "letter": letter,
            "a4": A4,
            "label_4x6": (288, 432)  # 4x6 inches in PostScript points
        }

        self._handlers = {
            "barcode": BarcodeHandler(),
            "qrcode": QrCodeHandler(),
            "image": ImageHandler()
        }

    def build_pdf_stream(self, soup, page_size_preset: str = "a4") -> BytesIO:
        """Orchestrates document construction from a sanitized BeautifulSoup tree."""
        pagesize = self._presets.get(page_size_preset, A4)
        pdf_buffer = BytesIO()
        
        # 0.5 inch safety margin constraints
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=pagesize,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        
        story = []
        root_node = soup.find("body") or soup
        
        self._compile_node(root_node, story)
        
        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer

    def _compile_node(self, current_node, story: list) -> None:
        styles = getSampleStyleSheet()
        
        for child in current_node.children:
            if child.name is None:
                continue

            if child.has_attr("slimjim_type"):
                self._handle_vector_element(child, story)
                continue

            if child.name in ["h1", "h2", "h3", "p"]:
                style_map = {
                    "h1": "Heading1",
                    "h2": "Heading2",
                    "h3": "Heading3",
                    "p": "BodyText"
                }
                text_content = child.get_text(strip=True)
                if text_content:
                    story.append(Paragraph(text_content, styles[style_map[child.name]]))
                    
            elif child.name == "br":
                story.append(Spacer(1, 10))

            if child.element_classes if hasattr(child, 'element_classes') else child.contents:
                self._compile_node(child, story)

    def _handle_vector_element(self, node, story: list) -> None:
        sj_type = node["slimjim_type"]
        
        handler = self._handlers.get(sj_type)
        if not handler:
            raise ValueError(f"Unsupported layout element type encountered: '{sj_type}'")
            
        handler.compile(node, story)