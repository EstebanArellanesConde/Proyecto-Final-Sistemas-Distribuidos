// Variable global y nula que albergará la instancia activa del WebSocket de la sesión
let ws = null;
// Obtenemos la referencia fija del DOM hacia el lienzo principal
const canvas = document.getElementById("gameCanvas");
// Extraemos el API de renderizado bidimensional del navegador
const ctx = canvas.getContext("2d");

// Inicializamos en memoria cliente las variables espaciales de la pelota
let ballX = 400, ballY = 400;
// Inicializamos el diccionario de posiciones de las paletas
let paddles = { "TOP": 350, "BOTTOM": 350, "LEFT": 350, "RIGHT": 350 };
// Variable para sincronizar el formato de renderizado con el de las reglas del backend (2 o 4)
let activePlayers = 0;
// Estructura local que almacenará el puntaje reportado en cada iteración del servidor
let scores = { "TOP": 0, "BOTTOM": 0, "LEFT": 0, "RIGHT": 0 };
// Guardamos la meta de victoria (por default 10) para cálculos de interfaz
let targetScore = 10;
// Variable para identificar localmente la posición del cliente en curso
let myPosition = ""; 

// Objeto constante de solo lectura que emula el mapeo hexadecimal del backend para la pintura
const COLORS = {
    "LEFT": "#ff0000",   
    "RIGHT": "#000080",  
    "TOP": "#ffff00",    
    "BOTTOM": "#008000"  
};

// Objeto literal que funciona como diccionario de traducciones de posición a texto de UI
const POS_NAMES = {
    "LEFT": "Jugador 1 (Izq)",
    "RIGHT": "Jugador 2 (Der)",
    "TOP": "Jugador 3 (Arr)",
    "BOTTOM": "Jugador 4 (Aba)"
};

// Variable booleana local para evitar despachos duplicados por mantener la tecla hundida
const keys = { ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false };

// Función middleware que convierte teclas físicas a nombres abstractos usables por el backend
function normalizeKey(key) {
    // Aplicamos conversión a minúsculas por si Caps Lock está activo en el hardware
    const lowerKey = key.toLowerCase();
    // Conversiones directas de sistema WASD a sistema de Flechas Direccionales
    if (lowerKey === 'w') return 'ArrowUp';
    if (lowerKey === 's') return 'ArrowDown';
    if (lowerKey === 'a') return 'ArrowLeft';
    if (lowerKey === 'd') return 'ArrowRight';
    // Si la tecla no es alfabética, retorna su propio valor de evento
    return key;
}

// Bucle recursivo disparado por requestAnimationFrame a la frecuencia máxima del monitor
function draw() {
    // Limpieza agresiva de todo el lienzo en las coordenadas absolutas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Activamos la ruta de trazado para figuras primitivas
    ctx.beginPath();
    // Definimos el color de la brocha a blanco puro para la pelota
    ctx.fillStyle = "#ffffff";
    // Trazamos una curva de 360 grados (círculo) utilizando las coordenadas de red y radio 10
    ctx.arc(ballX, ballY, 10, 0, Math.PI * 2);
    // Rellenamos el trazado con el color activo
    ctx.fill();
    
    // Cambiamos el color de la brocha al asociado a la paleta izquierda
    ctx.fillStyle = COLORS["LEFT"];
    // Dibujamos el rectángulo de colisión: (X=10, Y=ValorRed, Ancho=10, Alto=100)
    ctx.fillRect(10, paddles["LEFT"], 10, 100);
    
    // Cambiamos el color al asociado a la paleta derecha
    ctx.fillStyle = COLORS["RIGHT"];
    // Dibujamos el rectángulo de colisión derecho (X fijo en 780)
    ctx.fillRect(780, paddles["RIGHT"], 10, 100);

    // Condición de renderizado: si la variable sincronizada indica 4 jugadores activos
    if (activePlayers === 4) {
        // Pintamos el relleno con color amarillo para el superior
        ctx.fillStyle = COLORS["TOP"];
        // Trazado horizontal: (X=ValorRed, Y=10, Ancho=100, Alto=10)
        ctx.fillRect(paddles["TOP"], 10, 100, 10);
        
        // Pintamos el relleno con color verde para el inferior
        ctx.fillStyle = COLORS["BOTTOM"];
        // Trazado horizontal inferior (Y fijo en 780)
        ctx.fillRect(paddles["BOTTOM"], 780, 100, 10);
    }

    // Delegamos la siguiente ejecución del draw al ciclo interno del navegador web
    requestAnimationFrame(draw);
}

// Invocación inicial obligatoria para arrancar la máquina de estados de gráficos
draw(); 

// Rutina asíncrona iniciada al presionar el botón de host
function createRoom() {
    // Recuperamos el valor numérico del select de capacidad de jugadores en el DOM
    const maxPlayers = document.getElementById("playerCount").value;
    // Recuperamos el valor numérico del select de límite de puntos
    const scoreLimit = document.getElementById("targetScore").value;
    
    // Construimos dinámicamente la URL interpolando los datos como Query Parameters
    const wsUrl = `ws://${location.host}/host?max_players=${maxPlayers}&target_score=${scoreLimit}`;
    // Instanciamos el objeto WebSocket nativo forzando el handshake TCP hacia FastAPI
    ws = new WebSocket(wsUrl);
    
    // Enlazamos todos los manejadores de eventos y escuchadores al objeto recién creado
    setupSocket();
    
    // Ejecutamos la transición visual hacia la sala de espera apuntando a los nuevos IDs
    switchScreen("menuScreen", "lobbyScreen");
}

// Rutina asíncrona iniciada al ingresar el código
function joinRoom() {
    // Capturamos el input de texto y forzamos mayúsculas para evitar desajustes case-sensitive
    const code = document.getElementById("roomCode").value.toUpperCase();
    // Abortamos si el campo está vacío
    if (!code) return;
    // Instanciamos el socket apuntando a la ruta paramétrica
    ws = new WebSocket(`ws://${location.host}/join/${code}`);
    // Enlazamos eventos y rutinas
    setupSocket();
    
    // Cambiamos la vista apuntando a los nuevos contenedores responsivos
    switchScreen("menuScreen", "lobbyScreen");
}

// Función maestra para gestionar la visualización de las pantallas usando clases CSS
function switchScreen(hideId, showId) {
    // Retiramos la clase 'active' de la pantalla actual para ocultarla del flujo del DOM
    document.getElementById(hideId).classList.remove("active");
    // Añadimos la clase 'active' a la pantalla objetivo para aplicarle el display responsivo
    document.getElementById(showId).classList.add("active");
}

// Función colosal encargada de registrar los manejadores del objeto ws e interpretar el tráfico
function setupSocket() {
    // Sobrescribimos el evento onmessage con una función flecha para retener el contexto local
    ws.onmessage = (event) => {
        // Deserializamos obligatoriamente la carga útil de texto a JSON Javascript
        const data = JSON.parse(event.data);

        // Si el paquete es de confirmación de ingreso
        if (data.type === "room_created" || data.type === "joined") {
            // Guardamos localmente el rol otorgado por la máquina de estados central (ej. RIGHT)
            myPosition = data.position;
            // Extraemos con fallback el código de acceso
            const code = data.code || data.room;
            // Escribimos el código grande en la cabecera del lobby
            document.getElementById("roomTitle").innerText = "Sala: " + code;
            
            // Revelamos al usuario qué jugador y color le tocó directamente en el Lobby
            const roleEl = document.getElementById("myRoleText");
            if (roleEl) {
                // Inyectamos HTML para colorear el nombre del rol usando el diccionario
                roleEl.innerHTML = `Tú eres: <span style="color: ${COLORS[myPosition]}">${POS_NAMES[myPosition]}</span>`;
            }
        }

        // Si el paquete es un fotograma de sincronización de lobby
        if (data.type === "room_status") {
            // Actualizamos la meta de puntos sincronizándola con el Host
            targetScore = data.target_score;
            // Actualizamos el subtítulo de la sala reportando fracciones (ej: Jugadores 2/4)
            document.getElementById("roomConfigText").innerText = 
                `Objetivo: ${targetScore} Puntos | Jugadores: ${data.players}/${data.max_players}`;
            // Delegamos la repintada de la lista a una sub-función
            updateLobby(data.players_list);
        }

        // Si el paquete notifica que las condiciones de inicio se han cumplido
        if (data.type === "game_start") {
            // Ejecutamos la transición directa e instantánea del Lobby a la Interfaz de Juego
            switchScreen("lobbyScreen", "gameScreen");
        }

        // Si el paquete es un fotograma numérico emitido a 60 hz
        if (data.type === "game_state") {
            // Reasignamos coordenadas vectoriales a las variables gráficas
            ballX = data.ball_x; ballY = data.ball_y;
            // Reemplazamos el diccionario local de posiciones rectangulares
            paddles = data.paddles;
            // Ajustamos las reglas de pintura por modo
            activePlayers = data.active_players;
            // Actualizamos la información aritmética de las metas
            scores = data.scores;
            
            // Interceptamos la bandera de interrupción de juego (alguien llegó a la meta)
            if (data.game_over) {
                // Ejecutamos la transición hacia la última pantalla de victoria
                switchScreen("gameScreen", "gameOverScreen");
                
                // Generamos un string celebrando al ganador usando su color en texto
                document.getElementById("winnerText").innerText = `🏆 ¡EL ${POS_NAMES[data.winner].toUpperCase()} HA GANADO! 🏆`;
                // Ajustamos el color del anuncio de victoria para que coincida con el triunfador
                document.getElementById("winnerText").style.color = COLORS[data.winner];
                
                // Ejecutamos un cierre agresivo del canal de red TCP para prevenir fugas
                ws.close();
                // Abortamos la lectura del resto de la función para este fotograma
                return;
            }

            // Invocamos el constructor de DOM para repintar la barra horizontal de puntajes
            updateHUD();
        }
    };
}

// Rutina renderizadora que destruye y reconstruye el HUD de estadísticas en la barra superior
function updateHUD() {
    // Capturamos el bloque ancla HTML
    const scoreBoard = document.getElementById("scoreBoard");
    // Destruimos brutalmente los nodos hijos previos manipulando el string HTML interno
    scoreBoard.innerHTML = ""; 
    
    // Inicializamos una variable negativa para buscar el valor más alto en el diccionario
    let maxScore = -1;
    // Variable null para retener el string identificador del jugador dominante
    let leader = null;

    // Iteramos rígidamente sobre el vector de las 4 posiciones absolutas posibles
    ["LEFT", "RIGHT", "TOP", "BOTTOM"].forEach(pos => {
        // En escenarios 2P (Modo Clásico), omitimos las lecturas fantasmas del techo y suelo
        if (activePlayers === 2 && (pos === "TOP" || pos === "BOTTOM")) return;
        
        // Asignamos a constante para evitar re-lecturas en el diccionario principal
        const currentScore = scores[pos];
        
        // Bloque lógico de detección de máximo absoluto: si el evaluado supera al rey
        if (currentScore > maxScore) {
            // Actualizamos la métrica máxima
            maxScore = currentScore;
            // Actualizamos el identificador del líder
            leader = pos;
        }

        // Instanciamos en memoria un nuevo nodo de bloque (div) para un chip de puntaje
        const div = document.createElement("div");
        // Le inyectamos la clase pre-diseñada en CSS para el diseño compacto horizontal
        div.className = "score-item";
        // Estilizamos directamente su atributo style para que la letra tenga el color asociado al jugador
        div.style.color = COLORS[pos];
        // Inyectamos marcado HTML con un tamaño de fuente equilibrado (22px) para no desbordar el alto
        div.innerHTML = `<span>${POS_NAMES[pos]}</span> <span style="font-size: 22px;">${currentScore}</span>`;
        // Adjuntamos el nodo al contenedor horizontal
        scoreBoard.appendChild(div);
    });

    // Sub-rutina para el cálculo matemático de distancia hasta la victoria
    const remaining = targetScore - maxScore;
    // Capturamos la etiqueta de subtítulo
    const subtitle = document.getElementById("gameSubtitle");
    
    // Si nadie ha anotado aún y el valor máximo sigue siendo cero
    if (maxScore === 0) {
        // Mostramos un mensaje de calentamiento estándar neutral
        subtitle.innerText = `¡La partida ha comenzado! Límite: ${targetScore} pts.`;
        subtitle.style.color = "#fbbf24";
    // Si ya existen anotaciones en curso
    } else {
        // Interrumpimos con el anuncio oficial de liderazgo, marcando la distancia al objetivo
        subtitle.innerText = `¡${POS_NAMES[leader]} va a la delantera! (A ${remaining} puntos de ganar)`;
        // Coloreamos el aviso con la paleta del líder para mayor presión psicológica
        subtitle.style.color = COLORS[leader];
    }
}

// Función encargada de mantener viva la lista visible del lobby
function updateLobby(playersList) {
    // Capturamos el elemento tipo Unordered List
    const ul = document.getElementById("playerList");
    // Destruimos sus elementos de lista para no apilarlos iteración sobre iteración
    ul.innerHTML = "";
    // Evaluamos el arreglo mapeado proveniente del backend
    playersList.forEach(p => {
        // Inicializamos elemento ListItem
        const li = document.createElement("li");
        // Aplicamos el color directo al texto usando el string hexadecimal dictado en la respuesta JSON
        li.style.color = p.color; 
        // Generamos el texto evaluando el booleano 'ready' en línea
        li.innerText = `${POS_NAMES[p.position]} - ${p.ready ? "LISTO ✔️" : "ESPERANDO..."}`;
        // Enganchamos el nodo al árbol
        ul.appendChild(li);
    });
}

// Registro de manejador del click en el botón listador del cliente
document.getElementById("readyButton").onclick = () => {
    // Si el socket murió, ignoramos para no tirar error
    if (!ws) return;
    // Transmitimos el cambio de estado serializando el objeto en línea
    ws.send(JSON.stringify({ type: "ready" }));
    // Desactivamos el botón en el DOM para bloquear doble-clicks
    document.getElementById("readyButton").disabled = true;
    // Modificamos el texto para transmitir un estatus de espera a nivel usuario
    document.getElementById("readyButton").innerText = "ESPERANDO A LOS DEMÁS...";
    // Atenuamos visualmente el botón modificando su color de fondo a un gris oscuro
    document.getElementById("readyButton").style.background = "#4b5563"; 
};

// Listener global acoplado al documento para interceptar el hundimiento de teclas
document.addEventListener("keydown", (event) => {
    // Pasamos el input físico por la capa de normalización para homologar nomenclaturas
    const stdKey = normalizeKey(event.key);
    // Evaluamos estrictamente si la llave pertenece a nuestro ecosistema aceptado
    if (keys.hasOwnProperty(stdKey)) {
        // Bloqueamos el scroll o funciones alternativas asignadas por el navegador web
        event.preventDefault();
        // Si el estado en memoria no había registrado esta presión...
        if (!keys[stdKey]) {
            // Actualizamos la memoria
            keys[stdKey] = true;
            // Emitimos la petición del estado a los servidores
            sendMovement(stdKey, true);
            // Capturamos la caja gráfica asociada del tutorial del lobby
            const ui = document.getElementById("ui-" + stdKey);
            // Agregamos la clase de manipulación CSS para prender su color
            if(ui) ui.classList.add("active");
        }
    }
});

// Listener global inverso que monitorea el des-enganche físico del botón
document.addEventListener("keyup", (event) => {
    // Repetimos rutinas normalizadoras
    const stdKey = normalizeKey(event.key);
    // Verificamos propiedad de control
    if (keys.hasOwnProperty(stdKey)) {
        // Aseguramos fluidez cancelando default actions
        event.preventDefault();
        // Sincronizamos liberando bandera local
        keys[stdKey] = false;
        // Lanzamos orden de frenado al backend
        sendMovement(stdKey, false);
        // Despintamos la interfaz retirando la clase que da luz cyan a la caja
        const ui = document.getElementById("ui-" + stdKey);
        if(ui) ui.classList.remove("active");
    }
});

// Función despachadora del protocolo personalizado del cliente hacia la red
function sendMovement(key, isPressed) {
    // Estricta regla de envío: El objeto debe existir, y el protocolo TCP debe estar OPEN (1)
    if (ws && ws.readyState === WebSocket.OPEN) {
        // Emitimos la conversión literal serializada enviando el tipo, identificador de tecla y su booleano asociado
        ws.send(JSON.stringify({ type: "input", key: key, pressed: isPressed }));
    }
}