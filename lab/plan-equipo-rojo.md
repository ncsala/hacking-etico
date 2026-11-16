# Plan del equipo rojo — operación profesional del lab

> El documento operativo del lado ofensivo del lab. Estilo red team real,
> escalado a un solo operador (vos).
>
> **MARCO LEGAL (no negociable, pedido explícito del dueño):**
> 1. Todos los objetivos son infraestructura del usuario: la VPS azul
>    (64.177.41.17) y la web propia (hayrifa.uy / api.hayrifa.uy).
> 2. CERO ataques a sitios o sistemas de terceros. Nada "de prueba" a
>    dominios de otros "porque es chica la prueba". Sin excepciones.
> 3. CERO infraestructura robada o comprometida de terceros (bots, IPs
>    prestadas, etc.). Todo el equipo rojo es infraestructura propia.
> 4. Sin dominio/hostname para la roja: todo por IP, lab cerrado.
> 5. Cada técnica se registra con timestamp en la bitácora propia del
>    engagement — un red team profesional documenta TODO lo que hace
>    (para el reporte, no para esconderse).
>
> Si en cualquier sesión algo empieza a apuntar fuera del marco, se corta.

## 1. Misión de la campaña

Simular un atacante externo serio contra la superficie real del dueño y
producir dos entregables:
- **Rojo:** la ruta de ataque completa (qué se logró, cómo, con qué).
- **Insumo azul:** el rastro real que quedó (que la fase azul analizará).
- **Ejercicio meta:** auto-percepción vs realidad — antes de abrir los
  logs, el rojo escribe qué cree que dejó; después se compara. El gap es
  la mejor lección del lab.

## 2. Infraestructura del equipo rojo

### 2.1 Workstation: VPS roja (pendiente de crear)
- Proveedor DISTINTO a Vultr (ASN diferente — parte del diseño). Opciones
  evaluadas: Hetzner (~€4/mes, recomendada), DigitalOcean, OVH, Scaleway.
- Specs: 1 vCPU / 1–2 GB RAM / Debian 12 o Ubuntu 24.04. Llave SSH del lab
  cargada en el panel del proveedor (sin password, sin dominio, sin DNS).
- **Hardening mínimo de la roja** (importante: NO es "trampa" — es
  higiene hacia TERCEROS, no hacia el blanco; un red team real protege
  su propia infra de la internet, igual que cualquiera):
  - updates automáticos, SSH key-only, firewall que solo deje SSH.
  - Sin fail2ban/Suricata/etc: no hace falta (no expone servicios).
- Onboarding documentado como `lab/roja-arquitectura.md` + bitácora.

### 2.2 Estructura de archivos en la roja (la "carpeta del engagement")

```
~/engagement-hayrifa/
├── ROE.md              ← reglas de engagement (copia de este plan)
├── notes/
│   ├── 00-recon-pasivo.md
│   ├── 01-recon-activo.md
│   └── ...             ← una nota por sesión, con timestamps
├── recon/
│   ├── dns/ cert/ js/  ← outputs crudos de cada técnica
├── loot/
│   └── (hallazgos: endpoints, datos expuestos, rutas válidas)
└── report/
    └── E05-informe.md  ← el informe final
```

### 2.3 Toolset a instalar en la roja

| Categoría | Herramienta | Uso en la campaña |
|---|---|---|
| Recon activo | `nmap` | E01 escalera de sigilo (con root: `-sS`, `-f`) |
| Recon web | `ffuf` | fuzzing de rutas (rate-limited) |
| SQLi | `sqlmap` | SOLO con `--delay` y contra rutas de prueba |
| Brute force | `hydra` | login de la app propia (rate-limited) |
| Intercepción | `mitmproxy` + scripts propios | capturar Server Actions del navegador |
| Utilidades | `jq`, `curl`, `git`, `python3`, `tmux` | glue de todo |
| Scripts del lab | carpeta `lab/scripts/` sincronizada | recon_js_endpoints.py y próximos |

Los scripts propios viven AMBOS lados: en el repo (fuente de verdad) y en
la roja (en uso). Sincronizar con git clone/pull en la roja.

## 3. Metodología de campaña (como la de un red team real)

### Fase 0 — Pre-engagement (ya documentado)
ROE (este archivo), ventana horaria, scope fijo:
`64.177.41.17, hayrifa.uy, api.hayrifa.uy. NADA MÁS.`
Checkpoint: si aparece una IP/dominio nuevo (terceros, CDNs, mails),
se estudia pasivamente pero no se toca activamente.

### Fase 1 — Recon pasivo (E02 — HECHO, ver dossier)
OSINT: TLS/CT logs, DNS, RDAP, bundles JS, sitemap. Ya produjo:
arquitectura Server Actions, UUID v7 predecible, PostHog /ingest,
Next.js expuesto, api.hayrifa.uy identificado.

### Fase 2 — Recon activo con disciplina de ruido (E01)
Escalera de sigilo: `-T4` → `-T1 --max-rate 5` → `-f` → `--data-length`.
Con root en la roja: SYN scan real (`-sS`), fragmentación real.
**Regla de oro del ruido:** toda técnica arranca en su versión más
silenciosa; solo escala si no alcanza el objetivo. Cada peldaño se
anota con timestamp (la bitácora del rojo).

### Fase 3 — Campaña web (E03) — el plato fuerte
Contra hayrifa.uy/api (vía Cloudflare, como cualquier visitante):

a) **Mapeo del API real**: navegar la app con proxy de intercepción
   (mitmproxy) y capturar los POST de Server Actions (action-ID +
   payload). Documentar cada acción: qué hace, qué parámetros.
b) **Server Actions tampering** (técnica conocida contra Next.js):
   reproducir acciones con parámetros alterados (IDs ajenos, montos,
   estados). Objetivo: detectar si el server valida o confía en el cliente.
c) **Brute force de login** (si existe login): hydra/ffuf rate-limited,
   lista pequeña de prueba, contra la propia app.
d) **Enumeración de IDs v7**: dado el timestamp decodificado, probar el
   rango temporal alrededor de fechas conocidas (deploy 2026-08-31) para
   medir si otros IDs son accesibles sin auth.
e) **Fuzzing de rutas** con ffuf contra api.hayrifa.uy (rate limit 30).

Anti-DoS del lab: la azul tiene 1 CPU. Toda herramienta con `-rate`/
`--delay`/`-w` ajustado. Si algo tumba el blanco: STOP, documentar.

### Fase 4 — Persistencia simulada (E04)
Solo con acceso logrado de verdad (si lo hay): cuentas nuevas, cron de
latido, llave SSH extra — cada una con su reversión escrita en el mismo
paso. Si no se logró acceso: se simula discutido en el informe.

### Fase 5 — Informe (E05) y entrega a la fase azul
- Tabla técnica → ATT&CK → detección esperada/real → gap.
- Timeline de la campaña.
- Backlog de fixes para la app (los hallazgos reales del dueño).

## 4. Tradecraft del operador (higiene profesional, no evasión)

1. **Credenciales separadas**: llave/proveedores del lab ≠ llaves
   personales. 2FA en los paneles de los proveedores.
2. **Scope discipline**: cada comando con target explícito (IP/dominio
   escrito en el comando, no en un alias). Evitar `-iL` con listas que
   puedan arrastrar IPs de terceros.
3. **Registro propio**: el rojo documenta lo que HACE (no lo que deja).
   Es lo que permite el ejercicio de auto-percepción vs realidad.
4. **Horarios de la campaña** anotados: la fase azul usará las ventanas
   para correlacionar telemetría.
5. **Nada de munición real**: sin malware, sin exploit de terceros, sin
   datos falsos de terceros. Las técnicas del playbook alcanzan.

## 6. Arquitectura de sigilo del equipo rojo (indetectable ≠ intrazable)

Definición operativa:
- **INDETECTABLE** (objetivo jugable del lab): el azul no encuentra
  señales de actividad anómala. Se juega con disciplina de comportamiento.
- **INTRAZABLE** (fuera del marco): ocultar identidad/atribución con
  cadenas de infra anónima, pagos ocultos, etc. En el lab no aporta nada
  jugable y fuera de él es intrusión. El rojo profesional se optimiza
  por "no alertar", no por "no existir".

**Principio central:** el mejor sigilo es parecer tráfico normal. La
arquitectura se ordena en dos canales:

```
CANAL A — Red (desde la VPS roja)          CANAL B — Aplicación (el sigiloso)
┌─────────────────────────────┐            ┌─────────────────────────────┐
│ nmap / ffuf / hydra con     │            │ Navegador real + mitmproxy  │
│ disciplina de ruido         │            │ interceptando Server Actions│
│                             │            │ del propio flujo de uso     │
│ Detectable por diseño       │            │ Indistinguible de un usuario│
│ → sirve para MEDIR (E01)    │            │ real, porque ES el usuario  │
│                             │            │ → canal de ataque E03       │
└─────────────────────────────┘            └─────────────────────────────┘
```

### Disciplina de fingerprint (ambos canales)
1. **UA fijo y real**: un User-Agent de navegador verdadero, siempre el
   mismo. Nada de rotar UAs "por si acaso" — la rotación es firma.
2. **curl-impersonate**: cualquier curl que toque el blanco sale con el
   JA3/JA4 de un Chrome real (el TLS fingerprint deja de delatar).
3. **Rate ceiling**: ≤ 1 req/s en probing web; `-t 2`/`-rate` en ffuf;
   `-t 2 -w 5` en hydra.
4. **Horario de tráfico real**: operar cuando el sitio tiene tráfico
   normal; nunca ráfagas a las 4 AM (timing es firma).
5. **Orden randomizado**: `--randomize-hosts/ports` en nmap,
   `-shuffle` en ffuf.
6. **Cero headers de herramientas**: `sqlmap --random-agent`,
   `-H` custom en ffuf. Antes de correr cualquier tool, revisar qué
   firma dejaría (el rojo anota qué patrón está evitando — insumo
   directo de reglas para la fase azul).
7. **Ventanas cortas**: sesiones de probing de 10-15 min, no maratones.

### Qué NO se hace (marco, reafirmado)
- Sin cadenas de proxies anónimos, sin pagos ocultos, sin ocultar al
  operador. El sigilo del lab es de comportamiento, y se mide en la
  fase azul: "¿qué dejó el rojo que el azul pudiera ver?"

## 7. Escenarios y comandos (con la roja provisionada)

### 7.1 Instalación del toolset (Debian 12 / Ubuntu en la roja)

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y nmap hydra sqlmap jq git tmux curl python3-pip mitmproxy

# ffuf (binario release)
curl -sL https://github.com/ffuf/ffuf/releases/latest/download/ffuf_2.1.0_linux_amd64.tar.gz | tar xz -C /tmp && sudo mv /tmp/ffuf /usr/local/bin/

# curl-impersonate (Chrome real en línea de comando)
curl -sL https://github.com/lwthiker/curl-impersonate/releases/download/v0.6.1/curl-impersonate-v0.6.1.x86_64-linux-gnu.tar.gz | tar xz -C /usr/local/bin curl_chrome116 curl_chrome116-series

# wordlists mínimas (solo Discovery)
git clone --depth 1 https://github.com/danielmiessler/SecLists /opt/seclists

# estructura del engagement
mkdir -p ~/engagement-hayrifa/{notes,recon/{dns,cert,js},loot,report}
```

### 7.2 Escenario E01 — peldaños 3 y 4 (root real en la roja)

```bash
# Peldaño 3: SYN scan fragmentado, lento (antes era imposible sin root)
sudo nmap -sS -f -T1 --max-rate 5 -p 22,80,443,3000,8081,5432 64.177.41.17

# Peldaño 4: payload random + puertos randomizados + timing T2
sudo nmap -sS -f --data-length 24 --randomize-ports -T2 --max-rate 5 -p 1-500 64.177.41.17
```
El rojo anota después de cada peldaño: "qué creo que el azul vio"
(sin mirar los logs — eso es fase azul).

### 7.3 Escenario web disciplinado (Canal A con fingerprint limpio)

```bash
# Sondeo con JA3 de Chrome real (curl-impersonate)
curl_chrome116 -s -o /dev/null -w "%{http_code} %{time_total}\n" https://hayrifa.uy/raffle/<ID>

# Fuzzing de rutas: rate limitado, UA real fijo, shuffle
ffuf -u https://hayrifa.uy/FUZZ -w /opt/seclists/Discovery/Web-Content/common.txt \
     -rate 15 -t 2 -shuffle -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) Chrome/126.0" \
     -fc 404 -of json -o ~/engagement-hayrifa/recon/ffuf-raices.json
```

### 7.4 Escenario Server Actions (Canal B — el sigiloso, E03)

El addon `lab/scripts/capture_server_actions.py` (mitmproxy) registra
cada Server Action que el navegador dispara contra el blanco — con
scope discipline dentro del propio script (solo host del engagement):

```bash
# Captura (navegando la app como usuario real: comprar, consultar)
mitmdump -s capture_server_actions.py -w ~/engagement-hayrifa/recon/flows.mitm

# Reproducción con parámetros alterados (el test de validación del server):
curl https://hayrifa.uy/raffle/<ID> -X POST \
  -H "Next-Action: <action-id capturado>" \
  -H "Cookie: <sesión capturada>" \
  -H "Content-Type: text/plain;charset=UTF-8" \
  --data '<payload alterado>'
```
Técnicas derivadas: cambiar IDs de rifa/ticket por otros, alterar montos
o estados, replay sin sesión — todo contra la app propia, medido con
`--delay` si se repite.

### 7.5 El registro del rojo (cada sesión)

```bash
# Al terminar cada sesión de la fase roja, SIN mirar logs del azul:
echo "$(date -u +%FT%TZ) | canal A | nmap rung3 | creo que dejó: SYNs lentos" \
  >> ~/engagement-hayrifa/notes/01-recon-activo.md
```
Ese archivo de auto-percepción es el insumo del ejercicio meta: en la
fase azul se compara contra `eve.json` y se mide el gap.

## 8. Estado y próximos pasos

- [x] ROE + plan del equipo rojo (este documento)
- [x] Arquitectura de sigilo (sección 6: indetectable ≠ intrazable,
  dos canales, disciplina de fingerprint) + escenarios con comandos (sección 7)
- [x] Fase 1 recon pasivo (E02 dossier completo)
- [x] Script 1 del arsenal (recon_js_endpoints.py)
- [x] Script 2 del arsenal (capture_server_actions.py — mitmproxy addon
  para interceptar Server Actions, con scope discipline interno)
- [ ] VPS roja: crear (Hetzner/DO), onboarding, toolset (sección 7.1)
- [ ] Fase 2: E01 peldaños 3–4 (con root, sección 7.2)
- [ ] Fase 3: E03 campaña web (mitmproxy + Server Actions, sección 7.4)
- [ ] Fase 4: E04 persistencia (según acceso logrado)
- [ ] Fase 5: E05 informe + hand-off a la fase azul
