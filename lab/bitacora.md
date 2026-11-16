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
