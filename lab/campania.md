# Playbook de campaña del lab — E01 a E05

> Detalle completo del plan "ultra realista" del lab purple team.
> MARCO (no negociable): todos los ataques van contra la VPS azul
> (64.177.41.17) y la web propia. La VPS roja solo lanza. Nada de este
> playbook apunta a infraestructura de terceros, jamás.

## Reglas generales de operación

1. **Backup antes de tocar** la web/DB (`~/deploy/backup.sh` en la azul).
2. **Rate limits en el rojo**: la azul tiene 1 CPU — un fuzzing sin
   límites es un DoS a mi propio server. `ffuf -rate` y `sqlmap --delay`
   siempre. Protegerse de sí mismo también es lección del lab.
3. **Toda técnica se ejecuta con su línea de comando registrada** en la
   bitácora al momento (no "después la escribo").
4. **Cada técnica tiene una fila en la tabla de detección** (ver E05).
5. Stop condition: si algo tumba un servicio propio más allá del
   ejercicio, revertir y documentar el incidente (¡también es lección!).

---

## E01 — Escalera de sigilo (enumeración activa)

**Fase ATT&CK:** T1046 (Network Service Scanning)
**Objetivo rojo:** mapear la superficie externa de la azul con ruido
decreciente. **Objetivo azul:** saber qué peldaño se ve y cuál no.

Se corre desde la VPS roja (o PC local si no hay roja aún). Antes de
arrancar, en la azul limpiar el tablero:

```bash
# azul: pos base
sudo wc -l /var/log/suricata/fast.log
sudo nft list chain inet filter input | grep counter   # contadores
```

| Peldaño | Comando (desde la roja) | Ruido | Detección esperada |
|---|---|---|---|
| 1 | `nmap -T4 -p 1-1000 64.177.41.17` | 🔊 | `LAB Portscan 20puertos/60s` (sid 1000001) dispara seguro |
| 2 | `nmap -T1 --max-rate 5 -p 22,80,443,3000,8080,5432` | 🤫 | No dispara 1000001 (< 20 puertos). Aprender: la regla umbral tiene ceguera |
| 3 | `nmap -f -T1 -p 22,80,443` (fragmentado) | 🪓 | Ver si Suricata reensambla ( debería: stream reassembly está activo por defecto) |
| 4 | `nmap --data-length 24 --randomize-hosts -T1` | 🎭 | Payload random: no matchea firmas de scanner |

**Qué mirar en la azul después de cada peldaño:**

```bash
sudo tail -5 /var/log/suricata/fast.log
# y con detalle completo (EVE):
sudo tail -50 /var/log/suricata/eve.json | jq 'select(.event_type=="alert") | {ts, src_ip, alert: .alert.signature_id, sig: .alert.signature}'
```

**Entregable E01:** tabla con columnas: peldaño / comandos / ¿disparó?
/ qué regla / qué habría que agregar para detectarlo igual en silencio.
La respuesta tipo: umbral de puertos + *score de cadencia* (los SYN de
nmap tienen timing reconocible aunque sean lentos).

**Detección extra para implementar (lección del ejercicio):** regla de
timing: SYN con TTL y window coherentes entre sí pero frecuencia baja
sostenida hacia puertos cerrados → anomalía de "curiosidad" no de
"firma".

---

## E02 — Recon pasivo (sin tocar a la azul)

**Fase ATT&CK:** T1595.002 pre-intrusion / OSINT
**Objetivo rojo:** perfil del objetivo sin enviar 1 paquete a la azul.
**Objetivo azul:** entender que ESTO no se detecta con IDS — la única
defensa es minimizar lo que se expone en público.

```bash
# certificado TLS del sitio propio (vía el dominio, no la IP)
openssl s_client -connect mi-dominio.com:443 -servername mi-dominio.com < /dev/null 2>/dev/null | openssl x509 -noout -text | grep -E "Subject:|DNS:|Not"
# certificados históricos emitidos para el dominio (crt.sh se consulta desde el rojo)
curl -s "https://crt.sh/?q=%25.mi-dominio.com&output=json" | jq -r '.[].name_value' | sort -u
# DNS público
dig +short mi-dominio.com ANY; dig +short MX mi-dominio.com; dig +short TXT mi-dominio.com
# quién "es" el dueño del bloque de IP
whois 64.177.41.17 | grep -iE "org|netname|country"
```

**Lecciones esperadas:**
- Subdominios olvidados aparecen en crt.sh → superficie desconocida.
- El TXT/MX revelan proveedores (SPF = quién manda mails legítimo).
- Contra-medidas del azul: no son de red sino de higiene (borrar
  subdominios muertos, minimizar records, certs wildcard vs específicos).

---

## E03 — Campaña web contra la API propia

**Fase ATT&CK:** T1190 (Exploit Public-Facing Application)
**PRE-REQUISITO ABSOLUTO:** backup de DB y verificación:

```bash
# azul
cd ~/deploy && ./backup.sh && ls -la backups/   # confirmar que se creó
```

**Paso 0 — exponer la web de forma inspeccionable.** La web sale por
Cloudflare Tunnel (cifrada y desde IPs de CF): Suricata no ve el HTTP.
Para el lab se publica un puerto directo:

```yaml
# ~/deploy/docker-compose.lab.yml (override, NO toca el prod)
services:
  web:
    ports:
      - "8081:3000"
```

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.lab.yml up -d web
# nftables: permitir 8081 SOLO desde la IP de la VPS roja
sudo nft add rule inet filter input tcp dport 8081 ip saddr <IP_ROJA> accept
```

**Pasos del ejercicio (desde la roja):**

```bash
# 1. fingerprinting: qué responde, qué headers, qué framework
curl -sI http://64.177.41.17:8081 | head -20
# 2. descubrimiento de endpoints (rate-limited, wordlist common)
ffuf -u http://64.177.41.17:8081/FUZZ -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt -rate 30 -mc 200,301,302,401,403
# 3. brute force de login de la app (hydra/ffuf según el form)
# 4. fuzzing de parámetros y SQLi controlada con sqlmap (SOLO endpoints de
#    prueba, con --delay 1 --risk 2, NUNCA contra endpoints de escritura)
sqlmap -u "http://64.177.41.17:8081/api/endpoint?param=1" --batch --delay 1 --risk 2 --level 2
# 5. auth bypass: probar IDs de secuencia, JWT mal firmados, rutas sin token
```

**Detección esperada (y reglas a agregar al azul si no existen):**

```bash
# Suricata ya tiene: UA sqlmap (sid 1000002). Agregar según lo que aparezca:
# - UA de ffuf/go-fuzz (tiene UA propio reconocible)
# - requests a rutas inexistentes en volumen → 404-rate anomalía
# - access log del contenedor web: revisar docker logs deploy-web-1
```

**Nota realista:** contra Cloudflare Tunnel (el camino prod), CF hace de
WAF: los ejercicios web van por el puerto directo del lab. Comparar
ambos caminos (¿qué filtra CF solo?) es un sub-ejercicio valioso.

---

## E04 — Persistencia simulada

**Fase ATT&CK:** T1053 (Scheduled Task), T1098 (Account Manipulation), T1098.005 (SSH keys)
**Objetivo rojo:** lograr 3 mecanismos de "vuelta". **Objetivo azul:** detectarlos.

Simulaciones inocuas y reversibles (todas con ID de ejercicio en el nombre):

```bash
# P1: usuario nuevo con shell (T1098)
sudo useradd -m -s /bin/bash lab-persist-usr
# P2: cron que "late" a la roja cada 5 min (T1053)
echo '*/5 * * * * curl -s http://<IP_ROJA>:9999/heartbeat' | sudo tee /etc/cron.d/lab-persist
# P3: llave SSH extra en authorized_keys (T1098.005)
echo '<llave_de_prueba>' >> ~/.ssh/authorized_keys
```

**Detección azul (checklist a construir en este ejercicio):**
- P1: `last`, `getent passwd | grep lab-`, journalctl de useradd
- P2: `systemctl list-timers`? no — es cron: `ls /etc/cron.d/`, y en
  Suricata: la blue debería ver la request saliente periódica
  (regla: HTTP saliente cíclico hacia IP de datacenter)
- P3: diff de authorized_keys (base del "file integrity": md5/sha256
  snapshot pre-ejercicio → post → diff)
- **Upgrade azul a implementar:** snapshot de hashes de archivos críticos
  (authorized_keys, /etc/passwd, cron) antes de cada ejercicio.

**Cleanup E04 (parte del entregable):**

```bash
sudo userdel -r lab-persist-usr; sudo rm /etc/cron.d/lab-persist
# revocar la llave: editar authorized_keys
```

---

## E05 — Informe final (el entregable del lab)

Tabla única de toda la campaña, con mapeo ATT&CK:

| Ej | Técnica | ATT&CK | Comando/línea | ¿Se detectó? | Dónde (regla/log) | Gap del azul | Fix propuesto |
|---|---|---|---|---|---|---|---|

Más secciones: timeline de la campaña, qué expone el recon pasivo,
hallazgos sobre la propia web (¡los de E03 son hallazgos REALES de
seguridad de tu app —van a un backlog de fixes!), y conclusiones del
juego rojo/azul.

---

## Upgrades pendientes del lado azul (backlog)

- [ ] Honeytokens: `.env` trampa, ruta admin falsa, buzón canary
- [ ] Captura de paquetes: ring buffer `tcpdump -i enp1s0 -W 8 -C 50`
      (limitación honesta: mismo host = alcanzable por un root intruso;
      off-host real cuando haya dónde)
- [ ] Snapshot de integridad de archivos críticos (hashes pre-ejercicio)
- [ ] regla Suricata de timing/cadencia (resultado esperado del E01)
- [ ] auditd para syscalls (logins, execs) — evaluar RAM primero
