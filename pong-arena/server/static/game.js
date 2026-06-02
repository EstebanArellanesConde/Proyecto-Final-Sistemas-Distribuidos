// Variable global para almacenar y manejar la conexión abierta con el servidor WebSocket
let ws = null;

// Obtenemos el contenedor Canvas y su contexto 2D para renderizado
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

// Referencias a los elementos del DOM en el Lobby
const playerList = document.getElementById("playerList");
const roomTitle = document.getElementById("roomTitle");

// Variables del lado del cliente para rastrear la posición física de la pelota
let ballX = 400;
let ballY = 400;

// Estructura de datos local para mantener en memoria las coordenadas de las paletas
let paddles = { "TOP": 350, "BOTTOM": 350, "LEFT": 350, "RIGHT": 350 };
// Almacenará localmente el modo de juego (2 o 4 jugadores)
let activePlayers = 0;

// --- MODIFICACIÓN FASE 2: DICCIONARIO UNIFICADO DE TECLAS ---
// Solo rastreamos el estado de las 4 direcciones estándar, sin importar si el origen fue WASD o Flechas
const keys = {
    ArrowUp: false,
    ArrowDown: false,
    ArrowLeft: false,
    ArrowRight: false
};

// --- NUEVA FUNCIÓN FASE 2 ---
// Función traductora que intercepta WASD y lo convierte al estándar de flechas que entiende el backend
function normalizeKey(key) {
    // Convertimos la tecla a minúscula para evitar problemas si el Bloq Mayús está activo
    const lowerKey = key.toLowerCase();
    
    // Mapeo lógico de teclas alfabéticas a flechas direccionales
    if (lowerKey === 'w') return 'ArrowUp';
    if (lowerKey === 's') return 'ArrowDown';
    if (lowerKey === 'a') return 'ArrowLeft';
    if (lowerKey === 'd') return 'ArrowRight';
    
    // Si la tecla ya era una flecha u otro control, la devolvemos intacta
    return key;
}

// Bucle nativo del navegador encargado de renderizar gráficos a 60 FPS
function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Dibujo de la pelota
    ctx.beginPath();
    ctx.arc(ballX, ballY, 10, 0, Math.PI * 2);
    ctx.fill();
    
    // Dibujo de las paletas (Cyan)
    ctx.fillStyle = "#00e5ff";
    
    // Solo si hay 4 jugadores activos renderizamos superior e inferior
    if (activePlayers === 4) {
        ctx.fillRect(paddles["TOP"], 10, 100, 10);
        ctx.fillRect(paddles["BOTTOM"], 780, 100, 10);
    }
    
    // Paletas laterales
    ctx.fillRect(10, paddles["LEFT"], 10, 100);
    ctx.fillRect(780, paddles["RIGHT"], 10, 100);

    requestAnimationFrame(draw);
}

draw();

// Funciones de inicialización de sala
function createRoom() {
    ws = new WebSocket("ws://" + location.host + "/host");
    setupSocket();
    document.getElementById("menu").style.display = "none";
    document.getElementById("lobby").style.display = "block";
}

function joinRoom() {
    const code = document.getElementById("roomCode").value;
    connectPlayer(code);
}

function connectPlayer(code) {
    ws = new WebSocket("ws://" + location.host + "/join/" + code);
    setupSocket();
    document.getElementById("menu").style.display = "none";
    document.getElementById("lobby").style.display = "block";
    roomTitle.innerText = "Sala: " + code;
}

// Enrutador de mensajes recibidos del servidor
function setupSocket() {
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === "room_created") {
            roomTitle.innerText = "Sala: " + data.code;
        }

        if (data.type === "room_status") {
            updateLobby(data.players);
        }

        if (data.type === "game_state") {
            ballX = data.ball_x;
            ballY = data.ball_y;
            paddles = data.paddles;
            activePlayers = data.active_players;
        }
        
        if (data.type === "game_start") {
            document.getElementById("lobby").style.display = "none";
            canvas.style.display = "block";
        }
    };
}

// Actualización de UI del lobby
function updateLobby(players) {
    playerList.innerHTML = "";
    players.forEach(player => {
        const li = document.createElement("li");
        li.innerText = player.position + " - " + (player.ready ? "READY" : "WAITING");
        playerList.appendChild(li);
    });
}

// Botón de listo
document.getElementById("readyButton").onclick = () => {
    if (!ws) return;
    ws.send(JSON.stringify({ type: "ready" }));
};

// --- MODIFICACIÓN FASE 2: CAPTURA DE TECLAS NORMALIZADA ---
document.addEventListener("keydown", (event) => {
    // Normalizamos la tecla (convierte WASD a ArrowX)
    const stdKey = normalizeKey(event.key);
    
    // Si la tecla normalizada existe en nuestro mapa de controles
    if (keys.hasOwnProperty(stdKey)) {
        event.preventDefault();
        
        // Verificamos si no estaba presionada previamente
        if (!keys[stdKey]) {
            keys[stdKey] = true;
            sendMovement(stdKey, true);
            
            // Retroalimentación visual: Añadimos la clase 'active' al span correspondiente en el UI
            const uiElement = document.getElementById("ui-" + stdKey);
            if(uiElement) uiElement.classList.add("active");
        }
    }
});

document.addEventListener("keyup", (event) => {
    // Normalizamos la tecla
    const stdKey = normalizeKey(event.key);
    
    if (keys.hasOwnProperty(stdKey)) {
        event.preventDefault();
        keys[stdKey] = false;
        sendMovement(stdKey, false);
        
        // Retroalimentación visual: Removemos la clase 'active' para que recupere su color original
        const uiElement = document.getElementById("ui-" + stdKey);
        if(uiElement) uiElement.classList.remove("active");
    }
});

// Transmisión de comandos al servidor
function sendMovement(key, isPressed) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const message = {
            type: "input",
            key: key, // Se envía siempre ArrowUp, ArrowDown, etc. Nunca WASD.
            pressed: isPressed
        };
        ws.send(JSON.stringify(message));
    }
}