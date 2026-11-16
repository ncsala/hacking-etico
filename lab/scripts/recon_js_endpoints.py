#!/usr/bin/env python3
"""
recon_js_endpoints.py — Recon de endpoints de API desde el JS del frontend.

Técnica (E02, fase roja): las apps SPA/Next.js inlinean en sus bundles JS
las rutas del API que llaman (y a veces variables NEXT_PUBLIC_*). Sin
necesidad de docs del API: el propio frontend le dice al atacante dónde
está todo.

Uso:
    python3 recon_js_endpoints.py https://hayrifa.uy

Qué hace:
1. Descarga el HTML de la página y extrae las URLs de los <script src>.
2. Descarga cada bundle JS (caché local en out_dir).
3. Extrae: URLs absolutas del API, rutas relativas tipo /api/...,
   variables NEXT_PUBLIC_* y sus valores, y hostnames adicionales.

Uso interno del lab: SOLO contra infraestructura propia (ver AGENTS.md).
"""

import re
import sys
import pathlib
import urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
OUT_DIR = pathlib.Path(__file__).parent / "output" / "js-bundles"

# Qué buscar en los bundles (regex ordenadas de más específica a más general)
PATTERNS = {
    "NEXT_PUBLIC vars": r"NEXT_PUBLIC_[A-Z0-9_]+[\"':\s=]+[\"']([^\"']{3,120})[\"']",
    "URLs absolutas del API": r"https?://api\.[a-zA-Z0-9.-]+[a-zA-Z0-9/_\-.]*",
    "rutas /api/...": r"[\"'](/api/[a-zA-Z0-9/_\-\.]+)[\"']",
    "rutas /v1|v2/...": r"[\"'](/v[12]/[a-zA-Z0-9/_\-\.]+)[\"']",
    "fetch/axios a rutas": r"(?:fetch|axios[.\w]*\()\s*[\"'](/[a-zA-Z0-9/_\-\.]{2,60})[\"']",
    "hostnames de terceros": r"https?://([a-zA-Z0-9.-]+\.(?:supabase\.co|firebaseio\.com|supabase\.in|pages\.dev|workers\.dev))",
}


def fetch(url: str, binary: bool = False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", errors="replace")


def extraer_scripts(html: str, base: str) -> list[str]:
    urls = re.findall(r'src=[\'"](/_next/static/[^\'"]+\.js)[\'"]', html)
    urls += re.findall(r'src=[\'"](https?://[^\'"]+\.js)[\'"]', html)
    # Next.js moderno: los chunks van inline en el runtime JSON/JS del HTML,
    # no como atributos src. Buscar cualquier referencia a chunks en el HTML.
    urls += re.findall(r'/_next/static/[^"\\\s<>]{5,120}\.js', html)
    # normalizar relativas
    from urllib.parse import urljoin
    return sorted({urljoin(base, u) for u in urls})


def main(base_url: str):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[*] Target: {base_url}")
    html = fetch(base_url)
    scripts = extraer_scripts(html, base_url)
    print(f"[*] Bundles JS encontrados: {len(scripts)}")

    hallazgos: dict[str, set] = {k: set() for k in PATTERNS}
    for i, js_url in enumerate(scripts):
        try:
            js = fetch(js_url)
        except Exception as e:
            print(f"    [!] error descargando {js_url}: {e}")
            continue
        nombre = f"bundle-{i:02d}.js"
        (OUT_DIR / nombre).write_text(js, encoding="utf-8")
        print(f"    [+] {nombre} <- {js_url.split('//')[1][:60]}... ({len(js)//1024} KB)")
        for etiqueta, patron in PATTERNS.items():
            for m in re.findall(patron, js):
                hallazgos[etiqueta].add(m if isinstance(m, str) else m[0])

    print("\n" + "=" * 60)
    for etiqueta, items in hallazgos.items():
        if items:
            print(f"\n### {etiqueta} ({len(items)})")
            for item in sorted(items)[:40]:
                print(f"  {item}")
    print(f"\n[*] Bundles cacheados en: {OUT_DIR}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1].rstrip("/") + "/")
