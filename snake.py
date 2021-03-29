import sys
import json
import random
import pygame


class Part:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def pos(self):
        return (self.x, self.y)

    def move(self, direction):
        dx, dy, = direction
        self.x += dx
        self.y += dy

    def draw(self, surface, color):
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, color, rect)


class Food(Part):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.age = 0

    def draw(self, surface, color=(200, 200, 200)):
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, color, rect)


class Snake:
    def __init__(self, x, y, width, height):
        self.head = Part(x, y, width, height)
        self.body = [self.head]
        self.__direction = (0, 0)

    @property
    def direction(self):
        return self.__direction

    @direction.setter
    def direction(self, direction):
        if (self.__direction[0] != -direction[0] or
            self.__direction[1] != -direction[1] or
            len(self.body) < 2):
            self.__direction = direction

    @property
    def body_part_positions(self):
        return [part.pos for part in self.body]

    def move(self):
        for i, (x, y) in enumerate(self.body_part_positions[:-1]):
            self.body[i+1].x = x
            self.body[i+1].y = y
        self.head.move(self.direction)

    def draw(self, surface, color=(150, 150, 150)):
        for part in self.body:
            part.draw(surface, color)
        self.head.draw(surface, color=(100, 100, 100))


class Game:
    def __init__(self, food_lifetime, grid_size, cell_size):
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.snake = Snake(*self.__random_seed(), self.cell_size, self.cell_size)
        self.food = Food(*self.__random_seed(), self.cell_size, self.cell_size)
        self.food_lifetime = food_lifetime

    @property
    def score(self):
        return len(self.snake.body)

    def __random_seed(self):
        # TODO: Do not plant food underneath snake
        return [random.randint(0, self.grid_size-1) * self.cell_size,
                random.randint(0, self.grid_size-1) * self.cell_size]

    def __check_pbc(self):
        if self.snake.head.x < 0:
            self.snake.head.x += self.grid_size*self.cell_size
        elif self.snake.head.x >= self.grid_size*self.cell_size:
            self.snake.head.x -= self.grid_size*self.cell_size
        if self.snake.head.y < 0:
            self.snake.head.y += self.grid_size*self.cell_size
        elif self.snake.head.y >= self.grid_size*self.cell_size:
            self.snake.head.y -= self.grid_size*self.cell_size

    def __check_food(self):
        if self.food.pos == self.snake.head.pos:
            self.snake.body.append(self.food)
            self.food = Food(*self.__random_seed(), self.cell_size, self.cell_size,)
        elif self.food.age > self.food_lifetime:
            self.food = Food(*self.__random_seed(), self.cell_size, self.cell_size,)
        self.food.age += 1

    def __check_failure(self):
        # TODO: Fail when running into the last part
        snake_bit_itself = self.snake.head.pos in self.snake.body_part_positions[1:-1]
        return snake_bit_itself

    def update(self):
        self.snake.move()
        self.__check_pbc()
        self.__check_food()
        return self.__check_failure()

    def draw(self, surface):
        self.food.draw(surface)
        self.snake.draw(surface)


class Session:
    def __init__(self, player, game, update_frequency, framerate):
        self.player = player
        self.game = game
        self.update_frequency = update_frequency
        self.framerate = framerate

    def __load_highscores(self):
        try:
            with open('highscores.json', 'r') as json_file:
                scores = json.load(json_file)
        except (FileNotFoundError, json.JSONDecodeError):
            scores = {self.player : 0}
        return scores

    def update_highscores(self):
        print(f'Your final length was {self.game.score}.')
        highscores_have_changed = False
        highscores = self.__load_highscores()
        if max(highscores.values()) < self.game.score:
            print('This is a new all-time highscore!')
            highscores_have_changed = True
        else:
            try:
                player_highscore = highscores[f'{self.player}']
            except KeyError:
                player_highscore = 0
            if self.game.score > player_highscore:
                print('This is a new personal highscore!')
                highscores_have_changed = True
        if highscores_have_changed:
            highscores.update({self.player : self.game.score})
            with open('highscores.json', 'w') as json_file:
                json.dump(highscores, json_file)

    def play(self):
        pygame.init()
        clock = pygame.time.Clock()
        GAMEUPDATE = pygame.USEREVENT + 1
        pygame.time.set_timer(GAMEUPDATE, self.update_frequency)
        width = height = self.game.grid_size * self.game.cell_size
        screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        canvas = screen.copy()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    width, height = event.size
                elif event.type == GAMEUPDATE:
                    game_over = self.game.update()
                    if game_over:
                        self.update_highscores()
                        pygame.quit()
                        sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        direction = (0, -1)
                    elif event.key == pygame.K_DOWN:
                        direction = (0, 1)
                    elif event.key == pygame.K_LEFT:
                        direction = (-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        direction = (1, 0)
                    direction = (direction[0] * self.game.cell_size,
                                 direction[1] * self.game.cell_size)
                    self.game.snake.direction = direction

            canvas.fill((0, 0, 0))
            self.game.draw(canvas)
            screen.blit(pygame.transform.scale(canvas, (width, height)), (0, 0))
            pygame.display.update()
            clock.tick(self.framerate)


def main():
    print('\n\n\n\n    :::::::: Welcome to SNAKE ::::::::\n\n')
    print('Your nickname')
    PLAYER = input('>>>> ')
    FRAMERATE = 60
    UPDATE_FREQUENCY = 200
    FOOD_LIFETIME = 70
    GRID_SIZE = 30
    CELL_SIZE = 20
    GAME = Game(FOOD_LIFETIME, GRID_SIZE, CELL_SIZE)
    SESSION = Session(PLAYER, GAME, UPDATE_FREQUENCY, FRAMERATE)
    SESSION.play()

if __name__ == '__main__':
    main()
