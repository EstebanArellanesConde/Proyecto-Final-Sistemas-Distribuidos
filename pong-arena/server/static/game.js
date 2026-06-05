// Variable global y nula que albergará la instancia activa del WebSocket de la sesión
let ws = null;
// Obtenemos la referencia fija del DOM hacia el lienzo principal (Ahora mide 400x800)
const canvas = document.getElementById("gameCanvas");
// Extraemos el API de renderizado bidimensional del navegador
const ctx = canvas.getContext("2d");

// Inicializamos en memoria cliente las variables espaciales de la pelota (coordenadas absolutas)
let ballX = 400, ballY = 400;
// Inicializamos el diccionario de posiciones unidimensionales absolutas de las paletas
let paddles = { "TOP": 350, "BOTTOM": 350, "LEFT": 350, "RIGHT": 350 };
// Variable para sincronizar el formato de renderizado con el de las reglas del backend (2 o 4)
let activePlayers = 0;
// Estructura local que almacenará el puntaje reportado en cada iteración del servidor
let scores = { "TOP": 0, "BOTTOM": 0, "LEFT": 0, "RIGHT": 0 };
// Guardamos la meta de victoria (por default 10) para cálculos de interfaz
let targetScore = 10;
// Variable para identificar localmente la posición asignada a este cliente (Ej: "LEFT" o "RIGHT")
let myPosition = ""; 

// Objeto constante de solo lectura que emula el mapeo hexadecimal del backend para la pintura
const COLORS = {
    "LEFT": "#ff0000",   // Rojo (Jugador 1/Host)
    "RIGHT": "#000080",  // Azul marino (Jugador 2/Cliente)
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

/**
 * DECLARACIÓN: Función middleware que homologa layouts físicos a abstractos aceptados por el backend.
 * @param {string} key - Tecla cruda proveniente del evento del teclado.
 * @returns {string} - Tecla normalizada (Arrow sistema).
 */
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

/**
 * DECLARACIÓN: Bucle recursivo de renderizado (Gráficos 2D) que dibuja el Viewport a 60 FPS.
 * Implementa la lógica de Pantalla Dividida (Cámara Desplazada).
 */
function draw() {
    // 1. Limpieza de pantalla: Borramos todo el contenido del lienzo de 400x800
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 2. Guardamos el estado original del sistema de coordenadas (Cámara limpia en X=0, Y=0)
    ctx.save();

    // 3. --- LÓGICA DE VIEWPORT (CÁMARA DE PANTALLA DIVIDIDA) ---
    // Si somos el cliente asignado a la mitad DERECHA de la cancha absoluta...
    if (myPosition === "RIGHT") {
        // ...Empujamos el universo de dibujo 400 píxeles a la izquierda.
        // Esto causa que la coordenada absoluta 400 (centro) del servidor se renderice en X=0 (borde local)
        // y la coordenada absoluta 800 (borde) se renderice en X=400 (borde local).
        ctx.translate(-400, 0);
    } 
    // Nota: Si myPosition === "LEFT" (el host), el desplazamiento es nulo, así que dibuja el mundo normal.

    // 4. Dibujo de la Pelota usando las coordenadas ABSOLUTAS enviadas por el servidor
    ctx.beginPath();
    // Definimos el color de la brocha a blanco puro para la pelota
    ctx.fillStyle = "#ffffff";
    // Trazamos una curva de 360 grados (círculo) utilizando las coordenadas crudas de red (translate ajustará visualmente)
    ctx.arc(ballX, ballY, 10, 0, Math.PI * 2);
    // Rellenamos el trazado con el color activo
    ctx.fill();
    
    // 5. Cambiamos el color de la brocha al asociado a la paleta izquierda
    ctx.fillStyle = COLORS["LEFT"];
    // Dibujamos el rectángulo de colisión izquierdo en X absoluto 10
    ctx.fillRect(10, paddles["LEFT"], 10, 100);
    
    // 6. Cambiamos el color al asociado a la paleta derecha
    ctx.fillStyle = COLORS["RIGHT"];
    // Dibujamos el rectángulo de colisión derecho en X absoluto 780
    ctx.fillRect(780, paddles["RIGHT"], 10, 100);

    // Condición de renderizado: si la variable sincronizada indica partida de 4 jugadores
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

    // 7. Restauramos la cámara: Regresamos el origen del lienzo a X=0, Y=0 para el próximo ciclo
    ctx.restore();

    // Delegamos la siguiente ejecución del draw al ciclo interno del navegador web
    requestAnimationFrame(draw);
}

// Invocación inicial obligatoria para arrancar la máquina de estados de gráficos
draw(); 

// --- FLUJO DE MENÚS Y COMUNICACIÓN DE RED (WS) ---

/**
 * DECLARACIÓN: Rutina asíncrona iniciada al presionar "Crear Sala". Hostea e inicia el socket.
 */
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

/**
 * DECLARACIÓN: Rutina asíncrona iniciada al presionar "Unirse". Se conecta vía código.
 */
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

/**
 * DECLARACIÓN: Función middleware utilitaria para conmutar las vistas manipulando las clases active de CSS.
 * @param {string} hideId - ID del contenedor a ocultar.
 * @param {string} showId - ID del contenedor a mostrar.
 */
function switchScreen(hideId, showId) {
    // Retiramos la clase 'active' de la pantalla actual para ocultarla
    document.getElementById(hideId).classList.remove("active");
    // Añadimos la clase 'active' a la pantalla objetivo para aplicarle el display responsivo
    document.getElementById(showId).classList.add("active");
}

/**
 * DECLARACIÓN: Función colosal encargada de registrar los manejadores del objeto ws e interpretar el tráfico TCP entrante.
 */
function setupSocket() {
    // Sobrescribimos el evento onmessage para interceptar los fotogramas del servidor
    ws.onmessage = (event) => {
        // Deserializamos obligatoriamente la carga útil de texto crudo a objeto Javascript
        const data = JSON.parse(event.data);

        // Si el paquete es la confirmación oficial de ingreso/creación de sala
        if (data.type === "room_created" || data.type === "joined") {
            // Guardamos localmente el rol otorgado por la máquina de estados central (ej. LEFT o RIGHT)
            myPosition = data.position;
            // Extraemos con fallback el código de acceso
            const code = data.code || data.room;
            // Escribimos el código grande en la cabecera del lobby
            document.getElementById("roomTitle").innerText = "Sala: " + code;
            
            // Revelamos al usuario qué jugador y color le tocó directamente en el Lobby
            const roleEl = document.getElementById("myRoleText");
            if (roleEl) {
                // Inyectamos HTML para colorear el nombre del rol usando el diccionario COLORS
                roleEl.innerHTML = `Tú eres: <span style="color: ${COLORS[myPosition]}">${POS_NAMES[myPosition]}</span>`;
            }
        }

        // Si el paquete es un fotograma de sincronización de lobby (alguien entró o cambió estado "Listo")
        if (data.type === "room_status") {
            // Actualizamos la meta de puntos sincronizándola con la decisión del Host
            targetScore = data.target_score;
            // Actualizamos el subtítulo de la sala reportando fracciones (ej: Jugadores 2/2)
            document.getElementById("roomConfigText").innerText = 
                `Objetivo: ${targetScore} Puntos | Jugadores: ${data.players}/${data.max_players}`;
            // Delegamos la repintada de la lista a una sub-función
            updateLobby(data.players_list);
        }

        // Si el paquete notifica que todos están listos y comienza el juego
        if (data.type === "game_start") {
            // Ejecutamos la transición visual instantánea del Lobby a la Interfaz de Juego (Fase 3)
            switchScreen("lobbyScreen", "gameScreen");
        }

        // Si el paquete es un fotograma matemático crudo emitido a 60 hz
        if (data.type === "game_state") {
            // Reasignamos coordenadas vectoriales absolutas a las variables gráficas locales
            ballX = data.ball_x; ballY = data.ball_y;
            // Reemplazamos el diccionario local de posiciones rectangulares absolutas
            paddles = data.paddles;
            // Ajustamos las reglas de pintura por modo (2P/4P)
            activePlayers = data.active_players;
            // Actualizamos la información aritmética de los marcadores
            scores = data.scores;
            
            // Interceptamos la bandera de interrupción de juego (un jugador llegó a la meta)
            if (data.game_over) {
                // Ejecutamos la transición hacia la pantalla final de victoria (Fase 4)
                switchScreen("gameScreen", "gameOverScreen");
                
                // Generamos un string celebrando al ganador usando su color en texto
                document.getElementById("winnerText").innerText = `🏆 ¡EL ${POS_NAMES[data.winner].toUpperCase()} HA GANADO! 🏆`;
                // Ajustamos el color del anuncio de victoria para que coincida con el triunfador
                document.getElementById("winnerText").style.color = COLORS[data.winner];
                
                // Ejecutamos un cierre agresivo del canal de red TCP para prevenir fugas de memoria
                ws.close();
                // Abortamos la lectura del resto de la función para este fotograma
                return;
            }

            // Invocamos el constructor de DOM para repintar la barra lateral de puntajes
            updateHUD();
        }
    };
}

/**
 * DECLARACIÓN: Rutina renderizadora que destruye y reconstruye el HUD compacto superior (Marcador).
 */
function updateHUD() {
    // Capturamos el bloque ancla HTML
    const scoreBoard = document.getElementById("scoreBoard");
    // Destruimos brutalmente los nodos hijos previos manipulando el string HTML interno
    scoreBoard.innerHTML = ""; 
    
    // Inicializamos búsqueda de máximo absoluto para determinar el líder
    let maxScore = -1;
    let leader = null;

    // Iteramos rígidamente sobre el vector de las 4 posiciones absolutas posibles
    ["LEFT", "RIGHT", "TOP", "BOTTOM"].forEach(pos => {
        // En escenarios 2P (Modo Dividido), omitimos las lecturas fantasmas del techo y suelo
        if (activePlayers === 2 && (pos === "TOP" || pos === "BOTTOM")) return;
        
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
        // Le inyectamos la clase pre-diseñada en CSS (score-item horizontal)
        div.className = "score-item";
        // Estilizamos directamente su atributo style para que la letra tenga el color asociado al jugador
        div.style.color = COLORS[pos];
        // Inyectamos marcado HTML concatenando el nombre legible y su puntaje crudo
        div.innerHTML = `<span>${POS_NAMES[pos]}</span> <span style="font-size: 22px;">${currentScore}</span>`;
        // Adjuntamos el nodo al contenedor horizontal
        scoreBoard.appendChild(div);
    });

    // Sub-rutina matemática: cálculo matemático de distancia hasta la meta
    const remaining = targetScore - maxScore;
    const subtitle = document.getElementById("gameSubtitle");
    
    // Si nadie ha anotado aún y el valor máximo sigue siendo cero
    if (maxScore === 0) {
        // Mostramos un mensaje neutral de bienvenida
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

/**
 * DECLARACIÓN: Función encargada de reconstruir la lista de jugadores visibles en el Lobby.
 * @param {Array} playersList - Arreglo de objetos Player proveniente de FastAPI.
 */
function updateLobby(playersList) {
    // Capturamos el elemento tipo Unordered List
    const ul = document.getElementById("playerList");
    // Destruimos sus elementos de lista previos
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
    // Transmitimos el cambio de estado serializando el objeto JSON en línea
    ws.send(JSON.stringify({ type: "ready" }));
    // Desactivamos el botón en el DOM para bloquear doble-clicks
    document.getElementById("readyButton").disabled = true;
    // Modificamos el texto para transmitir un estatus de espera a nivel usuario
    document.getElementById("readyButton").innerText = "ESPERANDO A LOS DEMÁS...";
    // Atenuamos visualmente el botón modificando su color de fondo a un gris oscuro
    document.getElementById("readyButton").style.background = "#4b5563"; 
};

// --- CAPTURA DE EVENTOS DE TECLADO NORMALIZADOS ---

// Listener global acoplado al documento para interceptar el hundimiento físico de teclas
document.addEventListener("keydown", (event) => {
    // Pasamos el input físico por la capa de normalización para homologar nomenclaturas a Arrow Direccional
    const stdKey = normalizeKey(event.key);
    // Evaluamos estrictamente si la llave pertenece a nuestro ecosistema aceptado (Keys {})
    if (keys.hasOwnProperty(stdKey)) {
        // Bloqueamos el scroll o funciones alternativas asignadas por el navegador web (Default)
        event.preventDefault();
        // LÓGICA ANTI-SPAM: Si el estado en memoria no había registrado esta presión...
        if (!keys[stdKey]) {
            // Actualizamos la memoria local a TRUE (Presionado)
            keys[stdKey] = true;
            // Emitimos la petición del input al servidor autoritativo
            sendMovement(stdKey, true);
            // Capturamos la caja gráfica asociada del tutorial del lobby (ui-ArrowX)
            const ui = document.getElementById("ui-" + stdKey);
            // Agregamos la clase de manipulación CSS para prender su brillo
            if(ui) ui.classList.add("active");
        }
    }
});

// Listener global inverso que monitorea el des-enganche físico (liberación) del botón
document.addEventListener("keyup", (event) => {
    // Repetimos rutinas normalizadoras de layout (WASD -> Arrows)
    const stdKey = normalizeKey(event.key);
    // Verificamos propiedad de control
    if (keys.hasOwnProperty(stdKey)) {
        // Aseguramos fluidez cancelando default actions de scroll
        event.preventDefault();
        // Sincronizamos liberando bandera local a FALSE (Liberado)
        keys[stdKey] = false;
        // Lanzamos orden de frenado al backend indicando IsPressed=False
        sendMovement(stdKey, false);
        // Despintamos la interfaz retirando la clase que da luz cyan a la caja simulada
        const ui = document.getElementById("ui-" + stdKey);
        if(ui) ui.classList.remove("active");
    }
});

/**
 * DECLARACIÓN: Función despachadora que construye el payload JSON final y lo transmite vía Socket TCP.
 * @param {string} key - Identificador de tecla estandarizada (ArrowUp, ArrowDown, etc.).
 * @param {boolean} isPressed - Estado booleano de la tecla.
 */
function sendMovement(key, isPressed) {
    // Estricta regla de envío: El objeto debe existir, y el protocolo TCP debe estar OPEN (1)
    if (ws && ws.readyState === WebSocket.OPEN) {
        // Emitimos la conversión literal serializada enviando el tipo de mensaje, la tecla y su estado
        ws.send(JSON.stringify({ type: "input", key: key, pressed: isPressed }));
    }
}