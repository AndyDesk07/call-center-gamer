# CallCenterGamer

**Asignatura:** Programación Back End  
**Evaluación:** Sumativa N.º 3 — Unidad 2  
**Tecnología principal:** Django con MySQL/MariaDB

## Descripción del proyecto

CallCenterGamer es una aplicación web de soporte técnico para usuarios de videojuegos. Permite registrar consultas o *tickets*, conversar mediante respuestas asociadas a cada ticket y gestionar la atención de las solicitudes.

El sistema diferencia los permisos de clientes, técnicos y administradores. También cuenta con herramientas para consultar tickets, organizarlos por categoría y estado, gestionar usuarios y visualizar estadísticas.

## Tecnologías utilizadas

- Python y Django para el funcionamiento del servidor.
- MySQL/MariaDB para almacenar usuarios, consultas y respuestas.
- Django ORM para acceder a la base de datos.
- Django Forms para validar los formularios.
- HTML, CSS, JavaScript y Bootstrap para la interfaz.
- Django Admin para administrar los modelos del sistema.
- Google Gemini para responder dudas técnicas en el asistente virtual.

## Perfiles de usuario

| Perfil | Funciones principales |
| --- | --- |
| Cliente | Registrarse, iniciar sesión, crear consultas, consultar sus tickets y participar en sus conversaciones. |
| Técnico | Ver consultas de soporte, buscar y filtrar tickets, responder mensajes y actualizar estados. |
| Administrador | Administrar usuarios y sus roles, gestionar consultas, acceder a estadísticas y utilizar Django Admin. |

Los permisos de acceso se verifican en las vistas del servidor, además de los controles visibles en las páginas.

## Aplicaciones Django

El proyecto se organiza principalmente en dos aplicaciones:

- **`online`**: contiene los modelos `Usuario`, `Preguntas` y `Respuesta`; además de formularios y vistas para registro, inicio de sesión, creación de consultas y conversaciones.
- **`administracion`**: contiene las vistas y plantillas para la gestión de usuarios, la administración de consultas, el escritorio técnico y las estadísticas.

Los modelos del proyecto se registran en `online/admin.py` para su administración desde `/admin/`.

## Mejoras implementadas respecto al proyecto base

### 1. Categorías para las consultas

Se incorporó el campo `categoria` al modelo `Preguntas`, con las opciones Hardware, Software, Redes y Otro. La categoría se selecciona desde el formulario, se guarda en la base de datos y puede utilizarse para filtrar tickets.

### 2. Estados de atención

Se incorporó el campo `estado` al modelo `Preguntas`. Cada ticket puede estar en estado Abierto, En proceso o Cerrada. El personal autorizado puede actualizar su estado desde el listado de consultas.

### 3. Herramientas de gestión de soporte

Se añadieron búsqueda y filtros de consultas, un escritorio para técnicos y un dashboard que muestra estadísticas calculadas a partir de los datos guardados en el sistema.

Como complemento, se habilitó Django Admin para los modelos `Usuario`, `Preguntas` y `Respuesta`, con opciones de búsqueda y filtrado.

Los cambios del modelo están reflejados en los archivos de `online/migrations/`.

## Requisitos para ejecutar el proyecto

- Python con `pip` disponible.
- MySQL o MariaDB en funcionamiento (por ejemplo, mediante XAMPP).
- Dependencias indicadas en `requirements.txt`.

## Instalación y ejecución en Windows con XAMPP

1. Descomprimir el proyecto y abrir en Visual Studio Code **la carpeta que contiene `manage.py`**.
2. Iniciar MySQL desde el panel de control de XAMPP.
3. Crear una base de datos vacía llamada `CallCenterGamer` mediante phpMyAdmin o una herramienta equivalente.
4. Abrir una terminal en la misma carpeta de `manage.py` e instalar las dependencias:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Revisar la configuración del proyecto:

   ```powershell
   python manage.py check
   ```

6. Crear las tablas mediante las migraciones existentes:

   ```powershell
   python manage.py migrate
   ```

7. Crear una cuenta administradora:

   ```powershell
   python manage.py createsuperuser
   ```

8. Iniciar el servidor de desarrollo:

   ```powershell
   python manage.py runserver
   ```

9. Abrir `http://127.0.0.1:8000/` en el navegador. Django Admin se encuentra en `http://127.0.0.1:8000/admin/`.

> **Nota:** No se inicia el servidor pulsando solamente «Ejecutar archivo Python» sobre `manage.py`; hay que utilizar el comando `python manage.py runserver`.

### Configuración de la base de datos

La conexión está definida en `CallCenterGamer/settings.py` y utiliza estas variables de entorno cuando se necesitan valores distintos de los predeterminados:

| Variable | Valor predeterminado en desarrollo |
| --- | --- |
| `DB_NAME` | `CallCenterGamer` |
| `DB_USER` | `root` |
| `DB_PASSWORD` | Vacío |
| `DB_HOST` | `localhost` |
| `DB_PORT` | `3306` |

Si la instalación local de MySQL tiene otras credenciales, se deben configurar las variables correspondientes antes de iniciar el proyecto. No se deben incluir contraseñas personales en el código ni en el archivo comprimido de entrega.

## Pruebas

Para ejecutar las pruebas automatizadas:

```powershell
python manage.py test
```

También se pueden revisar los modelos y las migraciones con:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
```

El proyecto incluye pruebas para accesos según rol, conversaciones, operaciones administrativas, categorías, estados de tickets, validación del RUT y Django Admin.

**Importante:** en MySQL, las pruebas automatizadas requieren que el usuario de la base de datos tenga permiso para crear una base de pruebas temporal.

## Asistente virtual con Gemini

El chat de la página de inicio permite escribir dudas sobre videojuegos, computadores y conexiones. El sistema envía a Google Gemini **únicamente el mensaje escrito en ese chat**, sin incorporar tickets almacenados ni información de otros usuarios. Si no se puede resolver la duda, se recomienda crear un ticket para que un técnico la atienda.

Para utilizarlo:

1. Generar una clave de API en [Google AI Studio](https://aistudio.google.com/apikey). La disponibilidad del nivel gratuito depende de los límites y condiciones actuales de Google.
2. En la terminal de PowerShell de Visual Studio Code, configurar la clave antes de iniciar el servidor:

   ```powershell
   $env:GEMINI_API_KEY="TU_CLAVE_DE_GOOGLE"
   python manage.py runserver
   ```

3. Iniciar sesión como usuario, abrir el ícono del robot en el inicio y enviar una pregunta.

La clave se configura **solo en el servidor**, nunca dentro del HTML o JavaScript ni en los archivos de entrega. La variable está declarada en `CallCenterGamer/settings.py`. La configuración de PowerShell se mantiene durante esa sesión de terminal; si se abre otra, hay que establecerla nuevamente.

**Privacidad:** los textos que se escriben en el chat se procesan en los servidores de Google. Se recomienda no enviar contraseñas, datos personales ni información confidencial. Las consultas del chat no se guardan en la base de datos del proyecto.

El chat con Gemini es un complemento de la aplicación; no sustituye los tickets ni la atención de técnicos. Las tres mejoras principales de la evaluación siguen siendo categorías, estados y herramientas de gestión de soporte.

## Documentación de la evaluación

Este README describe el proyecto y su ejecución. La entrega académica también debe incluir, según la pauta de la asignatura, las respuestas de análisis e investigación, los diagramas solicitados, la explicación de las mejoras y las evidencias de funcionamiento. El trabajo manuscrito de `settings.py` corresponde a cada integrante.
