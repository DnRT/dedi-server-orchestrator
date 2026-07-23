# Orquestador Ligero para Servidores Dedicados

Este proyecto es una herramienta para automatizar el despliegue, monitoreo y respaldo de servidores dedicados para juegos (Minecraft, Project Zomboid, etc.) usando Docker de forma nativa. Incluye una **Interfaz Web (Panel de Control)** muy estética y fácil de utilizar.

## Requisitos
- **Python 3.6+**
- **Docker** instalado y corriendo
- **Dependencias de Python:** `pip install -r requirements.txt`

## 🖥️ Panel Web (Recomendado)

El orquestador cuenta con una interfaz gráfica moderna (Dark Mode y Glassmorphism) desde la cual puedes gestionar todo.

1. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Inicia el servidor web:
   ```bash
   python app.py
   ```
3. Abre tu navegador en **http://localhost:5000**.
   - Haz clic en "+ Nuevo Servidor" para desplegar una instancia desde una plantilla.
   - Observa la telemetría (CPU/RAM) actualizándose sola cada pocos segundos.
   - Controla el ciclo de vida de los contenedores (Pausar, Iniciar, Eliminar) con retroalimentación instantánea y manejo de errores.

## ⚙️ Uso desde la Terminal (CLI)

También puedes usar la lógica base desde tu terminal invocando el script `orchestrator.py` si prefieres no usar el entorno gráfico. 

Ejemplo:
```bash
python orchestrator.py deploy survival-mc -t minecraft
python orchestrator.py stats survival-mc
```

## 💾 Sistema de Respaldos (Cronjob)

El script `backup.sh` permite comprimir los datos del servidor (partidas guardadas) de forma segura sin apagar el contenedor, montando un contenedor `alpine` efímero.

**Uso manual:**
```bash
bash backup.sh <nombre_del_servidor> /ruta/interna/datos
```

Para automatizarlo (ej. respaldo diario a las 3 AM), agrégalo a tu cron en Linux:
```bash
0 3 * * * cd /ruta/al/proyecto && ./backup.sh mi-server-mc /data >> /var/log/backup.log 2>&1
```

## 🎮 Añadir Nuevos Juegos
El orquestador lee las plantillas de configuración en formato JSON desde la carpeta `templates/`. Si añades nuevos archivos allí (ej. `terraria.json`), aparecerán automáticamente en el menú desplegable del Panel Web listos para ser desplegados con un clic.
