import re
from bs4 import BeautifulSoup, Comment

class SlimJimParser:
    def __init__(self):
        # We explicitly enforce the native standard-library html.parser to avoid external binary bloat
        self.parser_backend = "html.parser"
        
        # Blacklisted structural nodes that have no business existing in an air-gapped PDF layout
        self.unsupported_tags = ["script", "style", "head", "meta", "link", "iframe"]

    def sanitize_and_normalize(self, raw_html: str) -> BeautifulSoup:
        soup = BeautifulSoup(raw_html, self.parser_backend)
        
        # Freeze the descendants into a list to safely mutate the underlying DOM tree
        for node in list(soup.descendants):
            # Safe Guard: If this node's parent was already extracted in a previous 
            # step of this loop, skip it entirely to avoid processing ghost elements.
            if node.parent is None and node != soup:
                continue

            if isinstance(node, Comment):
                node.extract()
                continue

            if isinstance(node, str):
                if node.parent and node.parent.name not in ["pre", "code"]:
                    normalized_text = re.sub(r'\s+', ' ', node)
                    node.replace_with(normalized_text)

            elif node.name in self.unsupported_tags:
                node.extract()
                
        return soup