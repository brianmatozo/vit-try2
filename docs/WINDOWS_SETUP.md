# Vitalcer — Guía de Instalación y Ejecución en Windows (Estilo XAMPP)

Esta guía explica cómo instalar y ejecutar el sistema **Vitalcer** en una computadora con **Windows 10 u 11** de forma autónoma, utilizando el **Panel de Control de Escritorio** (al estilo XAMPP / LAMP stack).

---

## 1. Arquitectura en Windows

El sistema funciona con **3 servicios coordinados** sin necesidad de Docker, WSL ni máquinas virtuales:

| Servicio | Puerto | Protocolo | Función |
| :--- | :--- | :--- | :--- |
| **PostgreSQL 18** | `5432` | TCP / PostgreSQL | Base de datos relacional con bloqueos atómicos (`SELECT FOR UPDATE`) para ventas concurrentes. |
| **FastAPI Backend** | `8000` | HTTP (`/api/v1`) | Motor de inventario por partida doble y endpoints de cobro POS. |
| **Caddy Web Server** | `5173` / `5174` | HTTP / **HTTPS** | Sirve el Admin (5173) y el POS Móvil (5174 con HTTPS y TLS interno automático para permisos de cámara). |

---

## 2. Instalación en 1 Clic (Asistente Automatizado)

1. Descargá o cloná el repositorio en tu PC con Windows (por ejemplo en `C:\vitalcer`).
2. Hacé **doble clic** en:
   ```cmd
   scripts\windows\install.bat
   ```
3. El asistente se encargará automáticamente de:
   - ✅ Instalar el gestor de paquetes de Python (`uv`).
   - ✅ Descargar el servidor web seguro `caddy.exe`.
   - ✅ Inicializar el cluster de base de datos PostgreSQL en `data\postgres\`.
   - ✅ Instalar las dependencias de Python y sincronizar el entorno.
   - ✅ Crear un **acceso directo en tu Escritorio**: **"Vitalcer Control Panel"**.

---

## 3. Uso del Panel de Control ("Vitalcer Control")

Hacé doble clic en el acceso directo del Escritorio o ejecutá:
```cmd
scripts\windows\run_control.bat
```

Se abrirá una ventana nativa de Windows con:
- **Semáforos de Estado**: Luces verdes (🟢 EN EJECUCIÓN) o rojas (🔴 DETENIDO) para cada servicio.
- **Botón `[▶️ Iniciar Todo]`**: Enciende PostgreSQL, FastAPI y Caddy en secuencia ordenada.
- **Botón `[⏹️ Detener Todo]`**: Apaga todos los procesos limpiamente y libera los puertos.
- **Acceso Directo al POS y Admin**:
  - `[Abrir POS (Caja)]`: Abre `https://localhost:5174` en tu navegador.
  - `[Abrir Admin]`: Abre `http://localhost:5173` para ver el catálogo y ventas de caja.
  - `[API Docs]`: Abre la documentación interactiva Swagger (`/docs`).
- **Consola de Registro en Vivo**: Muestra la salida de terminal y eventos en tiempo real.

---

## 4. Conectar Celulares de Mostrador (Lector de Cámara)

Para que los cajeros o empleados usen la cámara de sus teléfonos como lector de códigos de barra:

1. Asegurate de que la computadora y los celulares estén conectados a la **misma red Wi-Fi del local**.
2. En el Panel de Control, mirá el banner verde superior:
   ```
   • Lector de Cámara POS (Celulares en Wi-Fi): https://192.168.1.XX:5174
   ```
3. Abrí ese enlace en el navegador del celular (Chrome en Android o Safari en iOS).
4. Como Caddy genera un certificado TLS local seguro:
   - El navegador mostrará un aviso de advertencia ("La conexión no es privada").
   - Hacé clic en **"Configuración avanzada"** -> **"Continuar a 192.168.1.XX (no seguro)"**.
5. ¡Listo! El navegador tendrá permisos de cámara HTTPS (`getUserMedia`) y comenzará a escanear los códigos impresos por la balanza y productos empaquetados.

---

## 5. Múltiples Cajeros Simultáneos (Concurrencia)

- Cada celular tiene su **propio carrito independiente en memoria**.
- Las ventas se graban en PostgreSQL en **transacciones atómicas**:
  - Si dos cajeros cobran casi al mismo tiempo, PostgreSQL procesa una y luego la otra sin sobrescribir stock.
  - En el panel de **Ventas de Caja** (`/sales`), cada comprobante se agrupa automáticamente por su número de ticket independiente.

---

## 6. Solución de Problemas Frecuentes

### ¿El puerto 5432 ya está ocupado?
Si ya tenías PostgreSQL instalado previamente en Windows, el Panel de Control lo detectará automáticamente y utilizará ese servicio existente.

### ¿Cómo reiniciar la base de datos desde cero?
Simplemente detené los servicios desde el Panel de Control, borrá la carpeta `data\postgres\`, y volvé a ejecutar `install.bat`.

### ¿Cómo compilar cambios en el frontend?
Si modificás el código de las aplicaciones Svelte, podés recompilarlas ejecutando:
```cmd
scripts\windows\build.bat
```
