# Hestia Updater: DNS Dinámico para Hestia CP y Cloudflare

Aplicación Python diseñada para automatizar la actualización de registros DNS en Cloudflare y la sincronización de la IP del sistema en HestiaCP. Ideal para servidores con direcciones IP dinámicas, como aquellas obtenidas mediante PPPoE.

# Objetivos

1. Detectar la nueva IP externa después de la reconexión de PPP (IP en texto plano).
2. Usar `/usr/local/hestia/bin/v-list-users json` para obtener todos los usuarios de HestiaCP.
3. Para cada usuario, usar `/usr/local/hestia/bin/v-list-web-domains <user> json` para obtener sus dominios.
4. Para cada dominio, actualizar todos los registros DNS (A) en Cloudflare para que apunten a la nueva IP.
   - Saltar los dominios (obtenidos de v-list-web-domains) listados en una lista configurable de exclusión.
5. Ejecutar `/usr/local/hestia/bin/v-update-sys-ip` para actualizar la IP del sistema en HestiaCP.
6. Registrar todas las actividades, éxitos y errores en `debian syslog`, identificando el componente fuente.

## Funcionalidades Principales

- **Detección de IP Externa**: Identifica automáticamente la nueva dirección IP pública del servidor.
- **Integración con HestiaCP**: Obtiene la lista de usuarios y sus dominios web directamente desde HestiaCP.
- **Actualización de Cloudflare DNS**: Modifica los registros DNS (A) en Cloudflare para que apunten a la nueva IP.
  - Soporta la exclusión de dominios específicos.
  - Maneja la obtención dinámica del ID de Zona si no se especifica uno global.
- **Sincronización de IP en HestiaCP**: Ejecuta el comando `/usr/local/hestia/bin/v-update-sys-ip` para informar a HestiaCP sobre el cambio de IP.
- **Logging Detallado**: Registra todas las operaciones importantes y errores en `syslog` para facilitar el seguimiento y la depuración.

## Requisitos Previos

- Servidor con HestiaCP (probado en Debian 12).
- Python 3.x.
- Conexión a Internet para consultar servicios de IP y la API de Cloudflare.
- Cuenta de Cloudflare gestionando los DNS de los dominios alojados en HestiaCP.

## Configuración

La aplicación se configura mediante variables de entorno, gestionadas a través de un archivo `.env`.

> **Nota importante sobre la ubicación de `.env`**:
> - En desarrollo, el archivo `.env` se busca primero junto al código fuente.
> - En producción, si no se encuentra el archivo `.env` local, la aplicación intentará cargar automáticamente `/etc/hestia-pppoe/.env` como último recurso.
> - Esto permite mantener una configuración centralizada y segura para entornos productivos.

1.  **Crear archivo `.env`**: Copie el archivo de ejemplo `.env.example` a `.env` en la raíz del proyecto:
    ```bash
    cp .env.example .env
    ```
2.  **Editar `.env`**: Modifique las siguientes variables según su configuración:
    - `CLOUDFLARE_API_TOKEN`: TOKEN de API de Cloudflare. Obtenga uno en https://dash.cloudflare.com/profile/api-tokens
    - `CLOUDFLARE_API_BASE_URL`: URL base de la API de Cloudflare (valor predeterminado: `https://api.cloudflare.com/client/v4`)
    - `CLOUDFLARE_ZONE_ID`: ID de Zona de Cloudflare (opcional, si no se especifica, se obtendrá dinámicamente)
    - `V_LIST_USERS_PATH`: Ruta al comando de HestiaCP para obtener la lista de usuarios (valor predeterminado: `/usr/local/hestia/bin/v-list-users`)
    - `V_LIST_WEB_DOMAINS_PATH`: Ruta al comando de HestiaCP para obtener la lista de dominios web de un usuario (valor predeterminado: `/usr/local/hestia/bin/v-list-web-domains`)
    - `V_UPDATE_SYS_IP_PATH`: Ruta al comando de HestiaCP para actualizar la IP del sistema (valor predeterminado: `/usr/local/hestia/bin/v-update-sys-ip`)
    - `CLOUDFLARE_EXCLUDED_DOMAINS`: Dominios excluidos de la actualización de Cloudflare DNS (valor predeterminado: lista vacía)
  
## Empaquetado y Despliegue

El script está diseñado para ser empaquetado como un único binario ejecutable para Linux usando `shiv`.

1.  **Instalar dependencias de compilación** (en su máquina de desarrollo o en un entorno Debian 12):
    ```bash
    pip install shiv
    ```
2.  **Generar el binario**: Ejecute el script de compilación proporcionado:
    ```bash
    # Asegúrese de que el script tenga permisos de ejecución
    chmod +x scripts/build.sh
    bash scripts/build.sh
    ```
    
    ```bash
    ./hestia-pppoe/scripts/build.sh [opciones]
    ```

    Opciones principales:
    - `-i`, `--include-env`   Incluye el archivo `.env` dentro del binario generado.
    - `-n`, `--no-env`        No incluye ni copia ningún archivo `.env` (deberá gestionar las variables de entorno por otros medios).
    - (sin opciones)          Copia el archivo `.env` externo junto al binario en la carpeta de salida.

    **Ejemplos de uso:**
    - Empaquetar incluyendo `.env` en el binario:
      ```bash
      ./hestia-pppoe/scripts/build.sh --include-env
      ```
    - Empaquetar sin ningún `.env` (solo variables externas):
      ```bash
      ./hestia-pppoe/scripts/build.sh --no-env
      ```
    - Empaquetar con `.env` externo (por defecto):
      ```bash
      ./hestia-pppoe/scripts/build.sh
      ```

## Uso Automatizado (Tras Empaquetado)

El binario generado (ej. `hestia_updater`) debe ser copiado al servidor HestiaCP.
Para automatizar su ejecución tras un cambio de IP (por ejemplo, al establecer una conexión PPPoE), se puede enlazar en el directorio `/etc/ppp/ip-up.d/`.

1.  **Copiar el binario al servidor**:
    ```bash
    sudo cp dist/linux/hestia_updater /usr/local/bin/hestia_updater
    sudo chmod +x /usr/local/bin/hestia_updater 
    ```

**Nota sobre `.env` en producción**: Cuando se ejecuta desde `/etc/ppp/ip-up.d/`, el script podría no encontrar el archivo `.env` si no se especifica la ruta correcta o si el directorio de trabajo no es la raíz del proyecto. Considere:
    - Colocar el archivo `.env` en una ubicación accesible y conocida.
    - Modificar el script `hestia_updater` para buscar `.env` en una ruta absoluta o relativa a la ubicación del script.
    - O, preferiblemente para producción, gestionar las variables de entorno a través del entorno de ejecución del script `ip-up.d` o mediante un archivo de configuración de systemd si se gestiona como un servicio.

## Dependencias del Proyecto

Las dependencias de Python se listan en `requirements.txt`. Las principales son:
- `python-dotenv`: Para cargar la configuración desde el archivo `.env`.
- `requests`: Para realizar solicitudes HTTP a los servicios de IP y a la API de Cloudflare.
- `shiv`: Para el empaquetado (dependencia de desarrollo/compilación).

Instalar dependencias para desarrollo:
```bash
pip install -r requirements.txt
```

## Estructura del Código Fuente

## Notas Técnicas Adicionales

Esta sección proporciona detalles técnicos sobre las interacciones con HestiaCP y la API de Cloudflare que pueden ser útiles para el desarrollo, la depuración o la comprensión profunda del funcionamiento de la aplicación.

### Interacción con HestiaCP CLI

La aplicación interactúa con los siguientes comandos de la CLI de HestiaCP. Se asume que estos comandos están disponibles en el `PATH` del sistema donde se ejecuta el script y que el script tiene los permisos necesarios para ejecutarlos (generalmente se ejecuta como `root` cuando es invocado por `/etc/ppp/ip-up.d/`).

1.  **`v-list-users json`**
    *   **Propósito**: Obtener una lista de todos los usuarios gestionados por HestiaCP.
    *   **Uso**: Se ejecuta como `v-list-users json`.
    *   **Salida Esperada (JSON)**: Un objeto JSON donde cada clave es un nombre de usuario y el valor es un objeto con detalles del usuario. La aplicación solo utiliza las claves (nombres de usuario).
        ```json
        {
          "admin": { ... detalles ... },
          "user1": { ... detalles ... }
        }
        ```

2.  **`v-list-web-domains <username> json`**
    *   **Propósito**: Obtener una lista de todos los dominios web asociados a un usuario específico.
    *   **Uso**: Se ejecuta como `v-list-web-domains <nombre_de_usuario> json`.
    *   **Salida Esperada (JSON)**: Un objeto JSON donde cada clave es un nombre de dominio y el valor es un objeto con detalles del dominio. La aplicación solo utiliza las claves (nombres de dominio).
        ```json
        {
          "domain1.com": { ... detalles ... },
          "sub.domain2.com": { ... detalles ... }
        }
        ```

3.  **`v-update-sys-ip`**
    *   **Propósito**: Informar a HestiaCP sobre un cambio en la dirección IP principal del sistema. Este comando actualiza internamente las configuraciones de red de HestiaCP y los servicios que gestiona (DNS local, Apache, Nginx, etc.).
    *   **Uso**: Se ejecuta como `v-update-sys-ip`.
    *   **Salida Esperada**: Este comando no produce salida. La aplicación verifica el código de retorno del proceso: un código `0` indica éxito, cualquier otro valor indica un error.

### Interacción con la API de Cloudflare

La aplicación utiliza la API v4 de Cloudflare para gestionar los registros DNS. Se enfoca exclusivamente en registros de tipo `A` (IPv4).

-   **Autenticación**: Se utiliza un Token de API de Bearer (`CLOUDFLARE_API_TOKEN`) con permisos para leer información de la zona y leer/editar registros DNS.
-   **Base URL**: `https://api.cloudflare.com/client/v4`

**Endpoints Principales Utilizados:**

1.  **`GET /zones`**
    *   **Propósito**: Obtener el `zone_id` para un nombre de dominio si no se ha proporcionado uno globalmente (`CLOUDFLARE_ZONE_ID`).
    *   **Parámetros Clave**: `name=<domain_name>`, `status=active`.
    *   **Respuesta Exitosa Esperada (JSON)**: Un objeto con `"success": true` y un array `"result"` que contiene objetos de zona. Se utiliza el `id` de la primera zona devuelta.
        ```json
        {
          "result": [
            {
              "id": "CLOUDFLARE_ZONE_ID_EXAMPLE",
              "name": "example.com",
              ...
            }
          ],
          "success": true,
          "errors": [],
          "messages": []
        }
        ```

2.  **`GET /zones/{zone_id}/dns_records`**
    *   **Propósito**: Listar los registros DNS existentes de tipo `A` para un nombre de dominio específico dentro de una zona.
    *   **Parámetros Clave**: `name=<full_domain_name>`, `type=A`.
    *   **Respuesta Exitosa Esperada (JSON)**: Objeto con `"success": true` y `"result"` siendo un array de objetos de registro DNS.
        ```json
        {
          "result": [
            {
              "id": "CLOUDFLARE_RECORD_ID_EXAMPLE",
              "type": "A",
              "name": "example.com",
              "content": "192.0.2.1",
              ...
            }
          ],
          "success": true,
          ...
        }
        ```
        Si no existen registros, `"result"` será un array vacío.

3.  **`PUT /zones/{zone_id}/dns_records/{record_id}`**
    *   **Propósito**: Actualizar un registro DNS existente (tipo `A`).
    *   **Payload (JSON)**: Contiene `type`, `name`, `content` (la nueva IP), `ttl`.
        ```json
        {
          "type": "A",
          "name": "example.com",
          "content": "198.51.100.5",
          "ttl": 120
        }
        ```
    *   **Respuesta Exitosa Esperada (JSON)**: Objeto con `"success": true` y `"result"` con el detalle del registro actualizado.

4.  **`POST /zones/{zone_id}/dns_records`**
    *   **Propósito**: Crear un nuevo registro DNS (tipo `A`).
    *   **Payload (JSON)**: Similar al de `PUT`.
    *   **Respuesta Exitosa Esperada (JSON)**: Objeto con `"success": true` y `"result"` con el detalle del registro creado.

**Manejo de Errores de la API de Cloudflare**:

-   La aplicación verifica la clave `"success"` en la respuesta JSON. Si es `false`, se considera un error.
-   Los detalles del error se extraen del array `"errors"` en la respuesta, que típicamente contiene objetos con `code` y `message`.
-   También se manejan excepciones de red (`requests.exceptions.RequestException`) y errores de decodificación JSON.

