# Proyecto Final - Sistemas Distribuidos (Clave: 1959)
# 🏓 Pong Arena: Cliente-Servidor Multijugador

## 📖 Descripción del Proyecto

**Pong Arena** es una implementación multijugador en tiempo real del clásico juego de Ping Pong, diseñado para soportar hasta 4 jugadores simultáneos. Desarrollado como proyecto final para la asignatura de Sistemas Distribuidos en la Facultad de Ingeniería, este sistema demuestra la viabilidad de las comunicaciones de baja latencia mediante Sockets en redes locales.

El juego funciona bajo un modelo **Cliente-Servidor Autoritativo**, permitiendo que cualquier dispositivo (teléfonos móviles, tabletas, laptops) se conecte e interactúe a través de un navegador web estándar conectándose al host local.

## ✨ Características Principales

* **Multijugador en Tiempo Real (1v1 a 4-Player):** Sincronización de físicas y posiciones a 60 FPS.
* **Servidor Autoritativo:** La lógica pesada, las colisiones y el puntaje (`game_state.py`) se calculan centralizadamente en el servidor para evitar desincronización (*lag*) entre los clientes.
* **Gestión de Salas (Lobbies):** Soporte para múltiples partidas simultáneas e independientes mediante un sistema de gestión de salas (`rooms.py`).
* **Multiplataforma (Web-based):** Los clientes solo necesitan acceder a la IP del host desde su navegador (interfaz construida con HTML5 Canvas y JS). No requiere instalación.

## 🛠️ Stack Tecnológico

* **Backend / Host:** Python 3.x
* **Comunicación:** WebSockets (TCP) para mensajería bidireccional asíncrona.
* **Frontend / UI:** HTML5, CSS3, Vanilla JavaScript (`game.js`).

## ⚙️ Arquitectura de Red

El proyecto está diseñado para funcionar en una **Red de Área Local (LAN)** o mediante un **Mobile Hotspot** generado por el servidor host, evadiendo las restricciones de NAT o firewalls institucionales. 

1. El host levanta el servidor Python en un puerto específico.
2. Los dispositivos cliente se conectan a la misma red WiFi.
3. Los clientes acceden mediante el navegador a la dirección IPv4 local del host (ej. `http://192.168.1.XX:PORT`).

## 🚀 Instalación y Ejecución

### Prerrequisitos
* Python 3.8 o superior.
* Gestor de paquetes `pip`.

### Levantar el Servidor

1. Clona este repositorio:

```bash
   git clone [https://github.com/EstebanArellanesConde/Proyecto-Final-Sistemas-Distribuidos.git](https://github.com/EstebanArellanesConde/Proyecto-Final-Sistemas-Distribuidos.git)
   cd Proyecto-Final-Sistemas-Distribuidos/pong-arena
```

2. Recomendación: Crea y activa un entorno virtual

```bash 
python -m venv venv
   source venv/bin/activate  # En Linux/Mac
   # venv\Scripts\activate   # En Windows
```

3. Instala las dependencias necesarias:

```bash
pip install -r requirements.txt
```

4. Ejecuta la aplicación principal:

```bash
python server/app.py
```

# Conectar los Clientes

Asegúrate de que los dispositivos cliente estén en la misma red WiFi que el servidor.

Abre un navegador web en el cliente e ingresa la dirección IP del servidor.
Por ejemplo: http://localhost:8000


```bash
python -m venv venv
pip install fastapi uvicorn jinja2 websockets
uvicorn app:app --reload
```

# Estructura del Repositorio

```Plaintext
pong-arena/
├── client/
│   ├── join_client.py       # Script de prueba para simular clientes
│   └── test_client.py       # Herramienta de testeo de latencia/sockets
├── server/
│   ├── static/
│   │   └── game.js          # Lógica del cliente, renderizado del Canvas e inputs
│   ├── templates/
│   │   └── index.html       # Interfaz principal de usuario / Lobby
│   ├── app.py               # Entry point del servidor, rutas y conexión de sockets
│   ├── game_state.py        # Lógica de físicas, colisiones y estado autoritativo
│   └── rooms.py             # Estructura de datos para manejar múltiples partidas
└── README.md
```
