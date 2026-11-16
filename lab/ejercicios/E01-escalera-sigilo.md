# E01 — Escalera de sigilo (tabla de detección)

> Ejercicio en curso. Cada peldaño: la misma técnica con ruido decreciente.
> Se completa la tabla a mano con lo que el azul vio en cada paso.
> Tablero base al inicio (2026-11-16 01:21): fast.log 113 líneas de ruido
> de internet, cero alertas LAB.

## Pre-hallazgo del ejercicio (lección gratis)

El primer intento de discovery de nmap declaró la azul "down": las
sondas van al 80/443 y esos puertos descartan en silencio (postura
defensiva: el host parece muerto). Causa raíz descubierta: **ufw
preinstalado interceptando en paralelo al nftables** (ver bitácora
2026-11-16). Resuelto: ufw fuera, nftables única fuente, 80/443 en drop.

Lección doble:
- Atacante: cuando el discovery da "down" pero hay un servicio vivo
  conocido, se sigue con `-Pn`.
- Defensor: la postura "no response" en puertos sin servicio le cuesta
  info al atacante; y tener dos firewalls en paralelo es un riesgo de
  auditoría (solo uno se lee en los archivos de config).

## Tabla de detección

| # | Peldaño | Comando | Resultado scan | ¿Detectado? | Dónde | Gap del azul |
|---|---|---|---|---|---|---|
| 1 | Gritón (connect scan sin root) | `nmap -Pn -T4 -p 1-300 64.177.41.17` | 22 open, 299 filtered (no-response), 8.5s | **SÍ, inmediato** | `LAB Portscan 20puertos/60s` (sid 1000001) + `LAB SSH 5conn/60s` (sid 1000003), 599 líneas, ventana 01:25:38–45 exacta | Ninguno: el umbral de 20 puertos/60s lo caza de frente |
| 2 | Lento | `nmap -Pn -T1 --max-rate 5 -p 22,80,443,3000,8081,5432` | 22 open, 5 filtered, **196s** (vs 8.5s del gritón) | **SÍ, inesperado** | `LAB Portscan` ×19 + `ET SCAN ... PostgreSQL 5432` ×5 (regla ET preexistente) | El umbral count=20 cuenta SYNs, no puertos: las retransmisiones del connect scan sobre puertos filtrados cruzan el umbral igual |

**Notas del peldaño 2 (las mejores lecciones del lab hasta ahora):**

1. **Las retransmisiones delatan.** El scan lento es "silencioso" solo
   contra puertos abiertos. Contra puertos filtrados (sin respuesta),
   nmap reenvía el SYN varias veces → mismo puerto fuente/destino una y
   otra vez en las alertas (verificado en eve.json: `:45648 -> :8081` en
   ráfaga). El atacante low & slow contra un host que hace drop queda
   inflando su huella sin querer.
2. **Error de diseño de regla (mío) detectado por el ejercicio.** Quería
   "20 puertos distintos", escribí "20 paquetes". Iteración de regla
   intentada: `portcount 20` → falla de parse en detection_filter, en
   filter y en threshold (v8.0.3 no lo soporta en ninguna). Revertido a
   `count 20` (rev:2). Backlog: detección de cadencia/puertos únicos por
   otra vía (análisis de eve.json, xbits, o reglas de timing).
3. **ET-open ya sabía**: la regla `ET SCAN Suspicious inbound to
   PostgreSQL port 5432` cazó el sondeo al 5432 sin que yo escribiera
   nada. Las reglas de la comunidad cubren patrones clásicos.
4. **Lección de scripting**: `suricata -T | tail` se traga el exit code
   del pipe → el restart corrió con config rota. Fix: redirigir a archivo
   y chequear `$?` explícito. Suricata se repara en el mismo ciclo.
| 3 | Fragmentado | `nmap -Pn -f -T1 -p 22,80,443` | (pendiente) | | | |
| 4 | Disfrazado | `nmap -Pn -T1 --data-length 24 --max-rate 5 -p 22,80,443` | (pendiente) | | | |

Notas peldaño 1:
- Corrió sin root → nmap usó **TCP connect scan** (handshake completo),
  aún más ruidoso que un SYN scan. Un SYN scan (`-sS`, con root) envía
  menos paquetes: a probar en la VPS roja.
- La regla de umbral (20 puertos/60s) es "burra pero efectiva": caza el
  gritón al instante. El juego de verdad empieza en el peldaño 2: el
  mismo atacante bajo el umbral.
- El `LAB SSH 5conn/60s` demostró que un scan "amistoso" también puede
  dar falso positivo de bruteforce: lección de tuning para el azul.
