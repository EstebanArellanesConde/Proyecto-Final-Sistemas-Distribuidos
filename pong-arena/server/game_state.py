# Definición de la clase principal que actúa como el motor matemático aislado para cada sala
class GameState:

    # Constructor que inicializa el estado físico de la partida
    def __init__(self):

        # Ancho absoluto del tablero en píxeles
        self.width = 800
        # Alto absoluto del tablero en píxeles
        self.height = 800

        # Coordenada espacial X inicial de la pelota (exactamente en el centro)
        self.ball_x = 400
        # Coordenada espacial Y inicial de la pelota (exactamente en el centro)
        self.ball_y = 400

        # Vector inicial de velocidad horizontal (píxeles por fotograma)
        self.ball_vx = 5
        # Vector inicial de velocidad vertical (píxeles por fotograma)
        self.ball_vy = 4

        # Velocidad de desplazamiento de las paletas al oprimir una tecla
        self.paddle_speed = 10
        # Longitud física de la paleta, usada para calcular los bordes
        self.paddle_length = 100

        # --- NUEVAS VARIABLES FASE 1 ---
        # Guardaremos cuántos jugadores iniciaron la partida para definir el conjunto de reglas físicas
        self.active_players = 0
        # Radio del hitbox de la pelota para colisiones desde el borde, no desde el centro
        self.ball_radius = 10

        # Diccionario que almacena la posición unidimensional (X o Y dependiendo del lado) de cada paleta
        self.paddles = {
            "TOP": 350,    # Posición inicial X para el jugador de arriba (centro)
            "BOTTOM": 350, # Posición inicial X para el jugador de abajo (centro)
            "LEFT": 350,   # Posición inicial Y para el jugador izquierdo (centro)
            "RIGHT": 350   # Posición inicial Y para el jugador derecho (centro)
        }
        
        # Matriz de estados booleanos para rastrear qué teclas mantiene presionadas cada jugador
        self.inputs = {
            # El eje X superior solo escucha teclas horizontales
            "TOP": {"ArrowLeft": False, "ArrowRight": False},
            # El eje X inferior solo escucha teclas horizontales
            "BOTTOM": {"ArrowLeft": False, "ArrowRight": False},
            # El eje Y izquierdo solo escucha teclas verticales
            "LEFT": {"ArrowUp": False, "ArrowDown": False},
            # El eje Y derecho solo escucha teclas verticales
            "RIGHT": {"ArrowUp": False, "ArrowDown": False}
        }

        # Diccionario de puntajes o vidas iniciales para cada jugador
        self.scores = {
            "TOP": 3,
            "RIGHT": 3,
            "BOTTOM": 3,
            "LEFT": 3
        }

        # Bandera booleana para impedir el cálculo físico hasta que todos estén listos
        self.started = False

    # --- NUEVO MÉTODO FASE 1 ---
    # Método invocado por app.py cuando la sala cumple las condiciones para empezar
    def start_game(self, num_players):
        # Almacenamos si es una partida de 2 o 4 jugadores
        self.active_players = num_players
        # Liberamos el bloqueo lógico para que el método update comience a mover la pelota
        self.started = True

    # --- NUEVO MÉTODO FASE 1 ---
    # Método para regresar la pelota al centro cuando alguien pierde un punto
    def reset_ball(self):
        # Reposicionamos X a la mitad del tablero absoluto
        self.ball_x = self.width / 2
        # Reposicionamos Y a la mitad del tablero absoluto
        self.ball_y = self.height / 2
        # Invertimos el vector de velocidad horizontal para que el saque vaya hacia quien acaba de anotar
        self.ball_vx *= -1

    # Interfaz para que el servidor inyecte los comandos de red en la matriz de estados local
    def set_input(self, position, key, pressed):
        # Validamos que el jugador sea un eje horizontal (Arriba o Abajo) y su tecla sea válida
        if position in ["TOP", "BOTTOM"] and key in ["ArrowLeft", "ArrowRight"]:
            # Guardamos el estado de la tecla (True si se pulsó, False si se liberó)
            self.inputs[position][key] = pressed
            
        # Validamos que el jugador sea un eje vertical (Izquierda o Derecha) y su tecla sea válida
        elif position in ["LEFT", "RIGHT"] and key in ["ArrowUp", "ArrowDown"]:
            # Guardamos el estado de la tecla
            self.inputs[position][key] = pressed

    # Función iterativa principal llamada a 60 FPS desde app.py
    def update(self):
        
        # === BLOQUE DE MOVIMIENTO DE PALETAS HORIZONTALES (EJE X) ===
        
        # Si el jugador de arriba presiona izquierda...
        if self.inputs["TOP"]["ArrowLeft"]:
            # Restamos la velocidad, impidiendo mediante 'max' que cruce el límite izquierdo (0)
            self.paddles["TOP"] = max(0, self.paddles["TOP"] - self.paddle_speed)
            
        # Si el jugador de arriba presiona derecha...
        if self.inputs["TOP"]["ArrowRight"]:
            # Sumamos la velocidad, impidiendo mediante 'min' que el borde derecho de la paleta salga del mapa
            self.paddles["TOP"] = min(self.width - self.paddle_length, self.paddles["TOP"] + self.paddle_speed)
            
        # Si el jugador de abajo presiona izquierda...
        if self.inputs["BOTTOM"]["ArrowLeft"]:
            # Límite rígido en el borde 0
            self.paddles["BOTTOM"] = max(0, self.paddles["BOTTOM"] - self.paddle_speed)
            
        # Si el jugador de abajo presiona derecha...
        if self.inputs["BOTTOM"]["ArrowRight"]:
            # Límite rígido considerando el tamaño de la paleta
            self.paddles["BOTTOM"] = min(self.width - self.paddle_length, self.paddles["BOTTOM"] + self.paddle_speed)

        # === BLOQUE DE MOVIMIENTO DE PALETAS VERTICALES (EJE Y) ===
        
        # Si el jugador izquierdo presiona arriba...
        if self.inputs["LEFT"]["ArrowUp"]:
            # Restamos Y para subir, impidiendo cruzar el techo (0)
            self.paddles["LEFT"] = max(0, self.paddles["LEFT"] - self.paddle_speed)
            
        # Si el jugador izquierdo presiona abajo...
        if self.inputs["LEFT"]["ArrowDown"]:
            # Sumamos Y para bajar, limitando con el suelo de la ventana
            self.paddles["LEFT"] = min(self.height - self.paddle_length, self.paddles["LEFT"] + self.paddle_speed)
            
        # Si el jugador derecho presiona arriba...
        if self.inputs["RIGHT"]["ArrowUp"]:
            # Limitamos movimiento hacia el techo
            self.paddles["RIGHT"] = max(0, self.paddles["RIGHT"] - self.paddle_speed)
            
        # Si el jugador derecho presiona abajo...
        if self.inputs["RIGHT"]["ArrowDown"]:
            # Limitamos movimiento hacia el suelo
            self.paddles["RIGHT"] = min(self.height - self.paddle_length, self.paddles["RIGHT"] + self.paddle_speed)

        # === BLOQUE DE FÍSICAS DE LA PELOTA ===
        
        # Evaluamos si la bandera de inicio de partida ya fue activada por app.py
        if self.started:
            
            # Desplazamos la pelota horizontalmente sumando el vector de velocidad X
            self.ball_x += self.ball_vx
            # Desplazamos la pelota verticalmente sumando el vector de velocidad Y
            self.ball_y += self.ball_vy

            # --- NUEVAS FÍSICAS FASE 1: MODO 2 JUGADORES ---
            # Si el motor detecta que solo hay dos clientes conectados...
            if self.active_players == 2:
                
                # 1. Colisión con la pared superior (Techo)
                # Comprobamos si el borde superior de la pelota (centro - radio) choca o pasa el límite de Y=0
                if self.ball_y - self.ball_radius <= 0:
                    # Desencajamos la pelota posicionándola en el borde exacto
                    self.ball_y = self.ball_radius
                    # Invertimos el vector de velocidad vertical para efectuar el rebote
                    self.ball_vy *= -1
                    
                # 2. Colisión con la pared inferior (Suelo)
                # Comprobamos si el borde inferior (centro + radio) choca con el límite máximo (800)
                elif self.ball_y + self.ball_radius >= self.height:
                    # Desencajamos la pelota del suelo
                    self.ball_y = self.height - self.ball_radius
                    # Invertimos el vector vertical
                    self.ball_vy *= -1
                    
                # 3. Colisión con la paleta IZQUIERDA
                # Verificamos si la pelota cruza el plano X donde está dibujada la paleta izquierda (X=10 + ancho=10)
                if self.ball_x - self.ball_radius <= 20:
                    # Verificamos si en ese preciso instante, la pelota intercepta el rango Y de la paleta
                    if self.paddles["LEFT"] <= self.ball_y <= self.paddles["LEFT"] + self.paddle_length:
                        # Desencajamos la pelota de la paleta
                        self.ball_x = 20 + self.ball_radius
                        # Invertimos la velocidad horizontal para rebotar hacia la derecha
                        self.ball_vx *= -1
                        
                # 4. Colisión con la paleta DERECHA
                # Verificamos si la pelota cruza el plano X donde está dibujada la paleta derecha (X=780)
                if self.ball_x + self.ball_radius >= 780:
                    # Verificamos la intersección en el eje Y
                    if self.paddles["RIGHT"] <= self.ball_y <= self.paddles["RIGHT"] + self.paddle_length:
                        # Desencajamos
                        self.ball_x = 780 - self.ball_radius
                        # Rebote horizontal hacia la izquierda
                        self.ball_vx *= -1

                # 5. Sistema de Puntuación (Salidas del Mapa)
                # Si el centro de la pelota cruza el límite izquierdo absoluto (0)
                if self.ball_x < 0:
                    # Castigamos al jugador izquierdo restándole un punto
                    self.scores["LEFT"] -= 1
                    # Reseteamos la posición para el siguiente saque
                    self.reset_ball()
                    
                # Si el centro cruza el límite derecho absoluto (800)
                elif self.ball_x > self.width:
                    # Castigamos al jugador derecho restándole un punto
                    self.scores["RIGHT"] -= 1
                    # Reseteamos la posición
                    self.reset_ball()