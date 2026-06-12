# Slim Jim: A Lean Html to PDF Converter 

## About Slim Jim

Slim Jim was engineered to solve a very specific problem: **high-load, simple-layout PDF generation.** Not every HTML-to-PDF pipeline requires a Swiss Army knife level of layout detail or a complete web-rendering runtime. When your goal is to generate hundreds of thousands of "primitive" files—like barcodes, shipping labels, thermal tags, or picking receipts in a fast-paced warehouse—you don't need a heavy browser layout engine to draw text and vector shapes. Slim Jim is a lean, tailored solution for exactly these high-velocity situations.

It acts as an ultra-fast, stateless compilation bridge that translates a highly optimized, simplified HTML subset directly into native ReportLab canvas instructions. 

### Core Architectural Features:

* **Engineered for AWS Lambda & Serverless:** By keeping its dependency tree razor-thin (FastAPI, BeautifulSoup, ReportLab), Slim Jim achieves an incredibly small CPU and memory footprint. You don't need a heavy, multi-gigabyte container image or a costly, always-on server instance. It is lightweight enough to boot instantly on AWS Lambda, effectively erasing cold-start penalties and eliminating infrastructure waste where costs quickly add up.
* **Drop-in Codebase as Feature:** Because the core engine logic is exceptionally compact and modular, you aren't forced to maintain Slim Jim as an isolated, standalone microservice network dependency. It is simple enough to be cleanly pasted straight into your existing Python backend codebase as an internal application utility or shared module without bloating your repository or muddying your architecture.
* **Zero Network or Disk Delays:** To maintain extreme processing speeds, Slim Jim operates entirely in an air-gapped, inline-only environment. All structural graphics, 1D logistics barcodes, and logos must be passed directly inside the request stream as inline attributes or Base64 data strings. The service never makes outbound network calls to fetch external assets and never writes temporary files to a disk.
* **No Silent Layout Failures:** Most document generators try to be overly resilient when encountering bad data—silently stripping out unparseable code blocks or writing a broken, half-empty layout. Slim Jim handles boundaries strictly. If an image stream is corrupt or a layout constraint is broken, it fails fast and triggers an immediate HTTP 500 panic. This guarantees that unreadable or corrupted barcodes never silently pollute your physical fulfillment pipeline.
* **ReportLab Under the Hood:** The low-level PDF building blocks, canvas coordinates, and flowable engines are fully abstracted behind a clean Strategy pattern. While this isolates the rest of your application code from layout quirks, it does mean the compiler engine is tightly coupled to ReportLab's native behavior. If you want to tweak or expand the visual components, you will need to spend a little quality time with the official ReportLab documentation.

---

## Pipeline visualisation

```
Raw HTML Payload ──► [ FastAPI Gateway ] ──► [ BeautifulSoup4 DOM Tree ]
                                                            │
Streaming PDF Binary ◄── [ ReportLab Engine ] ◄── [ Custom Tag Adapter ]
```
---
## Supported Page Layout Presets
The engine limits canvas geometries to the following optimized industry profiles passed inside the `"preset"` field:

| Preset Name | Target Dimensions | Primary Use Case |
| :--- | :--- | :--- |
| `a4` | 595.27 x 841.89 pt | European standard documentation, invoices |
| `letter` | 612.00 x 792.00 pt | US standard documentation, corporate manifests |
| `label_4x6` | 288.00 x 432.00 pt | High-speed thermal warehouse shipping labels |

---

## Custom HTML Extension Tags

Slim Jim evaluates incoming markup text natively. To support high-fidelity vector components without external script execution, the parser intercepts custom attribute flags on `div` and `img` elements and binds them to native ReportLab vector handlers.

### 1. 1D Logistics Barcodes (Code 128)
To stamp an ultra-sharp, scannable vector shipping barcode, use an empty `div` container marked with a `data-barcode` payload attribute. Optional `width` (which sets the multi-point thickness of the narrowest bar) and `height` (vertical bar size) attributes configure the element canvas bounds:
```html
<div data-barcode="SHIP-NL-98234" width="1.5" height="60"></div>
```

### 2. 2D Vector QR Codes
To inject high-density matrix data, append a `data-qrcode` target string. Optional `width` and `height` properties configure vector container bounds dynamically:
```html
<div data-qrcode="https://slimjim.io/verify/98234" width="120" height="120"></div>
```

### 3. Inline Graphics & Logos
Images must be explicitly embedded as base64-encoded Data URIs. 
* Supported Formats: `.png`, `.jpg`, `.jpeg`
* Unsupported Formats: `.webp`, `.gif` (These are gracefully stripped by the isolation layout parser before canvas serialization).

```html
<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" width="100" height="50" />
```

## 💻 Local Development

### Environment Setup
For production-only builds, install from the core requirements file:
```bash
pip install -r requirements.txt
```

For local engineering, debug configurations, and extended toolings, install the development requirements file instead:
```bash
pip install -r requirements-dev.txt
```

### Running the Microservice Locally
To spin up a local live-reloading development worker instance:
```bash
uvicorn app.main:app --reload --port 8000
```