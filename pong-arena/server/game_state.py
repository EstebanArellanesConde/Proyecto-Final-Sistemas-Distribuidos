class GameState:

    def __init__(self):

        self.width = 800
        self.height = 800

        self.ball_x = 400
        self.ball_y = 400

        self.ball_vx = 5
        self.ball_vy = 4

    def update(self):

        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        if self.ball_x <= 0 or self.ball_x >= self.width:
            self.ball_vx *= -1

        if self.ball_y <= 0 or self.ball_y >= self.height:
            self.ball_vy *= -1

    def update(self):

        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        # Rebote simple temporal

        if self.ball_x <= 0 or self.ball_x >= self.width:

            self.ball_vx *= -1

        if self.ball_y <= 0 or self.ball_y >= self.height:

            self.ball_vy *= -1