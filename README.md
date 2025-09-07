<<<<<<< HEAD
# Clockify-API
This project allows you to receive, process, and audit webhooks sent by Clockify. It automates the management of user time sessions, records change logs, validates data, and notifies relevant events by email. 
=======
# Clockify Webhook API – ActionTracker

Este proyecto permite recibir, procesar y auditar webhooks enviados por Clockify. Automatiza la gestión de sesiones de tiempo de usuarios, registra bitácoras de cambios, valida datos y notifica por correo los eventos relevantes (como inicios, cierres, ediciones y eliminaciones de sesiones).

## ¿Qué hace esta API?

- Recibe eventos en tiempo real desde Clockify (start, end, edit, delete, manual).
- Guarda usuarios y sesiones en base de datos PostgreSQL.
- Lleva un historial detallado de cada cambio en la bitácora (`sessions_binnacle`).
- Detecta y gestiona inconsistencias como duplicados o modificaciones manuales.
- Envía correos automáticos de notificación a coordinación y usuarios.
- Genera reportes personalizados semanales/mensuales (formato Excel).
- Monitorea sesiones abiertas en tiempo real para detectar tiempos excedidos.

---

## Instalación local

> Requisitos: `Python 3.10+`, `PostgreSQL`, `Docker (opcional)`

### 1. Clonar el repositorio
```bash
git clone git@github.com:actiontracker-solutions/API-CLOCKIFY.git
cd API-CLOCKIFY
```
### 2. Clonar el repositorio
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```
### 3. Crear archivo .env
```bash

# Tokens por tipo de webhook
SECRET_TOKEN=...
CLOCKIFY_SECRET_TOKEN_START=...
CLOCKIFY_SECRET_TOKEN_END=...
CLOCKIFY_SECRET_TOKEN_EDIT=...
CLOCKIFY_SECRET_TOKEN_DELETE=...
CLOCKIFY_SECRET_TOKEN_MANUAL_CREATE=...

# SMTP
MAIL_SERVER=mail.actiontracker.eu
MAIL_PORT=587
MAIL_USE_TLS=TRUE
MAIL_USERNAME=notificaciones@actiontracker.eu
MAIL_PASSWORD=****
MAIL_DEFAULT_SENDER=notificaciones@actiontracker.eu
MAIL_RECIPIENT=clockify@actiontracker.eu
MAIL_RECIPIENTS=coordinacion@actiontracker.eu,gerencia@actiontracker.eu
EMAIL_MAX_RETRIES=3
EMAIL_RETRY_DELAY=5
EMAIL_PROCESS_INTERVAL=5
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=*****
DB_NAME=ClockifyWH
```

### 4. Ejecutar la aplicación
```bash
flask run
```
También puede usar Docker para levantar los servicios si tiene un archivo docker-compose.yml configurado.

# Uso y Endpoints disponibles
La aplicación expone varios endpoints protegidos por tokens:

## Webhooks de Clockify
* POST /webhook/clockify/start – Inicio de sesión

* POST /webhook/clockify/end – Fin de sesión

* POST /webhook/clockify/edit – Edición de sesión

* POST /webhook/clockify/delete – Eliminación de sesión

* POST /webhook/clockify/manual – Creación manual de sesión

Todos exigen el Authorization token correspondiente en el header (Clockify-Signature).

## Reportes personalizados
POST /sessions/api-clockify/reports/user

* **Requiere**: idUser, startDate, endDate, emailToSend. Se envia por cabecera el token correspondiente definido en SECRET_TOKEN

* Devuelve y envía por correo un archivo Excel con las sesiones del usuario en ese rango.

## Búsqueda
* GET /users/search?startDate=YYYY-MM-DD – Usuarios con sesión en una fecha

* GET /binnacle/search?email=...&projectName=... – Buscar en bitácora por criterios


### Características adicionales
* **Auditoría detallada**: Cada modificación a una sesión genera una entrada en sessions_binnacle.

* **Control de overtime**: Se detectan sesiones con duración mayor a 5 horas.

* **Validaciones estrictas**: Estructura, tipos, campos requeridos y tokens.

* **Manejo de errores**: Todos los errores críticos se guardan en la tabla error_log.

* **Notificaciones por correo**: Toda acción relevante se notifica al usuario y a coordinación.


# Preguntas frecuentes (FAQ)
1. **¿Qué pasa si Clockify envía una sesión con un ID externo repetido?**
El sistema lo detecta y lanza un error, guardando el evento en error_log y notificando por correo.

2. **¿Qué pasa si Clockify edita una sesión mientras está abierta?**
Se permite el cambio de startDate, se registra la edición, se incrementa updatingQuantity y se notifica.

3. **¿Qué hago si no recibo correos?**
Verifique la configuración SMTP en el .env y revise que el MAIL_RECIPIENTS incluya el correo deseado.

4. **¿Cuándo se marcan sesiones como overtime?**
Cuando su duración supera las 5 horas, automáticamente se establece session.overtime = True.

# Manual de uso – CRUD de sesiones
Todos los endpoints de esta sección requieren autenticación por token (Authorization header).

BASE URL:
https://su-servidor/api-clockify/sessions

### Obtener todas las sesiones
GET /getAll

Devuelve todas las sesiones registradas.
```bash
curl -H "Authorization: SECRET_TOKEN" https://su-servidor/api-clockify/sessions/getAll
```

### Obtener sesión por ID
GET /getById/<session_id>

Busca una sesión específica por su ID interno.
```bash
curl -H "Authorization: SECRET_TOKEN" https://su-servidor/api-clockify/sessions/getById/15
```
### Obtener sesiones por correo de usuario
GET /getByEmail/<email>

Busca sesiones según el correo del usuario.
```bash
curl -H "Authorization: SECRET_TOKEN" https://su-servidor/api-clockify/sessions/getByEmail/chocha@actiontracker.eu
```

### Crear una nueva sesión
POST /create

Crea una nueva sesión manualmente.
```bash
curl -X POST https://su-servidor/api-clockify/sessions/create \
-H "Authorization: SECRET_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "external_sesion_id": "abc123",
  "description": "Tarea manual",
  "idUser": 42,
  "idProject": "proj789",
  "projectName": "Proyecto Interno",
  "idWorkspace": "ws001",
  "workspaceName": "ActionTracker",
  "idTask": "task001",
  "taskName": "Planeación",
  "startDate": "2025-07-15T08:00:00Z",
  "endDate": "2025-07-15T10:00:00Z",
  "duration": "PT2H",
  "timeZone": "America/Bogota",
  "offsetStart": -18000,
  "offsetEnd": -18000,
  "currentlyRunning": false
}'
```
### Actualizar una sesión existente
PUT /update/<session_id>

Modifica los datos de una sesión específica.
```bash
curl -X PUT https://su-servidor/api-clockify/sessions/update/15 \
-H "Authorization: SECRET_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "description": "Tarea corregida",
  "endDate": "2025-07-15T11:00:00Z"
}'
```

### Eliminar una sesión
DELETE /delete/<session_id>

Elimina una sesión por su ID.
```bash
curl -X DELETE -H "Authorization: SECRET_TOKEN" https://su-servidor/api-clockify/sessions/delete/15
```

### Buscar sesiones con filtros
GET /search/

Permite buscar por múltiples filtros: email, projectName, startDate, taskName, etc.
```bash
curl -H "Authorization: SECRET_TOKEN" \
"https://su-servidor/api-clockify/sessions/search/?email=miguel@actiontracker.eu&projectName=Planeacion"
```
### /approve (POST)
Este endpoint permite aprobar o rechazar sesiones modificadas.

#### Headers
Authorization: token secreto

#### Query Param
externalSesionId: ID externo de la sesión que se desea aprobar/rechazar

#### Body JSON
aprobado: true o false, observacion(opcional): anotaciones del coordinador
```bash
{
  "aprobado": true,
  "observacion": "Se ajustó correctamente el horario"
}

```

# Manual de uso – Envío de reportes periódicos y personalizados (/api-clockify/session-report)

Este endpoint permite probar el envío de reportes semanales o mensuales generados automáticamente a partir de las sesiones registradas. Se ejecuta manualmente para forzar el envío sin necesidad de esperar el cron automático.
También puede generar uno personalizado para un usuario en especifico. 
Todos los endpoints requieren autenticación mediante Authorization con token secreto.
En este caso el token es el mismo de SECRET_TOKEN

### Enviar reportes periódicos manualmente
POST /sendAllReports

Este endpoint permite forzar el envío de todos los reportes semanales o mensuales definidos por el sistema. Los reportes se generan en formato Excel y se envían por correo a cada usuario registrado, incluyendo también a coordinación.

#### Parámetros en el body (JSON):

| Campo	| Tipo	   | Requerido	 | Descripción                                                                                          |
|-------|---------|------------|------------------------------------------------------------------------------------------------------|
|type	| string	 | SI	        | "weekly" o "monthly"                                                                                 |
|month	| int	    | NO	        | (opcional, solo si type es "monthly") Número del mes                                                 |
|year	| int	    | NO	        | (opcional, solo si type es "monthly", por defecto 2025) Año                                          |
|start_date	| date	   | NO	        | (opcional, solo si type es "weekly") Fecha del dia desde donde se quiera calcular el reporte semanal |


#### Ejemplo de uso (cURL):
```bash
curl -X POST https://su-servidor/api-clockify/session-binnacle/reports/sendAllReports \
-H "Authorization: SECRET_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "type": "weekly",        // "weekly" o "monthly"
  "month": 7,              // (opcional, solo si type es "monthly")
  "year": 2025,            // (opcional, por defecto el actual)
  "start_date": "2025-07-14"  // (opcional, solo si type es "weekly")
}'
```
#### Rta esperada
{
  "message": "monthly report sent (test mode)"
}
#### Posibles errores:
* 422: Tipo de reporte inválido (type debe ser "weekly" o "monthly").

* 500: Error interno del servidor (fallo al generar o enviar reportes).

### /user (POST)
Permite enviar un reporte personalizado a un correo específico para un solo usuario.

#### Headers
Authorization: token secreto

#### Body JSON
```bash
{
  "idUser": 12,
  "startDate": "2025-07-14",
  "endDate": "2025-07-21",
  "emailToSend": "coordinacion@empresa.com"
}
```
### Validaciones

Si falta algún campo o es inválido, retorna 400 o 422 según el caso.

Si el usuario no existe, retorna 404.

# Manual de uso – Endpoints de usuarios (/api-clockify/users)

Estos endpoints permiten consultar, crear, actualizar, eliminar y buscar usuarios dentro del sistema sincronizado con Clockify. Todos requieren token de autenticación.

### Obtener todos los usuarios

GET /getAll/

Devuelve la lista completa de usuarios registrados.
```bash
curl -X GET https://su-servidor/api-clockify/users/getAll/ \
-H "Authorization: SECRET_TOKEN"
```

### Buscar usuario por externalUserId

GET /getByExternalId/<external_id>

```bash
curl -X GET https://su-servidor/api-clockify/users/getByExternalId/U123 \
-H "Authorization: SECRET_TOKEN"
```

### Buscar usuario por email
GET /getByEmail/<email>
```bash
curl -X GET https://su-servidor/api-clockify/users/getByEmail/juan@example.com \
-H "Authorization: SECRET_TOKEN"
```

### Crear un nuevo usuario
POST /create/
```bash
curl -X POST https://su-servidor/api-clockify/users/create/ \
-H "Authorization: SECRET_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "name": "Nuevo Usuario",
  "email": "nuevo@example.com",
  "externalUserId": "U999",
  "hoursPerMonth": 160,
  "enable": true
}'
```
### Actualizar usuario por externalUserId
PUT /update/<external_id>
```bash
curl -X PUT https://su-servidor/api-clockify/users/update/U999 \
-H "Authorization: SECRET_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "name": "Usuario Actualizado",
  "email": "actualizado@example.com",
  "enable": false
}'
```
### Eliminar usuario por externalUserId
DELETE /deleteByExternalId/<external_id>
```bash
curl -X DELETE https://su-servidor/api-clockify/users/deleteByExternalId/U999 \
-H "Authorization: SECRET_TOKEN"
```
### Buscar usuarios por filtros
GET /search/?startDate=2025-07-01&toDate=2025-07-15

Permite buscar usuarios según fechas asociadas a sus sesiones.

| Filtro      | Tipo   | Descripción                          |
| ----------- | ------ | ------------------------------------ |
| `startDate` | string | Buscar usuarios con sesiones ese día |
| `fromDate`  | string | Fecha inicial para rango             |
| `toDate`    | string | Fecha final para rango               |

```bash
curl -X GET "https://su-servidor/api-clockify/users/search/?fromDate=2025-07-01&toDate=2025-07-15" \
-H "Authorization: SECRET_TOKEN"
```
# Manual de uso – Endpoints de Bitácora de sesiones (/api-clockify/session-binnacle)
Estos endpoints permiten consultar y registrar cambios en las sesiones de Clockify. La bitácora es solo de lectura y auditoría: no se actualiza ni elimina, solo se crean entradas nuevas para rastrear ediciones.

Todos los endpoints requieren autenticación mediante Authorization con token secreto.
### Obtener todas las bitácoras
GET /getAll/

Retorna todas las entradas de bitácora registradas en el sistema.
```bash
curl -X GET https://su-servidor/api-clockify/session-binnacle/getAll/ \
-H "Authorization: SECRET_TOKEN"
```
### Obtener bitácora por ID
GET /getById/<id_binnacle>

Consulta una entrada específica de bitácora.
```bash
curl -X GET https://su-servidor/api-clockify/session-binnacle/getById/42 \
-H "Authorization: SECRET_TOKEN"
```

### Obtener bitácoras por ID de sesión
GET /getByIdSession/<id_sesion>

Muestra todas las entradas de bitácora asociadas a una misma sesión.
```bash
curl -X GET https://su-servidor/api-clockify/session-binnacle/getByIdSession/24 \
-H "Authorization: SECRET_TOKEN"
```

### Crear una nueva entrada de bitácora
POST /create/

Registra manualmente una entrada de bitácora.
```bash
curl -X POST https://su-servidor/api-clockify/session-binnacle/create/ \
-H "Authorization: SECRET_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "idSesion": 24,
  "description": "Cambio manual",
  "startDate": "2025-07-15T08:00:00Z",
  "modificatedAt": "2025-07-15T09:00:00Z"
}'
```

**Nota**: Generalmente las bitácoras se crean automáticamente, pero este endpoint permite registrar eventos de manera manual si es necesario.

### Buscar bitácoras por filtros
GET /search/?email=juan@example.com&startDate=2025-07-10

Permite filtrar las bitácoras por:

| Filtro               | Tipo   | Descripción                      |
| -------------------- | ------ | -------------------------------- |
| `email`              | string | Email del usuario                |
| `external_sesion_id` | string | ID externa de la sesión Clockify |
| `projectName`        | string | Nombre del proyecto              |
| `startDate`          | string | Fecha exacta (YYYY-MM-DD)        |

```bash
curl -X GET "https://tu-servidor/api-clockify/session-binnacle/search/?email=juan@example.com&projectName=Internal" \
-H "Authorization: SECRET_TOKEN"
```

## Webhooks duplicados de Clockify: comportamiento esperado y manejo en ActionTracker

En ocasiones, el sistema puede recibir dos (o más) webhooks casi idénticos de Clockify con el mismo external_sesion_id, enviados en milisegundos de diferencia.

Este comportamiento ha sido observado, por ejemplo, cuando se inicia una sesión (/webhook/clockify/start), donde se registran dos eventos con el mismo contenido pero procesados como si fueran dos solicitudes.

### ¿Por qué ocurre?
Aunque Clockify no lo documenta explícitamente como comportamiento esperado, es un patrón común en servicios que usan webhooks. La duplicación puede deberse a:

* Retries por fallos de red o respuesta lenta.
* Falta de confirmación (ACK) por parte del servidor receptor.
* Naturaleza asincrónica del sistema que envía el webhook.

Y aunque no lo advierten directamente, la ausencia de confirmación manual o firma criptográfica implica que no hay garantía de entrega única. Esto es normal para este tipo de sistema de webhooks que siguen un modelo "fire and forget".

### Referencias de comportamientos similares:

[Stripe Webhooks – Delivery and Retry:](https://stripe.com/docs/webhooks/best-practices)

"Webhook endpoints might receive the same event more than once. We recommend making your webhook handlers idempotent."

[GitHub Webhooks:](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks)

"GitHub may deliver the same webhook more than once."

[Twilio Webhooks:](https://www.twilio.com/docs/events/event-delivery-and-duplication)

"Your application should be able to handle duplicate requests. It is possible that Twilio will send the same webhook more than once."
>>>>>>> de2af5b (Initial commit: Clockify API (webhooks, reports, email queue))
