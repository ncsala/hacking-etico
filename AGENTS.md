# Contexto del proyecto: Lab Purple Team

## Quién soy y qué estoy haciendo
Estoy aprendiendo ciberseguridad ofensiva/defensiva de forma autodidacta.
A veces me cuesta explicar lo que quiero, así que este archivo resume el
contexto para no tener que explicarlo desde cero en cada sesión.

## Plan a futuro: arquitectura objetivo de dos VPS (definido 2026-11-16)

```
┌──────────────────────┐         ┌──────────────────────┐
│  VPS ROJA            │         │  VPS AZUL (la actual)│
│  (por crear, otro    │  ataques│  Vultr 64.177.41.17  │
│  proveedor, ASN      │────────►│  Ubuntu 26.04        │
│  distinto)           │         │  HARDENING COMPLETO ✓│
│                      │         │  Suricata ✓          │
│  Rol: estación del   │         │  fail2ban ✓          │
│  atacante. Nada más. │         │  nftables ✓          │
│  NO es objetivo.     │         │  web (blanco) ✓      │
└──────────────────────┘         └──────────────────────┘
```

- **Azul**: ya lista. Lado defensor + blanco de práctica.
- **Roja**: pendiente (el usuario la crea cuando pueda — requiere pago/
  apertura). Proveedor distinto a Vultr para tener ASN diferente.
  Toolset previsto: nmap, ffuf, sqlmap, hydra, curl-impersonate.
  Hardening idéntico al de la azul: es pública y se cuida igual.
- **Regla de oro (a pedido del usuario, no negociable):** la roja es la
  silla del atacante, nunca el objetivo. Todos los ataques apuntan a la
  VPS azul y a la web propia. Nada de este lab toca infraestructura de
  terceros, jamás.
- Mientras la roja no exista: la azul se sigue usando como está; los
  ejercicios pueden correr desde la PC local (instalando nmap ahí) o
  esperarse a la roja.
- Al 2026-11-16 la azul está completa y el E01 queda en pausa hasta
  tener nmap local o la roja.

## El escenario que armamos (acordado el 2026-11-15)
Ejercicio **purple team** en mi propia infraestructura:

- **Lado rojo (yo, atacante):** lanzo técnicas desde una máquina mía
  (escaneos, fuzzing, fingerprints, túneles, etc.) contra un objetivo que
  también es mío.
- **Lado azul (defensor):** el objetivo está vigilado con IDS y logging,
  y el objetivo del ejercicio es ver **cómo y cuándo se detecta** cada
  técnica del lado rojo.
- Ciclo: técnica → señal en logs/IDS → análisis de detección → ajuste.

La meta real es entender la pregunta "¿cómo me detectan?" desde el lado
de la detección, practicando en un entorno que controlo.

## Reglas acordadas (no negociables, no insistir)
1. Todos los objetivos del lab son infraestructura mía o de VMs diseñadas
   para ser atacadas (VulnHub, DVWA, Juice Shop, Vulhub, etc.).
2. Nada de esto se apunta a sitios o sistemas de terceros, aunque exista
   supuesta "autorización". Un pentest autorizado trabaja transparente
   (IPs whitelisteada por el cliente, actividad reportada), no oculto.
3. El asistente ayuda con sysadmin, detección, análisis de logs,
   conceptos y técnica de lab; no arma infraestructura de intrusión no
   autorizada ni guías de ocultación contra terceros.

## Metodología: fases ROJA y AZUL separadas (2026-11-16)

A pedido del usuario, el lab NO corre los dos lados simultáneamente:

- **FASE ROJA (a ciegas):** el atacante opera sin ver logs/configs del
  azul. Suricata/fail2ban registran solos en background. El asistente
  apoya SOLO el lado rojo (herramientas, técnica) y no revela telemetría
  del defensor. Entregable rojo: qué logró + su auto-percepción del rastro.
- **PRIORIDAD EXPLÍCITA (reafirmada por el usuario 2026-11-16): TODO el
  trabajo es ROJO hasta el final del final.** Toda la infra, instalación
  de herramientas, pruebas de ataque y campañas corren primero, contra
  la línea de base original. El lado azul (hardening, reglas de
  detección, informe defensivo) se construye RECÉN AL FINAL, después de
  la campaña completa, como entregable. Durante la fase roja: cero
  modificaciones al azul, salvo la cámara Suricata que sigue grabando
  (pasiva, necesaria para que la fase azul tenga datos).
- **FASE AZUL (a libro abierto):** juntos se analizan los logs, se
  reconstruye la campaña desde la telemetría, se escriben las reglas que
  faltan y se arma el informe (E05). Clave del entregable: el gap entre
  "lo que el rojo cree haber dejado" y "lo que realmente quedó".

El marco no cambia en ninguna fase: el blanco es siempre la VPS azul y
la web propia. Nada de terceros, jamás.

### Línea de base de la FASE ROJA (2026-11-16, a pedido del usuario)

El rojo ataca el estado ORIGINAL de la VPS, no el hardening del lab.
Revertido para la fase roja:

| Componente | Fase roja (original) | Vuelve en fase azul |
|---|---|---|
| nftables (nuestro) | ❌ eliminado (ufw original activo: deny incoming, solo 22) | ✓ re-aplicar desde `configs/etc/nftables.conf` |
| ufw | ✅ activo (era el original, lo descubrimos de casualidad) | decisión pendiente (convivencia con nftables) |
| fail2ban | ❌ detenido | ✓ reactivar |
| SSH | ✅ key-only + NOPASSWD (operativo, no afecta superficie) | igual |
| **Suricata** | ✅ **SIGUE grabando** — es la cámara de la fase azul (modo IDS, no bloquea nada) | igual |
| Web + tunnel | ✅ intactos (incidente del forward resuelto) | igual |

Regla derivada del incidente: tras cualquier cambio de firewall, probar
tráfico de host Y de contenedor (curl al sitio desde afuera).

## El juego del lab (definición del ejercicio, 2026-11-16)
Es rojo vs azul sobre infraestructura propia, con objetivos asimétricos:

**Lado rojo — minimizar la huella.** Técnicas permitidas (siempre contra
infraestructura propia o VMs de práctica): escaneo low & slow, timing
evasivo, fragmentación, decoys, user-agents custom, ataques vía jump
host entre VPS propias, living-off-the-land.

**Lado azul — detectar pese al sigilo.** Idea central del lab:
> El rastro cero no existe. Quedan los rastros que el atacante NO
> controla (timing, cadencia, tamaños de paquete, TTL, huella del stack
> TCP, desviación de la línea base) y la telemetría fuera de su alcance
> (captura de paquetes, contadores del firewall, flujos). El defensor no
> encuentra al atacante por "su IP": lo encuentra por anomalías de
> comportamiento.

**Ejercicios tipo "escalera de sigilo":** la misma técnica con ruido
decreciente (ej: `nmap -T4` → `-T1` → `--max-rate 5` → fragmentado) y en
cada peldaño se anota qué se detectó y qué dejó de verse. La tabla
resultado es el entregable.

**Rol del asistente:** construir el lado azul, explicar qué ve cada
telemetría, proponer variantes del ejercicio; nunca optimizing del rojo
para uso fuera del lab.

## Stack previsto
- **VPS propia** como workstation de ataque: Debian/Ubuntu + nmap, ffuf,
  nuclei, hydra, sqlmap; hardening con SSH por llaves, fail2ban,
  nftables (input/forward/NAT + ip_forward).
- **Objetivo vigilado** (otra VPS o contenedor en la misma): Suricata
  (modo IDS, reglas ET-open), Wazuh o ELK centralizando logs, honeytokens.
- **Reglas de detección** escritas a mano (SYN floods a muchos puertos,
  bruteforce SSH, User-Agents de herramientas, etc.).
- Conceptos en estudio: JA3/JA4, TTL y coherencia de fingerprints,
  escaneo low & slow, proxy chaining (en el lab), detección SIEM.

## Stack real instalado (la VPS azul, actualizado 2026-11-16)
- Suricata 8.0.3 en modo IDS sobre `enp1s0` — **con JA3/JA4 integrado de
  fábrica** (features HAVE_JA3/HAVE_JA4). 69k reglas ET-open + reglas
  propias en `/var/lib/suricata/rules/local.rules` (portscan, UA sqlmap,
  bruteforce SSH). Logs: `/var/log/suricata/{eve,fast,stats}.log`
- fail2ban (jail sshd) — ya baneando IPs reales
- nftables: policy drop en input/forward, 22/80/443 abiertos, contadores
  y log de descartados
- SSH: llave + NOPASSWD para `rifa`; **PasswordAuthentication aún ON** ⚠️
- La web (proyecto-rifa) en Docker con Cloudflare Tunnel: blanco de
  práctica. NO tocar los contenedores sin permiso.

## Roadmap de la campaña (definido 2026-11-16)

Un atacante serio no hace técnicas sueltas: hace una campaña. El lab la
simula completa, un ejercicio por fase:

| Ej. | Fase de campaña | Dónde corre | Notas |
|---|---|---|---|
| E01 | Enumeración: escalera de sigilo (nmap -T4 → -T1 → --max-rate → fragmentado) | VPS roja → VPS azul | Tabla "qué se detectó por peldaño" |
| E02 | Recon pasivo: certs TLS, DNS, Shodan-style, JA3/JA4 | VPS roja (sin tocar al azul) | Cero alertas esperadas |
| E03 | Acceso inicial: campaña web contra la API propia (fuzzing, auth, inyecciones) | VPS roja → web | **Backup de la DB antes** (`~/deploy/backup.sh`) |
| E04 | Persistencia simulada: cuentas, tokens, cron | Dentro del lab | Y su detección |
| E05 | Entregable final: tabla técnica → detección + lecciones | Repo | |

**VPS roja (planificada — se crea cuando el usuario pueda, 2026-11-16):**
- ⏳ Estado: PENDIENTE — el usuario la crea en otro momento (requiere
  pago/apertura). Hoy no existe.
- **Límite explícito, escrito a pedido del usuario:** la roja es la
  *estación de ataque*, no un objetivo. TODOS los ataques del lab se
  dirigen a la VPS azul (64.177.41.17) y a la web propia, que son
  infraestructura del usuario. Nada del lab apunta a sistemas de
  terceros, jamás. La roja solo lanza.
- Proveedor DISTINTO a Vultr (ASN diferente — para medir cómo cambia la
  percepción del defensor según el origen: doméstico vs datacenter)
- Specs mínimas alcanzan (1 CPU / 1 GB, Debian 12 o Ubuntu 24.04)
- Rol: workstation del atacante. Toolset: nmap, ffuf, sqlmap, hydra,
  curl-impersonate, jq. Hardening igual que la azul (llaves, fail2ban,
  firewall) — es pública también.
- Posibilidad extra: usarla como jump host (PC → roja → azul) para el
  sub-ejercicio de "atacante que oculta su origen" y su detección por
  comportamiento.

## Alternativas de práctica legal
Hack The Box, TryHackMe, VulnHub, CTFs. Ruta sugerida:
TryHackMe Jr Penetration Tester → HTB Easy/Medium → especialización.

## Documentación del lab (estructura obligatoria)
El lab se documenta en `lab/` de este repo:
- `lab/00-arquitectura.md` — inventario, diagrama, decisiones y por qué
- `lab/bitacora.md` — registro cronológico de cambios (fecha + qué + por qué)
- `lab/campania.md` — **playbook detallado E01–E05**: comandos, reglas de
  detección esperadas, mapeo MITRE ATT&CK, backlog de upgrades del azul
- `lab/configs/` — copia exacta de cada archivo de config aplicado en la
  VPS, con su misma ruta relativa
Regla: **cada cambio en la VPS actualiza bitácora y configs en la misma
sesión**. No se deja nada "para después". El objetivo es que el lab se
pueda reconstruir y re-practicar desde estos documentos.

## Estado actual (actualizado 2026-11-16)
- [x] Inventario de la VPS: una sola (Vultr, Ubuntu 26.04, 1 CPU/1.6GB).
      La web (proyecto-rifa) corre en Docker y sale por Cloudflare
      Tunnel; único puerto público: 22. NO tocar los contenedores.
- [x] Pila de logging elegida: **Suricata + rsyslog** (Wazuh/ELK no
      entran por la RAM)
- [x] NOPASSWD activado (validado con visudo)
- [x] Updates completos + reboot
- [x] fail2ban activo (jail sshd, ya baneando IPs)
- [x] nftables aplicado, persistente y probado post-cambio
- [x] Suricata instalado, configurado, validado y ACTIVO — primeras
      detecciones de ruido de internet en el primer minuto
- [x] ⚠️→✅ PasswordAuthentication OFF (2026-11-16, con validación y
      prueba de conexión; solo entra la llave de la PC local)
- [ ] Ejercicio E01: escalera de sigilo (nmap -T4 → -T1 → --max-rate →
      fragmentado) contra el puerto 22, con tabla de detección por peldaño
- [ ] Línea base documentada (qué es "normal" en la caja)
- [ ] Captura de paquetes off-host (pcap) + honeytokens

## Cómo trabajar conmigo
- Hablá en español rioplatense, directo y sin tecnicismos innecesarios.
- Explicá el "por qué" de cada pieza, no solo el "cómo".
- Cuando algo esté fuera de las reglas de arriba, decímelo y ofreceme la
  alternativa legítima más cercana (así aprendemos el mismo concepto).
