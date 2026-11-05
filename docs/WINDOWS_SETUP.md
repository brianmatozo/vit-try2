# Vitalcer — Guía de Instalación y Empaquetado para Windows

Esta guía explica cómo empaquetar, instalar y ejecutar el sistema **Vitalcer** en computadoras con **Windows 10 u 11** de forma autónoma mediante un **instalador único profesional para usuarios no técnicos** (`vitalcer-setup-x64.exe`), sin requerir Python, Node.js ni Docker en la máquina del cliente.

---

## 1. Arquitectura de Servicios en Windows

El sistema opera con **3 componentes coordinados en segundo plano** (sin ventanas de terminal ni consolas visibles):

| Servicio | Puerto | Protocolo | Función |
| :--- | :--- | :--- | :--- |
| **PostgreSQL 18** | `5432` | TCP / PostgreSQL | Base de datos relacional portable con bloqueos atómicos (`SELECT FOR UPDATE`). |
| **FastAPI Backend** | `8000` | HTTP (`/api/v1`) | Motor de inventario por partida doble y endpoints de cobro POS. |
| **Caddy Web Server** | `5173` / `5174` | **HTTPS** | Sirve el Admin (5173) y el POS Móvil (5174) con TLS interno automático para permisos de cámara W3C. |

---

## 2. Generación del Instalador Autónomo (Inno Setup)

Para compilar y empaquetar todo el sistema en un único archivo ejecutable autoinstalable:

1. **Requisitos de compilación** (en máquina de desarrollo o CI con Windows):
   - Inno Setup 6 (`winget install JRSoftware.InnoSetup`).
   - Herramientas del repositorio sincronizadas (`uv`, `pnpm`).

2. **Compilar el paquete**:
   ```cmd
   scripts\windows\package.bat
   ```
   El script ejecuta automáticamente el pipeline completo:
   - ✅ Descarga los binarios portables de Caddy y PostgreSQL 18 en `tools/`.
   - ✅ Compila y precomprime los frontends estáticos con Brotli nivel 11 (`apps/admin` y `apps/pos`).
   - ✅ Congela el backend FastAPI y el launcher headless mediante PyInstaller (`scripts/windows/vitalcer.spec`) sin librerías GUI (excluye Tkinter).
   - ✅ Compila el instalador autoejecutable Inno Setup con compresión sólida LZMA2 en `dist\vitalcer-setup-x64.exe`.

---

## 3. Experiencia de Instalación para el Usuario Final (Comercio)

El instalador está diseñado para que cualquier persona no técnica pueda configurar el sistema en 1 minuto:

1. El comerciante hace doble clic en `vitalcer-setup-x64.exe`.
2. El asistente de instalación en español guía el proceso:
   - Carpeta destino: `C:\Vitalcer` (por defecto).
   - Opciones pre-marcadas:
     - `[x]` Crear acceso directo a Vitalcer POS (Caja) en el Escritorio.
     - `[x]` Crear acceso directo a Vitalcer Admin en el Escritorio.
     - `[x]` Iniciar Vitalcer automáticamente en segundo plano al encender la computadora.
3. El instalador realiza de manera **silenciosa e invisible**:
   - Extracción de todos los binarios y archivos estáticos.
   - Inicialización del cluster PostgreSQL (`initdb.exe`).
   - Creación de la base de datos `vitalcer` (`createdb.exe`).
   - Registro en el inicio automático de Windows (`HKLM\...\Run`).
4. Al finalizar:
   - Casilla de verificación: `[x] Abrir Vitalcer POS ahora`.
   - Al pulsar "Finalizar", se inician los servicios en segundo plano y se abre automáticamente el navegador en `https://localhost:5174`.

---

## 4. Uso Diario en el Local Comercial

### Inicio y Trabajo Diario
- **Al encender la PC**: Los servicios (Postgres, Backend y Caddy) inician automáticamente en segundo plano sin mostrar ninguna ventana de consola negra ni paneles técnicos.
- **Acceso rápido**:
  - Doble clic en el icono **"Vitalcer POS"** del Escritorio: Abre directamente el mostrador de ventas en el navegador (`https://localhost:5174`).
  - Doble clic en el icono **"Vitalcer Admin"** del Escritorio: Abre el catálogo y reportes (`https://localhost:5173`).
- **Comportamiento idempotente**: Si los servicios ya están en marcha, el acceso directo abre el navegador al instante. Si estuvieran detenidos, los inicia en segundo plano antes de abrir la pantalla.

### Conectar Celulares de Mostrador (Lector de Balanza y Cámara)
Para que los cajeros o empleados utilicen sus teléfonos como lectores inalámbricos:
1. Conectar el celular a la **misma red Wi-Fi del local**.
2. Abrir en el navegador del teléfono: `https://<IP-DE-LA-PC>:5174` (por ejemplo `https://192.168.1.50:5174`).
3. Al ser un certificado TLS local seguro:
   - El navegador mostrará advertencia de privacidad.
   - Seleccionar **"Configuración avanzada"** -> **"Continuar (no seguro)"**.
4. ¡Listo! El navegador activará la cámara para escanear etiquetas GS1 de balanza y códigos EAN-13.

### Detener Servicios o Desinstalar

#### Detener Servicios
- Desde el menú Inicio: carpeta **Vitalcer** -> **"Detener Servicios Vitalcer"**.

#### Desinstalación Completa (Packaged Uninstaller)
El sistema incluye múltiples puntos de acceso para desinstalar de forma limpia:
1. **Configuración de Windows**: Ir a *Configuración > Aplicaciones > Aplicaciones Instaladas*, buscar **Vitalcer** y hacer clic en *Desinstalar*.
2. **Menú Inicio**: Carpeta *Vitalcer* -> **"Desinstalar Vitalcer"**.
3. **Carpeta de Instalación (`C:\Vitalcer`)**:
   - Acceso directo **"Desinstalar Vitalcer"**.
   - Script ejecutable **`Desinstalar.bat`**.

El desinstalador se encarga de:
- Detener ordenadamente PostgreSQL, FastAPI y Caddy.
- Forzar el cierre de procesos residuales para liberar bloqueos de archivos.
- Eliminar los accesos directos del Escritorio (**Vitalcer POS** y **Vitalcer Admin**).
- Limpiar el registro de inicio automático de Windows (`HKLM` / `HKCU`).
- Realizar un **borrado completo y limpio** de toda la carpeta `C:\Vitalcer` (incluyendo base de datos `data\postgres` y logs `data\logs`), dejando el equipo sin archivos huérfanos.

---

## 5. Instalación y Desinstalación Local para Desarrolladores

### Instalación desde el código fuente
Si trabajás directamente sobre el código fuente en Windows:
```cmd
scripts\windows\install.bat
```
Este script descarga las herramientas portables, sincroniza las dependencias con `uv sync` y crea el acceso directo en el Escritorio apuntando a `scripts\windows\launcher.py`.

### Desinstalación y Limpieza en Desarrollo
Para limpiar el entorno de desarrollo y remover los accesos directos creados:
```cmd
scripts\windows\uninstall.bat
```
El asistente detendrá los procesos locales, removerá los accesos directos del Escritorio y consultará si deseás eliminar la carpeta local `data/`.
