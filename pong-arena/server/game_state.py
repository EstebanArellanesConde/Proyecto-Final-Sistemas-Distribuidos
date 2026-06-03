# Definición de la clase principal que actúa como el motor autoritativo de físicas y reglas
class GameState:

    # Constructor que inicializa el estado físico de la partida y recibe la meta de puntos
    def __init__(self, target_score=10):

        # Ancho absoluto del tablero virtual en píxeles
        self.width = 800
        # Alto absoluto del tablero virtual en píxeles
        self.height = 800

        # Posición horizontal inicial de la pelota (centro del tablero)
        self.ball_x = 400
        # Posición vertical inicial de la pelota (centro del tablero)
        self.ball_y = 400

        # Vector de velocidad horizontal (píxeles por actualización)
        self.ball_vx = 5
        # Vector de velocidad vertical (píxeles por actualización)
        self.ball_vy = 4

        # Velocidad de desplazamiento de las paletas controladas por el jugador
        self.paddle_speed = 10
        # Longitud física del hitbox de cada paleta
        self.paddle_length = 100

        # Cantidad de jugadores activos para dictar las reglas del entorno (2 o 4)
        self.active_players = 0
        # Tamaño radial del hitbox de la pelota para cálculo preciso de colisiones
        self.ball_radius = 10

        # Almacenamos la meta de puntos necesaria para ganar el juego
        self.target_score = target_score
        
        # Variable crítica para almacenar qué jugador fue el último en golpear la pelota (LEFT, RIGHT, TOP, BOTTOM)
        self.last_touch = None
        
        # Bandera para detener las físicas cuando alguien alcanza el puntaje objetivo
        self.game_over = False
        # Variable para almacenar la cadena de texto con el ID del ganador de la ronda
        self.winner = None

        # Diccionario con las coordenadas unidimensionales (eje de movimiento) de las paletas
        self.paddles = {
            "TOP": 350, "BOTTOM": 350,
            "LEFT": 350, "RIGHT": 350
        }
        
        # Diccionario para rastrear el estado actual (presionado/liberado) de las teclas de cada jugador
        self.inputs = {
            "TOP": {"ArrowLeft": False, "ArrowRight": False},
            "BOTTOM": {"ArrowLeft": False, "ArrowRight": False},
            "LEFT": {"ArrowUp": False, "ArrowDown": False},
            "RIGHT": {"ArrowUp": False, "ArrowDown": False}
        }

        # Diccionario de puntajes, ahora inicializado en 0 para contar de forma incremental
        self.scores = {
            "TOP": 0, "RIGHT": 0,
            "BOTTOM": 0, "LEFT": 0
        }

        # Bandera lógica para congelar la pelota hasta que la interfaz indique el inicio
        self.started = False

    # Método invocado por app.py cuando la sala está lista para iniciar
    def start_game(self, num_players):
        # Registramos cuántos jugadores entraron para adaptar las paredes
        self.active_players = num_players
        # Habilitamos el cálculo físico
        self.started = True

    # Método para regresar la pelota al centro del mapa tras una anotación
    def reset_ball(self):
        # Devolvemos X al centro absoluto
        self.ball_x = self.width / 2
        # Devolvemos Y al centro absoluto
        self.ball_y = self.height / 2
        # Invertimos la velocidad horizontal para darle el saque inicial al perdedor
        self.ball_vx *= -1
        # IMPORTANTE: Borramos la memoria del último toque para evitar puntos fantasma en el nuevo saque
        self.last_touch = None

    # Método encargado de evaluar y asignar el puntaje bajo la regla del "Último Toque"
    def award_point(self):
        # Solo procesamos el punto si alguien golpeó la pelota (evita puntos si nadie tocó la pelota en el saque)
        if self.last_touch is not None:
            # Sumamos un punto entero al jugador que realizó el último impacto
            self.scores[self.last_touch] += 1
            
            # Verificamos si este nuevo punto iguala o supera la condición de victoria
            if self.scores[self.last_touch] >= self.target_score:
                # Marcamos el fin del juego para detener el loop de físicas en update()
                self.game_over = True
                # Registramos oficialmente al ganador de la partida
                self.winner = self.last_touch
                
        # Independientemente de si hubo punto o no, reseteamos la pelota para continuar
        self.reset_ball()

    # Interfaz para actualizar el estado de los controles desde la red
    def set_input(self, position, key, pressed):
        if position in ["TOP", "BOTTOM"] and key in ["ArrowLeft", "ArrowRight"]:
            self.inputs[position][key] = pressed
        elif position in ["LEFT", "RIGHT"] and key in ["ArrowUp", "ArrowDown"]:
            self.inputs[position][key] = pressed

    # Función del núcleo matemático, invocada 60 veces por segundo (60 FPS)
    def update(self):
        
        # Abortamos inmediatamente cualquier cálculo de movimiento si la partida ya tiene un ganador
        if self.game_over:
            return

        # === BLOQUE DE MOVIMIENTO DE PALETAS (Límites rígidos en bordes) ===
        if self.inputs["TOP"]["ArrowLeft"]: self.paddles["TOP"] = max(0, self.paddles["TOP"] - self.paddle_speed)
        if self.inputs["TOP"]["ArrowRight"]: self.paddles["TOP"] = min(self.width - self.paddle_length, self.paddles["TOP"] + self.paddle_speed)
        if self.inputs["BOTTOM"]["ArrowLeft"]: self.paddles["BOTTOM"] = max(0, self.paddles["BOTTOM"] - self.paddle_speed)
        if self.inputs["BOTTOM"]["ArrowRight"]: self.paddles["BOTTOM"] = min(self.width - self.paddle_length, self.paddles["BOTTOM"] + self.paddle_speed)
        if self.inputs["LEFT"]["ArrowUp"]: self.paddles["LEFT"] = max(0, self.paddles["LEFT"] - self.paddle_speed)
        if self.inputs["LEFT"]["ArrowDown"]: self.paddles["LEFT"] = min(self.height - self.paddle_length, self.paddles["LEFT"] + self.paddle_speed)
        if self.inputs["RIGHT"]["ArrowUp"]: self.paddles["RIGHT"] = max(0, self.paddles["RIGHT"] - self.paddle_speed)
        if self.inputs["RIGHT"]["ArrowDown"]: self.paddles["RIGHT"] = min(self.height - self.paddle_length, self.paddles["RIGHT"] + self.paddle_speed)

        # === BLOQUE DE FÍSICAS DE LA PELOTA ===
        if self.started:
            
            # Aplicamos los vectores de inercia a la posición espacial
            self.ball_x += self.ball_vx
            self.ball_y += self.ball_vy

            # 1. Colisión con la paleta IZQUIERDA
            if self.ball_x - self.ball_radius <= 20:
                if self.paddles["LEFT"] <= self.ball_y <= self.paddles["LEFT"] + self.paddle_length:
                    self.ball_x = 20 + self.ball_radius # Desencajamos
                    self.ball_vx *= -1 # Rebotamos
                    self.last_touch = "LEFT" # Registramos a este jugador como el último en tocar
                    
            # 2. Colisión con la paleta DERECHA
            elif self.ball_x + self.ball_radius >= 780:
                if self.paddles["RIGHT"] <= self.ball_y <= self.paddles["RIGHT"] + self.paddle_length:
                    self.ball_x = 780 - self.ball_radius
                    self.ball_vx *= -1
                    self.last_touch = "RIGHT" # Registramos a este jugador como el último en tocar

            # === ADAPTACIÓN DE ENTORNO: 2 JUGADORES ===
            if self.active_players == 2:
                # Techo sólido: Rebota pero NO registra last_touch
                if self.ball_y - self.ball_radius <= 0:
                    self.ball_y = self.ball_radius
                    self.ball_vy *= -1
                    
                # Suelo sólido: Rebota pero NO registra last_touch
                elif self.ball_y + self.ball_radius >= self.height:
                    self.ball_y = self.height - self.ball_radius
                    self.ball_vy *= -1

                # Si la pelota se pierde por la izquierda o por la derecha, asignamos el punto a quien la tocó al final
                if self.ball_x < 0 or self.ball_x > self.width:
                    self.award_point()

            # === ADAPTACIÓN DE ENTORNO: 4 JUGADORES ===
            elif self.active_players == 4:
                # 3. Colisión orgánica con la paleta SUPERIOR
                if self.ball_y - self.ball_radius <= 20:
                    if self.paddles["TOP"] <= self.ball_x <= self.paddles["TOP"] + self.paddle_length:
                        self.ball_y = 20 + self.ball_radius
                        self.ball_vy *= -1
                        self.last_touch = "TOP" # Registramos el toque
                        
                # 4. Colisión orgánica con la paleta INFERIOR
                elif self.ball_y + self.ball_radius >= 780:
                    if self.paddles["BOTTOM"] <= self.ball_x <= self.paddles["BOTTOM"] + self.paddle_length:
                        self.ball_y = 780 - self.ball_radius
                        self.ball_vy *= -1
                        self.last_touch = "BOTTOM" # Registramos el toque

                # En 4P, cualquier salida del mapa detona la asignación del punto al último que tocó
                if self.ball_x < 0 or self.ball_x > self.width or self.ball_y < 0 or self.ball_y > self.height:
                    self.award_point()