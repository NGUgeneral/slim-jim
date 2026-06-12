import re
from bs4 import BeautifulSoup, Comment

class SlimJimParser:
    def __init__(self):
        self.parser_backend = "html.parser"
        self.unsupported_tags = ["script", "style", "head", "meta", "link", "iframe"]

    def sanitize_and_normalize(self, raw_html: str) -> BeautifulSoup:
        soup = BeautifulSoup(raw_html, self.parser_backend)
        
        # Freeze the descendants layout into a flat list to safely mutate the live tree
        for node in list(soup.descendants):
            if self._should_extract_or_skip(node):
                continue

            if isinstance(node, str):
                self._normalize_text_node(node)
                continue

            self._intercept_vector_assets(node)
                
        return soup

    def _should_extract_or_skip(self, node) -> bool:
        # Parent was already vaporized in a previous iteration
        if node.parent is None and node != node.find_parent(): 
            return True
            
        # Strip out raw markup comments
        if isinstance(node, Comment):
            node.extract()
            return True
            
        # Strip out blacklisted tags along with their entire sub-tree
        if not isinstance(node, str) and node.name in self.unsupported_tags:
            node.extract()
            return True
            
        return False

    def _normalize_text_node(self, node: str) -> None:
        if node.parent and node.parent.name not in ["pre", "code"]:
            normalized_text = re.sub(r'\s+', ' ', node)
            node.replace_with(normalized_text)

    def _intercept_vector_assets(self, node) -> None:
        """
        Audits live tags for Slim Jim HTML5 properties or Base64 images,
        stamping metadata directly onto the scratchpad nodes.
        """
        if node.name == "div":
            if node.has_attr("data-barcode"):
                node["slimjim_type"] = "barcode"
                node["slimjim_value"] = node["data-barcode"]

            elif node.has_attr("data-qrcode"):
                node["slimjim_type"] = "qrcode"
                node["slimjim_value"] = node["data-qrcode"]

        elif node.name == "img":
            src = node.get("src", "")
            if src.startswith("data:image/"):
                try:
                    # "data:image/png;base64,iVBORw0KG..."
                    header, base64_data = src.split(",", 1)
                    mime_type = header.split(";")[0]  # "data:image/png"
                    img_format = mime_type.split("/")[1]  # "png", "jpeg", etc.

                    if img_format not in ["png", "jpeg", "jpg"]:
                        node.extract()
                        return
                    
                    node["slimjim_type"] = "image"
                    node["slimjim_value"] = base64_data
                except IndexError:
                    # Defensive purge: Malformed data URI asset structure gets vaporized
                    node.extract()