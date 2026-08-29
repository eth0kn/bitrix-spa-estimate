"""
pdf2png microservice — HTTP wrapper over pdf2image (poppler).
Converts PDF bytes to array of hi-res PNG/JPEG images (one per page).

Endpoint:
  POST /pdf-to-images?dpi=150&format=JPEG&quality=85&max_size_bytes=20000000
  Body: raw PDF bytes (Content-Type: application/pdf)
  Response: { pages: [ { page: N, mime: "image/jpeg", size: bytes, data_url: "data:...base64,..." } ], count, total_bytes }

Query params (all optional):
  dpi              — render resolution (default 150). Higher = better OCR + bigger.
  format           — JPEG (default, smaller) or PNG
  quality          — JPEG quality 1-100 (default 85). Ignored for PNG.
  grayscale        — 'true'/'false' — convert to grayscale (default false; smaller files)
  max_size_bytes   — soft cap on total response payload; if exceeded, service auto-reduces
                     quality (down to 40) and DPI (down to 100) to fit. Default 20000000.

Used by n8n workflow "Product Image Extraction (Quote)" to feed OpenAI Vision
with hi-res per-page images (better OCR for small text like quotation ref suffix).
"""
from flask import Flask, request, jsonify
from pdf2image import convert_from_bytes
from io import BytesIO
import base64
import logging

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok', 'service': 'pdf2png'}


def render(pdf_bytes, dpi, fmt, quality, grayscale):
    images = convert_from_bytes(pdf_bytes, dpi=dpi)
    result = []
    total = 0
    for i, img in enumerate(images):
        if grayscale:
            img = img.convert('L')
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        buf = BytesIO()
        if fmt.upper() == 'JPEG':
            img.save(buf, format='JPEG', quality=quality, optimize=True)
            mime = 'image/jpeg'
        else:
            img.save(buf, format='PNG', optimize=True)
            mime = 'image/png'
        raw = buf.getvalue()
        total += len(raw)
        b64 = base64.b64encode(raw).decode()
        result.append({
            'page': i + 1,
            'mime': mime,
            'size': len(raw),
            'data_url': f'data:{mime};base64,{b64}',
        })
    return result, total


@app.route('/pdf-to-images', methods=['POST'])
def pdf_to_images():
    dpi = int(request.args.get('dpi', 150))
    fmt = request.args.get('format', 'JPEG')
    quality = int(request.args.get('quality', 85))
    grayscale = request.args.get('grayscale', 'false').lower() == 'true'
    max_bytes = int(request.args.get('max_size_bytes', 20_000_000))

    # Accept EITHER raw PDF bytes OR JSON with base64 (more reliable via n8n)
    ctype = (request.headers.get('Content-Type') or '').lower()
    if 'application/json' in ctype:
        body = request.get_json(silent=True) or {}
        b64 = body.get('pdf_base64')
        if not b64:
            return jsonify({'error': 'JSON body must include "pdf_base64" field'}), 400
        try:
            pdf_bytes = base64.b64decode(b64)
        except Exception as e:
            return jsonify({'error': f'invalid base64: {e}'}), 400
        # Allow JSON body to override query params
        dpi = int(body.get('dpi', dpi))
        fmt = body.get('format', fmt)
        quality = int(body.get('quality', quality))
        grayscale = bool(body.get('grayscale', grayscale))
        max_bytes = int(body.get('max_size_bytes', max_bytes))
    else:
        pdf_bytes = request.get_data()
    if not pdf_bytes:
        return jsonify({'error': 'empty body — send PDF bytes as request body, or JSON with pdf_base64'}), 400
    app.logger.info(f'pdf-to-images: received {len(pdf_bytes)} bytes, dpi={dpi}, format={fmt}')

    try:
        pages, total = render(pdf_bytes, dpi, fmt, quality, grayscale)
    except Exception as e:
        app.logger.exception('render failed')
        return jsonify({'error': f'render failed: {e}'}), 500

    # Auto-reduce if too big (best-effort)
    attempts = 0
    while total > max_bytes and attempts < 3:
        attempts += 1
        if fmt.upper() == 'JPEG' and quality > 40:
            quality = max(40, quality - 20)
            app.logger.info(f'auto-reduce: quality → {quality} (was {total} bytes)')
        elif dpi > 100:
            dpi = max(100, dpi - 30)
            app.logger.info(f'auto-reduce: dpi → {dpi} (was {total} bytes)')
        else:
            break
        try:
            pages, total = render(pdf_bytes, dpi, fmt, quality, grayscale)
        except Exception as e:
            return jsonify({'error': f'reduce render failed: {e}'}), 500

    return jsonify({
        'pages': pages,
        'count': len(pages),
        'total_bytes': total,
        'used_dpi': dpi,
        'used_quality': quality if fmt.upper() == 'JPEG' else None,
        'used_format': fmt.upper(),
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
