# E02 — Recon pasivo de hayrifa.uy (dossier del atacante)

> Fase ROJA. Fecha: 2026-11-16 ~01:44 UTC. Cero paquetes hacia la
> infraestructura propia: todo OSINT de terceros públicos (CT logs, DNS
> público, RDAP, HTTP vía Cloudflare).
> Marco: dominio propio del usuario; no se apunta a terceros.

## 1. Superficie descubierta

| Dato | Resultado | Lectura del atacante |
|---|---|---|
| Cert TLS vigente | `hayrifa.uy` + `*.hayrifa.uy`, Google Trust Services (WE1), vence 2027-01-05 | Rota cada ~3 meses (CF auto). Wildcard: los subdominios comparten cert |
| crt.sh (certs históricos) | Solo apex + wildcard | Limpio: no hay subdominios olvidados en CT logs |
| DNS A | 172.67.150.99, 104.21.71.225 (Cloudflare) | **Origen NO expuesto en DNS** — el IP real queda detrás de CF |
| MX | route1/2/3.mx.cloudflare.net | Mail vía Cloudflare Email Routing |
| TXT | SPF cloudflare (~all) + google-site-verification | Mail manejado en edge; usa Google Search Console (OSINT menor) |
| NS | margaret/dale.ns.cloudflare.com | Todo el DNS en CF |
| CAA | **vacío** | Cualquier CA puede emitir certs para el dominio |
| Subdominios por guess | **api.hayrifa.uy existe** (proxied); los otros 9: nada | El blanco API es la segunda puerta |
| RDAP dominio .uy | 404 — sin servicio RDAP | Recon tooling: ccTLD sin RDAP → caer a whois/nic.uy |
| RDAP IP 64.177.41.17 | Bloque 64.176.0.0–64.177.255.255, CHOOP-1, The Constant Company (Vultr), direct allocation | Confirma: VPS en datacenter. El azul asume que esto es público |
| **Estado del target** | **HTTP 530 (origin unreachable) en apex y api, vía CF** | El blanco está CAÍDO para el atacante en este momento |

## 2. Conclusiones tácticas del rojo

1. **El túnel de Cloudflare es la mejor defensa del origen**: sin
   puertos entrantes (80/443 cerrados en el IP real) ni cert en el
   origen que se pueda escanear (Censys/Shodan por cert fallaría).
   Descubrir el origen requeriría fugas menos probables: headers de
   mails salientes, históricos de DNS pagados (SecurityTrails), o
   errores de config futuros.
2. **La superficie HTTP real es lo que CF deja pasar**: cf-ray EZE
   (PoP Buenos Aires), headers de CF. El blanco para la campaña web
   (E03) es apex + api, ambos detrás del WAF de CF.
3. **La app está caída (530)**: para el atacante esto es un estado, no
   un hallazgo — para el DUEÑO es un problema real a verificar.
4. **CAA vacío** es higiene pendiente (fase azul: agrega CAA para
   restringir CAs).

## 4. Recon de la app (superficie HTTP, vía Cloudflare — extensión E02)

| Dato | Resultado | Lectura del atacante |
|---|---|---|
| Tech stack | `x-powered-by: Next.js` (header expuesto) | Framework conocido → superficie tipo Next (rutas server actions, API routes) |
| Redirect raíz | 307 → `/raffle/01a0552c-...` (rifa activa) | El patrón de URL revela la estructura: `/raffle/<id>` + sub-ruta `/resultado` |
| **ID de rifa** | **UUID v7** (versión 7 confirmada) — decodificado: **timestamp 2026-08-31T00:15 UTC** (día del deploy) | v7 codifica el epoch ms: IDs creados cerca en el tiempo son parcialmente predecibles/enumerables → riesgo de enumeración/IDOR a revisar en fase azul |
| sitemap.xml | 200: lista la rifa activa, `/raffle/<id>/resultado`, `/mis-numeros`, `/terminos`, `/privacidad` | Mapa del sitio servido voluntariamente: confirma rutas y la página de tickets de usuario |
| `/mis-numeros` sin sesión | **200 (sin redirect)** | Página de tickets responde sin auth — puede ser guard client-side (Next) o authz real: a verificar en E03 (el que decide es el API, no el render) |
| API (`api.hayrifa.uy`) | 404 en `/`, `/health`, `/docs`, `/openapi.json` | API existe pero endpoints no obvios: descubrir con el tráfico real de la app (JS del frontend revela las rutas del API) |
| security.txt | 404 | Menor |

## 5. Qué NO se pudo ver (y por qué es la lección del E02)

- El IDS azul no registró nada de este recon: **no hay detección
  posible del recon pasivo** (ningún paquete llegó a la infra).
  La única contramedida es la higiene pública (menos records, CAA,
  subdominios muertos fuera) — que es trabajo de config, no de red.
- El IP de origen no aparece en ningún registro público consultado.

## 4. Pendiente

- [ ] Verificar el 530 (¿caída intencional del sitio o problema real
  del tunnel?) — acción del dueño, fuera de la fase roja
- [ ] Continuar recon HTTP de la app cuando esté arriba (E03)
