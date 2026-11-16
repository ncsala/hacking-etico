# configs/ — Respaldos de configuración

En esta carpeta van **copia exacta de cada archivo que se configura en la
VPS**, con la misma ruta relativa que tiene allá. Son la fuente de verdad
del lab: si hay que reconstruir la máquina, se restauran desde acá.

Convención:

```
configs/
  etc/ssh/sshd_config.d/99-hardening.conf   ← copia de /etc/ssh/sshd_config.d/...
  etc/nftables.conf                          ← copia de /etc/nftables.conf
  etc/suricata/...                           ← copia de /etc/suricata/...
  etc/fail2ban/...                           ← copia de /etc/fail2ban/...
```

Estado de aplicación: lo que está **aplicado** y qué **pendiente** queda
anotado en `../bitacora.md`. El checklist por fase está en el README de
cada fase (próximamente, `fases/`).

Regla: si el archivo de la VPS cambia, se actualiza la copia acá en la
misma sesión (y se anota en la bitácora).
