#!/bin/bash
# Script de Respaldo Automatizado para Servidores Dedicados
# Uso: ./backup.sh <nombre_del_contenedor> <ruta_interna_de_datos>

CONTAINER_NAME=$1
DATA_PATH=${2:-/data}
BACKUPS_DIR="$(pwd)/backups"

if [ -z "$CONTAINER_NAME" ]; then
    echo "Error: Debes proporcionar el nombre del contenedor."
    echo "Uso: $0 <nombre_del_contenedor> [ruta_interna_de_datos]"
    exit 1
fi

# Crear directorio de respaldos si no existe
mkdir -p "$BACKUPS_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILENAME="${CONTAINER_NAME}_${TIMESTAMP}.tar.gz"

echo "Iniciando respaldo del contenedor '$CONTAINER_NAME'..."

# Verificar si el contenedor existe
if ! docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}\$"; then
    echo "Error: El contenedor '$CONTAINER_NAME' no existe."
    exit 1
fi

# Utilizamos un contenedor temporal (alpine) que monta los volúmenes del contenedor objetivo
# y el directorio local de respaldos para realizar la compresión.
docker run --rm \
    --volumes-from "${CONTAINER_NAME}" \
    -v "${BACKUPS_DIR}:/backup" \
    alpine \
    tar czf "/backup/${BACKUP_FILENAME}" "${DATA_PATH}"

if [ $? -eq 0 ]; then
    echo "✅ Respaldo completado exitosamente: backups/${BACKUP_FILENAME}"
else
    echo "❌ Error al crear el respaldo."
    exit 1
fi
