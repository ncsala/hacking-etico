# Bitácora del lab

Registro cronológico de lo que se hace en la infraestructura, con fecha.
Cada entrada: qué se hizo, por qué, y referencia a los archivos de config
correspondientes en `configs/`.

---

## 2026-11-15 — Sesión inicial: diagnóstico (sin cambios en la VPS)

**Qué se hizo**
- Reconocimiento de la VPS por SSH desde la PC local (3 conexiones).
- Sin ningún cambio aplicado todavía.

**Hallazgos**
- Ubuntu 26.04 LTS en Vultr, 1 CPU / 1.6 GB RAM / 52 GB disco (29%).
- La web (proyecto-rifa) corre en Docker Compose en `~/deploy` y sale a
  internet vía **Cloudflare Tunnel**: el único puerto público es el 22.
- Contenedores activos: web (3000), api (8080), postgres (127.0.0.1:5432),
  cloudflared. Todo "Up" desde hace ~5 semanas. No se tocó nada de esto.
- `rifa` está en grupos `sudo` y `docker`; el sudo pide password.
- SSH: llave funcionando, `PermitRootLogin no`, pero
  `PasswordAuthentication yes` (archivo `00-no-password.conf` mal
  nombrado — el contenido dice `yes`).
- 71 paquetes por actualizar, uptime 78 días.

**Decisiones**
- Pila azul liviana: **Suricata + rsyslog** (no Wazuh/ELK por la RAM).
- Primer ejercicio: portscan contra el puerto 22 + detección en Suricata.
- La web NO se baja: sirve de blanco real con logs reales.

**Pendiente del usuario**
- Correr el comando de `NOPASSWD` (ver chat de esa sesión).

**Próximos pasos**
1. Updates (`apt full-upgrade`) + reboot.
2. fail2ban para SSH.
3. nftables (permitir 22, validar con sesión de prueba antes de enable).
4. Suricata con reglas propias (portscan, UA sqlmap, bruteforce SSH).
5. Ejercicio E01: nmap desde la PC → verificar alertas en `fast.log`.

---

## 2026-11-15 — Sesión 2: hardening base aplicado

**Qué se hizo**

1. **`NOPASSWD` para `rifa`** — `/etc/sudoers.d/99-lab-nopasswd` (440),
   validado con `visudo -cf -` antes de escribir.
   *Off switch:* `sudo rm /etc/sudoers.d/99-lab-nopasswd`
2. **Updates** — `apt-get full-upgrade` (71 → 0; quedan 5 *phased
   updates* de Ubuntu, se liberan solos, no se fuerzan) + reboot
   (volvió en ~45s).
3. **fail2ban** — instalado y activado; jail `sshd` por defecto.
   Resultado inmediato: 22 intentos fallidos, **2 IPs baneadas** en
   minutos. Primeras detecciones reales del lab, gratis.
4. **nftables** — `/etc/nftables.conf` aplicado + servicio habilitado
   (persistente al reboot). Ver copia en `configs/etc/nftables.conf`.

**Decisiones y por qué**

- **No se usó `flush ruleset`**: hubiese borrado las tablas que Docker
  administra vía iptables-nft (DNAT de postgres). Se usa el patrón
  idempotente `table inet filter` + `delete table inet filter` para
  reemplazar solo nuestra tabla.
- **Sin rate-limit en el puerto 22**: la limitación de conexiones la
  hace fail2ban (que decide por comportamiento y con baneos temporales,
  mejor que un límite ciego por minuto).
- **80/443 abiertos ya**: se van a necesitar para los ejercicios web;
  no hay servicio publicado en esos puertos todavía, así que el riesgo
  agregado es cero y evitamos tocar el firewall después.
- **Política forward = drop**: la VPS no enruta tráfico de terceros;
  lo logueado ahí es ruido de internet (131 paquetes descartados en el
  primer minuto).

**Verificación post-cambio** (sesión nueva de SSH tras aplicar)
- SSH OK, sintaxis validada con `nft -c -f` antes de aplicar.
- Contenedores Docker: web/api/postgres/cloudflared Up, postgres healthy.
- fail2ban: sigue activo.

**Pendiente**
- Decidir apagar `PasswordAuthentication` (⚠️ urgencia subió: ahora un
  password adivinado da root directo por el NOPASSWD).
- Suricata + reglas propias.
- Ejercicio E01 (portscan → detección).

---

## 2026-11-16 — Sesión 3: Suricata en producción

**Qué se hizo**

1. **Suricata 8.0.3** instalado (`suricata` + `suricata-update`).
   Hallazgo clave: trae **JA3/JA4 integrado de fábrica** — los
   fingerprints TLS que se estudian en el lab se ven de serie en `eve.json`.
2. Configurado: `HOME_NET: "[64.177.41.17]"`, interfaz `enp1s0` (3
   menciones), reglas propias añadidas a `rule-files`.
3. `suricata-update` descargó **69.456 reglas ET-open** (53.484 enabled).
4. Reglas propias en `/var/lib/suricata/rules/local.rules`:
   - `1000001` Portscan 20puertos/60s (detection_filter)
   - `1000002` UA sqlmap
   - `1000003` SSH 5conn/60s (bruteforce)
5. Validado con `suricata -T` → "successfully loaded" → servicio
   **enable --now** → active. Logs escribiendo: `eve.json`, `fast.log`,
   `stats.log`.
6. Respaldos actualizados: `configs/etc/suricata/suricata.yaml` y
   `configs/var/lib/suricata/rules/local.rules`.

**Error propio documentado (aprendizaje)**

Los primeros `sed` corrieron **sin sudo** y fallaron silenciosamente con
"Permission denied" — el output engañoso hizo pensar que había aplicado.
Lección: en comandos remotos no interactivos, verificar siempre con
`grep` que el cambio quedó escrito antes de seguir. El re-run con sudo
usó guard `grep -q ... ||` para no duplicar la línea de rule-files.

**Primeras detecciones reales (25 segundos de vida)**

- ET CINS Active Threat Intel: IP con mala reputación → puerto 6008
- ET Spamhaus DROP ×2: IPs blocklisteadas tanteando telnet (23) y puertos
  random
- O sea: el ruido de fondo de internet es constante y la ET lo caza solo.
  Esto ES la línea base del lab: la caja "en calma" ya tiene alertas.

## 2026-11-16 — Cierre de sesión: plan a dos VPS definido

**Estado de la azul al cierre: COMPLETA Y DURMIENDO VIGILADA**

| Componente | Estado |
|---|---|
| Updates | ✓ al día + reboot |
| SSH | key-only (1 llave, PC local), root login off, fail2ban banneando |
| Sudo | NOPASSWD para rifa (off switch documentado) |
| nftables | ✓ aplicado, persistente, contadores activos |
| Suricata | ✓ activo, 69k reglas ET + 3 propias, JA3/JA4 integrado |
| Web (blanco) | ✓ intocada, corriendo por Cloudflare Tunnel |
| Docs | ✓ bitácora + configs respaldadas |

**Plan a futuro** (queda anotado en `AGENTS.md`): segunda VPS **roja**
en proveedor distinto (ASN diferente) como estación de ataque — pendiente
de que el usuario la cree. Regla de oro escrita a su pedido: la roja
lanza, la azul recibe; nada apunta a terceros.

**Roadmap de campaña** definido: E01 escalera de sigilo → E02 recon
pasivo → E03 campaña web (con backup de DB previo) → E04 persistencia
→ E05 informe.

**Próximo paso cuando se retome:** crear la roja, o instalar nmap local
(`sudo apt install -y nmap`) y correr E01 desde la PC.

---

## 2026-11-16 — Playbook de campaña escrito (`lab/campania.md`)

A pedido del usuario: plan "ultra detallado / ultra realista". El
playbook define por ejercicio (E01–E05): comandos exactos, reglas de
Suricata que deberían disparar, qué mirar en `eve.json`/`fast.log`,
mapeo MITRE ATT&CK (T1046, T1595, T1190, T1053, T1098), reglas de
operación (rate limits para no DoS-earnos a nosotros mismos, backup
previo en E03, stop conditions) y el backlog de upgrades del azul
(honeytokens, pcap, snapshot de integridad, regla de timing, auditd).

Marco reafirmado en el encabezado del playbook: solo infraestructura
propia, la roja lanza y la azul recibe, nada a terceros.

---

## 2026-11-16 — Sesión 5: E01 en marcha + hallazgo de doble firewall

**El hallazgo del día (digno de oro)**

El primer nmap declaró la azul "down". Investigación con ping, connects
de python y los logs del firewall reveló: **ufw estaba activo en
paralelo al nftables** (preinstalado en la imagen), permitiendo solo el
22 y descartando en silencio el 80/443. Los firewalls se evalúan ambos:
nuestro `accept` de 80/443 nunca había tenido efecto. Lección
documentada: dos firewalls en paralelo = config no auditable.

**Cambios aplicados (con prueba de SSH fresca tras cada paso)**

1. `ufw disable` — nftables queda como única fuente de verdad.
2. nftables: regla `tcp dport {80,443} accept` desactivada (comentada
   con referencia al E03). La postura "host muerto en 80/443" se
   conserva — ahora por diseño documentado y no por accidente.
   Copia actualizada en `configs/etc/nftables.conf`.

**E01 — Peldaño 1 (gritón) ejecutado desde la PC local**

- `nmap -Pn -T4 -p 1-300` → 22 open, 299 filtered, 8.5s.
- Azul: `LAB Portscan 20puertos/60s` + `LAB SSH 5conn/60s` dispararon
  inmediatamente (599 líneas, ventana exacta del scan).
- Tabla de detección en `lab/ejercicios/E01-escalera-sigilo.md`
  (peldaños 2–4 pendientes).
- Notas de aprendizaje: connect scan (sin root) vs SYN scan; falso
  positivo de bruteforce por el scan del 22 (tuning del azul).

---

## 2026-11-16 — E01 peldaño 2: el lento TAMBIÉN cayó

- `nmap -Pn -T1 --max-rate 5 -p 6 puertos`, 196s de ejecución.
- Detectado: 19 alertas LAB Portscan + 5 `ET SCAN ... PostgreSQL`.
- Causa: **retransmisiones del connect scan sobre puertos filtrados**
  cruzan el umbral `count 20` (cuenta paquetes, no puertos únicos).
- Iteración de regla intentada: `portcount` en detection_filter/filter/
  threshold → la v8.0.3 no lo soporta (3 errores de parse documentados).
  Revertido a `count 20` rev:2. Suricata re-validado y activo.
- Backlog del azul actualizado: detección por cadencia/puertos únicos.
- Copia de `local.rules` actualizada en el repo.

---

## 2026-11-16 — Cambio de metodología: fases ROJA/AZUL separadas

El usuario prioriza el lado rojo: la campaña corre en dos fases.
FASE ROJA a ciegas (sin ver telemetría del azul; el asistente apoya
solo el rojo) → FASE AZUL a libro abierto (análisis de logs, reglas
nuevas, informe). Antes de cada fase roja, el azul se actualiza en
silencio (cartas tapadas para el defensor). Peldaños 3-4 del E01 se
pasan a la fase roja (necesitan root: VPS roja o sudo local).
Detalles en `AGENTS.md` → "Metodología".

---

## 2026-11-16 — E02: recon pasivo de hayrifa.uy (fase roja, iniciada)

Dossier completo en `lab/ejercicios/E02-recon-pasivo.md`. Resumen:
- Origen NO expuesto: DNS 100% proxied por CF, mail en edge, tunnel sin
  puertos entrantes ni cert escaneable → mejor defensa del lab hasta
  ahora, y es la de producción real.
- Guess de subdominios pegó: `api.hayrifa.uy` existe (proxied).
- CAA vacío (higiene pendiente), RDAP de .uy inexistente (lección de
  tooling: RDAP ARIN para la IP funcionó; dominio cae a whois/nic.uy).
- **El target responde HTTP 530 en apex y api** (origin unreachable):
  el blanco está caído para el atacante. Pendiente que el dueño verifique
  el estado del tunnel (acción fuera de la fase roja).

---

## 2026-11-16 — E02 extendido: superficie de la app (web viva de nuevo)

- Stack: **Next.js** (header expuesto). Redirect raíz → rifa activa con
  **UUID v7** cuyo timestamp embebido (2026-08-31, día del deploy) es
  decodificable → IDs parcialmente predecibles: hallazgo real para la
  fase azul (enumeración/IDOR a revisar).
- sitemap.xml lista rutas (`/mis-numeros` responde 200 sin sesión — a
  verificar si el guard es client-side en E03).
- api.hayrifa.uy: endpoints no obvios (404 en paths comunes) → se
  descubrirán con el JS del frontend (siguiente paso de recon).
- Todo en `lab/ejercicios/E02-recon-pasivo.md`.

---

## 2026-11-16 — E02: recon vía bundles JS → Server Actions

- Primer script del arsenal: `lab/scripts/recon_js_endpoints.py`
  (descarga HTML → extrae chunks → busca endpoints/NEXT_PUBLIC/terceros;
  output cacheado en `lab/scripts/output/`, .gitignore creado).
- 14 bundles analizados: **cero endpoints de API en el cliente** — la
  app usa Next.js **Server Actions** (`createServerReference`), las
  llamadas van por POST con action-IDs encriptados, no por URLs del API.
- Recon estático = dead end (hallazgo defensivo-arquitectural). La
  superficie real de Server Actions (interceptar/reproducir action-IDs
  con parámetros alterados) queda para el E03.
- Bonus: PostHog con endpoint `/ingest` identificado.

---

## 2026-11-16 — Cierre de sesión: plan del equipo rojo completo

- Nuevo documento: `lab/plan-equipo-rojo.md` — el plan operativo
  profesional del lado rojo: ROE con marco legal explícito (pedido del
  usuario: solo infra propia, cero terceros, cero infra robada),
  infraestructura (VPS roja en proveedor distinto + estructura de
  engagement), toolset completo, metodología de campaña (5 fases),
  tradecraft del operador e higiene (no evasión), estado y próximos pasos.
- E02 dossier: numeración corregida (era desprolija).
- `.gitignore` para output de scripts.
- Sesión cerrada. Mañana: crear VPS roja → onboarding + toolset →
  E01 peldaños 3–4 → preparación E03 (mitmproxy + Server Actions).

---




## 2026-11-16 — ⚠️ INCIDENTE: el lab tiró la web de producción (resuelto)

**Qué pasó**

El 530 que detectó el recon E02 no era del proveedor ni del lab "de
afuera": fue **causado por nuestro firewall**. El tunnel de cloudflared
(contenedor) hace conexiones salientes por QUIC hacia el edge de CF; ese
tráfico atraviesa la cadena `forward` de nftables, que tenía
`policy drop` sin reglas para los bridges de Docker → tunnel muerto →
Cloudflare sin origen → 530 en todo el sitio. La web (Next.js) siempre
estuvo sana adentro del contenedor.

**Por qué no lo vimos venir**

Todas las pruebas post-firewall fueron tráfico de HOST (SSH, apt,
suricata-update, docker exec) — nunca tráfico de CONTENEDOR hacia
internet. Lección brutal y real: un cambio de infra "que no toca la web"
la puede tumbar igual por una cadena intermedia (forward) que nadie
miró. Es exactamente el tipo de incidente que las post-mortems reales
documentan.

**Resolución (3 minutos)**

1. Diagnóstico: logs de cloudflared (`failed to dial to edge with quic`)
   → traffic de contenedor bloqueado en forward.
2. Fix live: `nft insert rule ... iifname "br-*" accept` (+ docker0 y
   established) ANTES del drop, por índice.
3. `Registered tunnel connection` a las 01:48:50 UTC → sitio vivo
   (307 con CSP verificado desde afuera).
4. Fix persistente: `/etc/nftables.conf` regenerado con forward
   corregido (comentario del incidente incluido), validado, aplicado,
   copia al repo actualizada.

**Mejoras derivadas**
- Regla del lab: tras CUALQUIER cambio de firewall, probar tráfico de
  host Y de contenedor (curl al sitio desde afuera incluido).
- El incidente queda como evidencia de que el lab sí rompe cosas reales:
  más valor para la fase de "cleanup" del playbook.

---

## 2026-11-16 — Línea de base de fase roja: revertido al estado original

A pedido del usuario ("el rojo ataca lo que yo tenía, no el castillo"):

- ❌ nftables: deshabilitado y tabla `inet filter` eliminada (configs
  preservadas en el repo para re-aplicar en fase azul)
- ✅ ufw: re-activado (era el estado original: deny incoming, solo 22)
- ❌ fail2ban: detenido (con SSH key-only no hay vector de bruteforce)
- ✅ Suricata: sigue grabando — la cámara de la fase azul (IDS pasivo,
  no bloquea nada; sin ella no habría qué analizar después)
- ✅ SSH key-only + NOPASSWD: quedan (operativos, no cambian la
  superficie de ataque)
- Verificado post-cambio: SSH OK, web 307 OK, tunnel registrado

Estado del host ahora = tal como lo tenía el usuario antes del lab.
La fase roja corre contra ESTA línea de base. El hardening completo
(nftables + fail2ban + reglas nuevas) se arma en la fase AZUL, después
de la campaña, como entregable defensivo.

---









## 2026-11-16 — Sesión 4: password de SSH apagado

**Qué se hizo**

- `PasswordAuthentication` → **no** en
  `/etc/ssh/sshd_config.d/00-no-password.conf` (el archivo por fin
  coincide con su nombre 😅). Respaldado como
  `configs/etc/ssh/sshd_config.d/00-key-only.conf`.
- Detalle técnico: en sshd gana el **primer** valor leído (los archivos
  de `sshd_config.d/` se leen en orden lexicográfico), por eso se corrigió
  el existente en vez de crear uno nuevo que no habría ganado.
- Validación: `sshd -t` (sintaxis) + `sshd -T` (config efectiva:
  `passwordauthentication no`) + restart + **conexión nueva de prueba**
  (key-only OK, sudo OK).
- Bonus: `linuxuser` (UID 1000) tiene password **bloqueado** — no es puerta.

**Por qué (urgencia que motivó el cambio)**

Con `NOPASSWD` activo, un password de SSH adivinado daba **root directo**.
La evidencia de los logs mostró que TODOS los logins exitosos eran
`publickey` desde la IP de casa — el password era una puerta que nadie
legítimo usaba y solo servía para brute force. fail2ban quedó como
segunda capa (el SSH sigue expuesto; lo que se eliminó es la
posibilidad de entrar adivinando).

**Estado de la superficie externa (a esta altura)**

Puerto 22 abierto, key-only, fail2ban banneando. Única puerta real:
la llave privada en la PC local. Rescate: consola web Vultr.

---


