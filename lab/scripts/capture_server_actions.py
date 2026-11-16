"""
capture_server_actions.py — Addon de mitmproxy para el lab purple team.

Qué hace: registra cada Server Action (POST con header `Next-Action`)
que el navegador dispara contra el blanco del engagement, con su
payload, headers y cookies. Ese registro alimenta el E03:
  1) mapeo de las acciones reales de la app (el "API oculto" de Next.js)
  2) reproducción con parámetros alterados (test de validación del server)

MARCO: solo infraestructura propia (ver lab/plan-equipo-rojo.md). El
script aplica scope discipline internamente: si el host no es el blanco,
no registra nada. Configurar TARGET_HOST antes de usar.

Uso:
    mitmdump -s capture_server_actions.py -w sesion.flows
    (navegar la app con el proxy apuntado a mitmproxy y operar como
     usuario real: comprar ticket, consultar resultado, login...)

Salida: server_actions.jsonl (una línea por acción capturada).
"""

import json
import time
from pathlib import Path

from mitmproxy import http

# Scope del engagement: el ÚNICO host que este addon registra.
TARGET_HOST = "hayrifa.uy"

OUT = Path(__file__).parent / "output" / "server_actions.jsonl"

# Headers que interesan para reproducir una acción después
INTERESTING_HEADERS = [
    "next-action",
    "content-type",
    "cookie",
    "user-agent",
    "referer",
    "origin",
]


def request(flow: http.HTTPFlow) -> None:
    host = flow.request.pretty_host
    if host != TARGET_HOST:
        return  # scope discipline: nada fuera del blanco

    if flow.request.method != "POST":
        return

    headers = {h: flow.request.headers.get(h, "") for h in INTERESTING_HEADERS}
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": host,
        "path": flow.request.path,
        "es_server_action": bool(headers["next-action"]),
        "headers": headers,
        "body": flow.request.get_text(limit=8000),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    if rec["es_server_action"]:
        print(f"[SA] {rec['path']}  action={rec['headers']['next-action'][:20]}...")
