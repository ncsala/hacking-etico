# Contexto del proyecto: Lab Purple Team

## Quién soy y qué estoy haciendo
Estoy aprendiendo ciberseguridad ofensiva/defensiva de forma autodidacta.
A veces me cuesta explicar lo que quiero, así que este archivo resume el
contexto para no tener que explicarlo desde cero en cada sesión.

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

## Alternativas de práctica legal
Hack The Box, TryHackMe, VulnHub, CTFs. Ruta sugerida:
TryHackMe Jr Penetration Tester → HTB Easy/Medium → especialización.

## Documentación del lab (estructura obligatoria)
El lab se documenta en `lab/` de este repo:
- `lab/00-arquitectura.md` — inventario, diagrama, decisiones y por qué
- `lab/bitacora.md` — registro cronológico de cambios (fecha + qué + por qué)
- `lab/configs/` — copia exacta de cada archivo de config aplicado en la
  VPS, con su misma ruta relativa
Regla: **cada cambio en la VPS actualiza bitácora y configs en la misma
sesión**. No se deja nada "para después". El objetivo es que el lab se
pueda reconstruir y re-practicar desde estos documentos.

## Estado actual (actualizado 2026-11-15)
- [x] Inventario de la VPS: una sola (Vultr, Ubuntu 26.04, 1 CPU/1.6GB).
      La web (proyecto-rifa) corre en Docker y sale por Cloudflare
      Tunnel; único puerto público: 22. NO tocar los contenedores.
- [x] Pila de logging elegida: **Suricata + rsyslog** (Wazuh/ELK no
      entran por la RAM)
- [ ] Activar NOPASSWD (con validación visudo) para gestión automatizada
- [ ] Decidir apagar PasswordAuthentication (confirmar que no hay otros
      dispositivos de acceso)
- [ ] Updates + fail2ban + nftables + Suricata
- [ ] Ejercicio E01: portscan SSH → detección en Suricata

## Cómo trabajar conmigo
- Hablá en español rioplatense, directo y sin tecnicismos innecesarios.
- Explicá el "por qué" de cada pieza, no solo el "cómo".
- Cuando algo esté fuera de las reglas de arriba, decímelo y ofreceme la
  alternativa legítima más cercana (así aprendemos el mismo concepto).
