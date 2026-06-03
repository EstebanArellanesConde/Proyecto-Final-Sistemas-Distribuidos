#!/bin/bash
# Script de automatización para preparar y ejecutar el servidor Pong Arena

# 1. Definimos el nombre del directorio que contendrá el entorno virtual
VENV_DIR="venv"

# 2. Imprimimos un mensaje de inicio para retroalimentación visual en consola
echo "Iniciando proceso de despliegue para Pong Arena..."

# 3. Estructura condicional para verificar si el entorno virtual ya existe
if [ ! -d "$VENV_DIR" ]; then
    # Si el directorio no existe, notificamos al usuario
    echo "[+] Creando un nuevo entorno virtual ($VENV_DIR)..."
    # Instanciamos el entorno virtual limpio usando el módulo nativo de Python 3
    python3 -m venv $VENV_DIR
else
    # Si el directorio ya existe, omitimos la creación
    echo "[OK] El entorno virtual ya existe."
fi

# 4. Activamos el entorno virtual para garantizar que las dependencias se instalen de forma aislada
echo "[+] Activando entorno virtual..."
source $VENV_DIR/bin/activate

# 5. Instalamos y actualizamos las dependencias necesarias mediante pip
# Usamos el flag -q (quiet) para no saturar la consola si ya están instaladas
echo "[+] Verificando dependencias (FastAPI, Uvicorn, WebSockets, Jinja2)..."
pip install -q fastapi uvicorn websockets jinja2

# 6. Desplegamos instrucciones finales en la consola antes de bloquear el hilo con el servidor
echo ""
echo "======================================================="
echo "🚀 Servidor Autoritativo Listo"
echo "🌐 Escuchando en la red local (Host: 0.0.0.0, Port: 8000)"
echo "📱 Conecta tus clientes usando tu IP IPv4 (ej. 192.168.x.x:8000)"
echo "======================================================="
echo ""

# 7. Ejecutamos el servidor ASGI exponiéndolo a todas las interfaces de red para permitir conexiones LAN
uvicorn app:app --host 0.0.0.0 --port 8000