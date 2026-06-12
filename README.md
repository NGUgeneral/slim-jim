# Slim Jim

### The Lean, Zero-Browser HTML-to-PDF Microservice

**Slim Jim** is an ultra-lightweight, high-performance Python microservice designed explicitly to convert structured semantic HTML into production-grade transaction documents, warehouse stickers, and logistics labels.

Most modern HTML-to-PDF solutions are heavyweights. They drag in headless browser binaries (Chromium/Playwright) that balloon deployment footprints to nearly a gigabyte, murder serverless cold starts, and require complex container orchestration. 

Slim Jim takes the opposite approach. It treats HTML not as a visual CSS playground, but as a structured intent tree. By combining a lean DOM parser with a low-level graphics compiler, Slim Jim bypasses the browser entirely—generating pixel-perfect vector PDFs entirely in memory using a fraction of the resources.

---

## MVP Architecture & Scope

The Minimum Viable Product (MVP) enforces a strict, air-gapped pipeline with a microscopic attack surface. It relies on exactly **three highly vetted production dependencies**: `FastAPI` (network), `BeautifulSoup4` (parsing), and `ReportLab` (graphics generation).

```
Raw HTML Payload ──► [ FastAPI Gateway ] ──► [ BeautifulSoup4 DOM Tree ]
                                                            │
Streaming PDF Binary ◄── [ ReportLab Engine ] ◄── [ Custom Tag Adapter ]
```

### Core Features

* **Zero-Disk I/O Pipeline:** Accepting an HTML string via a secure `POST` endpoint, Slim Jim parses, budgets, and compiles the document entirely in memory, streaming the raw binary bytes back instantly via an HTTP `StreamingResponse`. 
* **Native Vector Barcodes & QR Codes:** No external image generators, no network fetching. By intercepting custom data attributes (`data-barcode`, `data-qrcode`), Slim Jim instructs the underlying engine to draw mathematically perfect vector lines and grids. They remain crisp and scan flawlessly at any resolution—even on 200 DPI warehouse thermal printers.
* **Serverless Native Footprint:** With a total unzipped deployment package size under **30 MB**, Slim Jim easily deploys as a standard zip file or AWS Lambda Layer. Cold starts are negligible, and memory overhead stays below 80 MB per execution.

### Strict MVP Constraints

To maintain its extreme speed and architectural elegance, Slim Jim intentionally trades away general-purpose web rendering capabilities:
* **No CSS Layout Engine:** Global CSS files, float properties, Flexbox, and CSS Grid are completely ignored. Document layout is dictated strictly by semantic block-level HTML tags (`<h1>`, `<p>`, `<br>`) and tabular data structures (`<table>`, `<tr>`, `<td>`).
* **No External Asset Fetching:** Outbound network connections are completely eliminated. If corporate logos or stamp graphics are required, they must be embedded inline directly inside the HTML payload as explicit Base64 Data URIs specifying strict height and width boundaries.
