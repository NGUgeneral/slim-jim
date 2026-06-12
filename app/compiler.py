import base64
from io import BytesIO
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import code128
from reportlab.graphics.barcode.qr import QrCodeWidget

class SlimJimCompiler:
    def __init__(self):
        self.PRESETS = {
            "a4": A4,
            "letter": LETTER,
            "label_4x6": (4 * inch, 6 * inch),
            "label_4x4": (4 * inch, 4 * inch)
        }
        self.styles = getSampleStyleSheet()
        self._init_custom_styles()

    def _init_custom_styles(self):
        self.body_style = ParagraphStyle(
            'SlimJimBody',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14
        )

    def build_pdf_stream(self, sanitized_soup, page_size_preset: str = "a4") -> BytesIO:
        """
        Ingests the sanitized DOM, loops through the elements, 
        and maps them straight to ReportLab Flowables. Any structural or 
        binary corruption will intentionally throw a hard crash.
        """
        pdf_buffer = BytesIO()
        resolved_pagesize = self.PRESETS.get(page_size_preset.lower(), A4)
        margin = 54 if resolved_pagesize[0] > (5 * inch) else 10
        
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=resolved_pagesize,
            leftMargin=margin, rightMargin=margin,
            topMargin=margin, bottomMargin=margin
        )
        
        story = []
        root_node = sanitized_soup.body if sanitized_soup.body else sanitized_soup
        self._compile_node(root_node, story)

        doc.build(story)
        
        pdf_buffer.seek(0)
        return pdf_buffer

    def _compile_node(self, current_node, story: list) -> None:
        """Iterates through DOM sub-nodes and converts them into layout Flowables."""
        for child in current_node.children:
            if isinstance(child, str):
                text = child.strip()
                if text:
                    story.append(Paragraph(text, self.body_style))
                continue

            if child.has_attr("slimjim_type"):
                self._handle_vector_element(child, story)
                continue

            if child.name in ["p", "span", "h1", "h2", "h3", "h4", "h5", "h6"]:
                text = child.get_text().strip()
                if text:
                    story.append(Paragraph(text, self.body_style))
                    
            elif child.name == "br":
                story.append(Spacer(1, 10))
                
            elif child.name in ["div", "section", "article"]:
                self._compile_node(child, story)

    def _handle_vector_element(self, node, story: list) -> None:
        sj_type = node["slimjim_type"]
        val = node["slimjim_value"]

        if sj_type == "barcode":
            barcode_value = node.get("data-barcode")
            bc = code128.Code128(barcode_value, barWidth=1.2, barHeight=50)
            story.append(bc)

        elif sj_type == "qrcode":
            qr_code_value = node.get("data-qrcode")
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

        elif sj_type == "image":
            img_bytes = base64.b64decode(val)
            img_stream = BytesIO(img_bytes)

            reader = ImageReader(img_stream)
            pixel_w, pixel_h = reader.getSize()
            
            html_w = node.get("width")
            html_h = node.get("height")
            
            if html_w and html_h:
                w = float(html_w)
                h = float(html_h)
            else:
                w = float(pixel_w)
                h = float(pixel_h)
            
            story.append(Image(img_stream, width=w, height=h))