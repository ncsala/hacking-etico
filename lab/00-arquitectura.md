# Lab Purple Team — Arquitectura

> Última actualización: 2026-11-15 (sesión inicial)
> Objetivo del lab: entender "¿cómo me detectan?" practicando ambos lados
> (rojo ataca, azul detecta) sobre infraestructura propia.

## Diagrama general

```
┌─────────────────────┐                        ┌───────────────────────────────┐
│  PC local (Vultr SSH key) │                    │  VPS Vultr 64.177.41.17       │
│                     │                        │  Ubuntu 26.04 LTS, 1 CPU      │
│  Lado ROJO          │──── ataques (nmap, ───►│  1.6 GB RAM, 52 GB disco      │
│  (workstation       │      ffuf, sqlmap,     │  (IPs documentadas abajo)     │
│  del atacante)      │      hydra, ...)       │                               │
└─────────────────────┘                        │  Lado AZUL + OBJETIVO:        │
                                               │   • Suricata IDS (enp1s0)     │
                                               │   • rsyslog/journald          │
                                               │   • fail2ban (SSH)            │
                                               │   • nftables                  │
                                               │   • Web propia (Docker)       │
                                               │     = blanco de práctica      │
                                               └───────────────────────────────┘
```

## Inventario de la VPS (levantado 2026-11-15)

| Componente | Detalle |
|---|---|
| Host | Vultr, Ubuntu 26.04 LTS, kernel 7.0.0-29-generic, x86_64 |
| Recursos | 1 CPU, 1.6 GB RAM, swap 5.3 GB, disco 52 GB (29% usado) |
| IP pública | 64.177.41.17 (interfaz `enp1s0`, /23) |
| Usuario de gestión | `rifa` (grupos: sudo, users, docker) |
| SSH | Puerto 22, llave autorizada (1), `PermitRootLogin no`, `PasswordAuthentication yes` ⚠️ |
| Sudo | Password requerido → pendiente activar `NOPASSWD` (con validación visudo) |

## La web (blanco de práctica) — NO tocar sin permiso explícito

Corre en Docker Compose (carpeta `~/deploy`), en marcha desde hace ~5 semanas:

| Contenedor | Imagen | Puerto | Nota |
|---|---|---|---|
| deploy-web-1 | ghcr.io/ncsala/proyecto-rifa-web:v0.1.17 | 3000 (interno) | Frontend |
| deploy-api-1 | ghcr.io/ncsala/proyecto-rifa-api:v0.1.17 | 8080 (interno) | Backend |
| deploy-postgres-1 | postgres:16-alpine | 127.0.0.1:5432 | Solo localhost |
| deploy-cloudflared-1 | cloudflare/cloudflared:latest | — | **La web sale por Cloudflare Tunnel, no por puertos abiertos** |

### Consecuencia importante para el lab

La superficie externa real de la VPS es **solo el puerto 22**. Los ataques
web por el dominio llegan cifrados desde las IPs de Cloudflare vía túnel
(que la VPS abrió hacia afuera), así que Suricata no ve el contenido HTTP
de ese camino. Para ejercicios web se planea publicar el contenedor web
en un puerto directo (limitado con nftables a la IP de casa), donde el
tráfico sí es inspeccionable.

## Decisiones de diseño (y por qué)

| Decisión | Motivo |
|---|---|
| Una sola VPS para empezar | Es la que existe; para entrenar detección alcanza. Segunda VPS (o VM local) como workstation roja más adelante si hace falta |
| **Suricata + rsyslog, no Wazuh/ELK** | 1 CPU / 1.6 GB RAM no da para un SIEM. Suricata es liviano y el análisis se hace leyendo logs a mano — que es justo lo que enseña más |
| nftables y no ufw | Control fino y es lo que se estudia en el lab (input/forward/NAT explícito) |
| Ataques desde la PC local | La IP de casa queda documentada como "IP del atacante del lab" — en un lab propio eso es una feature, permite filtrar/identificar las señales del lado rojo |
| Atacar el puerto 22 primero | Es la superficie real: portscan + detección es el primer ejercicio honesto posible |

## IP del lado rojo (atacante)

- 186.53.225.232 (última conexión SSH documentada en el login del host)
- ⚠️ Dinámica presumiblemente — verificar en cada ejercicio

## Plan a futuro (2026-11-16): arquitectura de dos VPS

Segunda VPS **roja** (estación de ataque, proveedor distinto a Vultr para
diferencia de ASN) → ataca a la **azul** (esta máquina). El detalle
completo del plan, la regla de oro ("la roja lanza, la azul recibe, nada
apunta a terceros") y el roadmap de campaña (E01–E05) están en el
`AGENTS.md` del repo. Hoy la azul está completa; la roja queda pendiente
de creación por el usuario.

## Pendientes de la arquitectura

- [ ] VPS roja: crearla cuando el usuario pueda (proveedor ≠ Vultr)
- [ ] Con la roja: instalar toolset del atacante + hardening igual a la azul
- [ ] puerto de lab para exponer la web inspeccionable (E03)
- [ ] honeytokens + captura de paquetes off-host
