
import sys
from random import choice, randint
from enum import Enum
import shelve
import pygame

# original game
# https://youtu.be/MU4psw3ccUI
# art
# https://github.com/danz1ka19/Space-Invaders-Unity-Clone
# https://opengameart.org/content/space-shooter-art
# font
# https://www.dafont.com/pixeled.font
# sounds
# https://opengameart.org/content/512-sound-effects-8-bit-style
# https://opengameart.org/content/arcade-boss-tracks-8-bitchiptune
# colors
# https://www.webucator.com/article/python-color-constants-module/

# переменные экрана
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
pygame.display.set_caption('Игра Papander')

# события
EV_ALIENS_SHOOT = pygame.USEREVENT + 1
EV_ALIENS_SHIP = pygame.USEREVENT + 2

#
GAME_FONT = None
GAME_MUSIC = None
GAME_STATUS = None


# меняем текущий статус приложения
def change_game_status(status):
    global GAME_STATUS
    GAME_STATUS = status


#
def sprite_collide(sprite, group, dokill, spritekill):
    sprite_hit = pygame.sprite.spritecollide(sprite, group, dokill)
    if spritekill and sprite_hit:
        sprite.kill()

    return sprite_hit


# отображение многострочного текста
# https://stackoverflow.com/questions/42014195/rendering-text-with-multiple-lines-in-pygame
def blit_text(surface, text, pos, font, color=pygame.Color('black')):
    words = [word.split(' ') for word in text.splitlines()]  # 2D array where each row is a list of words
    space = font.size(' ')[0]  # the width of a space
    max_width, max_height = surface.get_size()
    x, y = pos
    for line in words:
        for word in line:
            word_surface = font.render(word, 0, color)
            word_width, word_height = word_surface.get_size()
            if x + word_width >= max_width:
                x = pos[0]  # reset the x
                y += word_height  # start on new row
            surface.blit(word_surface, (x, y))
            x += word_width + space
        x = pos[0]  # reset the x
        y += word_height  # start on new row


# задний фон
class Space:
    #
    background = 'resources/background.png'

    def __init__(self):
        self.bg = pygame.image.load(self.background).convert_alpha()
        self.bg = pygame.transform.scale(self.bg, (SCREEN_WIDTH, SCREEN_HEIGHT))

    def draw(self):
        self.bg.set_alpha(randint(60, 100))  # мерцающий эффект экрана
        screen.blit(self.bg, (0, 0))


# выстрел пришельцев/корабля
class Shoot(pygame.sprite.Sprite):
    #
    size = (4, 20)  # размер 4x20
    color = 'white'

    shoot_resource = 'resources/shoot.wav'
    explosion_resource = 'resources/explosion.wav'

    def __init__(self, pos, speed):
        super().__init__()

        # рисуем (белый прямоугольник)
        self.image = pygame.Surface(self.size)
        self.image.fill(self.color)
        self.rect = self.image.get_rect(center=pos)

        # скорость перемещения
        self.speed = speed

    # перемещаем
    def update(self):
        self.rect.y += self.speed
        # проверка на выхода за экран
        if self.rect.y <= -(self.rect.height) or self.rect.y >= SCREEN_HEIGHT + self.rect.height:
            self.kill()


# блок укрытия для нашего корабля
class Block(pygame.sprite.Sprite):
    #
    block_size = 6  # размер одного блока
    color = (255, 48, 48)  # firebrick1

    shape = [  # фигура укрытия (состоит из блоков)
        '  xxxxxxx  ',
        ' xxxxxxxxx ',
        'xxxxxxxxxxx',
        'xxxxxxxxxxx',
        'xxxxxxxxxxx',
        'xxx     xxx',
        'xx       xx']

    def __init__(self, x, y):
        super().__init__()

        self.image = pygame.Surface((self.block_size, self.block_size))
        self.image.fill(self.color)
        self.rect = self.image.get_rect(topleft=(x, y))

    # создаем укрытие из блоков
    def create_shelter(x_start, y_start, x_offset):
        blocks = pygame.sprite.Group()

        for row_index, row in enumerate(Block.shape):
            for col_index, col in enumerate(row):
                if col == 'x':
                    x = x_start + col_index * Block.block_size + x_offset
                    y = y_start + row_index * Block.block_size
                    block = Block(x, y)
                    blocks.add(block)

        return blocks.sprites()


# направление движения
class Direction(Enum):
    Random = 1
    Right = 2
    Left = 3
    Down = 4


# пришелец
class Alien(pygame.sprite.Sprite):
    #
    resource = 'resources/alien_'  # + _type + .png
    size = (40, 30)  # размер 40x30

    score = 100  # базовое количество очков

    def __init__(self, _type, x, y, x_speed, y_speed):
        super().__init__()

        self.image = pygame.image.load(self.resource + _type + '.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, self.size)
        self.rect = self.image.get_rect(topleft=(x, y))

        # скорость перемещения
        self.x_speed = x_speed
        self.y_speed = y_speed

        # количество очков
        if _type == 'big':
            self.score = 300  # big
        elif _type == 'average':
            self.score = 200  # average
        else:
            self.score = 100  # small

    # перемещаем
    def update(self, direction):
        if direction == Direction.Down:
            # вниз
            self.rect.y += self.y_speed
        else:
            # право/лево
            self.rect.x += (self.x_speed if direction == Direction.Right else -(self.x_speed))


# корабль пришельцев
class AlienShip(pygame.sprite.Sprite):
    #
    resource = 'resources/alien_ship.png'
    size = (50, 20)  # размер 50x20

    score = 500  # базовое количество очков

    def __init__(self, direction, y, y_speed):
        super().__init__()

        self.image = pygame.image.load(self.resource).convert_alpha()
        self.image = pygame.transform.scale(self.image, self.size)

        if direction == Direction.Random:
            # случайное направление движения
            direction = choice([Direction.Right, Direction.Left])

        if direction == Direction.Left:
            # справа налево
            x = SCREEN_WIDTH + self.image.get_width()
            self.speed = -(y_speed)
        else:
            # слева направо
            x = -(self.image.get_width())
            self.speed = y_speed

        self.rect = self.image.get_rect(topleft=(x, y))  # позция на экране

    # перемещаем
    def update(self):
        self.rect.x += self.speed


# наш корабль
class Player(pygame.sprite.Sprite):
    #
    resource = 'resources/player.png'
    size = (40, 40)  # размер 40x40

    def __init__(self, pos, speed, shoot_cooldown, min_x=0, max_x=SCREEN_WIDTH):
        super().__init__()

        self.image = pygame.image.load(self.resource).convert_alpha()
        self.image = pygame.transform.scale(self.image, self.size)
        self.rect = self.image.get_rect(midbottom=pos)

        self.speed = speed
        self.min_x = min_x
        self.max_x = max_x

        self.shoot_ready = True
        self.shoot_time = 0
        self.shoot_cooldown = shoot_cooldown

        self.shoots = pygame.sprite.Group()

        if pygame.mixer.get_init() is not None:
            self.shoot_sound = pygame.mixer.Sound(Shoot.shoot_resource)
            self.shoot_sound.set_volume(0.5)

    # ждем интервал между выстрелами
    def recharge(self):
        if not self.shoot_ready:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.shoot_cooldown:
                self.shoot_ready = True

    def shoot(self):
        self.shoots.add(Shoot(self.rect.center, -10))

    # обрабатываем нажатые клавиши
    def process_input(self):
        keys = pygame.key.get_pressed()

        # передвижение право/лево
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        elif keys[pygame.K_LEFT]:
            self.rect.x -= self.speed

        # проверяем ограничения на передвижение
        if self.rect.left <= self.min_x:
            self.rect.left = self.min_x
        elif self.rect.right >= self.max_x:
            self.rect.right = self.max_x

        # стрельба
        if keys[pygame.K_SPACE] and self.shoot_ready:
            self.shoot()
            self.shoot_ready = False
            self.shoot_time = pygame.time.get_ticks()

            if GAME_MUSIC is not None:
                self.shoot_sound.play()

    # перемещаем
    def update(self):
        self.process_input()
        self.recharge()
        self.shoots.update()


# текущий статус игры
class GameStatus(Enum):
    Main_Menu = 1
    Show_Scores = 2
    Playing = 3
    GameOver = 4


# экран основной игры
class Game:
    #
    player_lives = 3  # количество жизней у игрока
    player_level = 1  # начальный уровень
    #	player_level    = 3         # debug
    player_speed = 5  # скорость перемещения игрока
    player_shoot_interval = 600  # интервал между выстрелами игрока

    aliens_x_pos = 70  # позиция пришельцев
    aliens_y_pos = 100
    aliens_rows = 6  # количество пришельцев
    #	aliens_rows     = 1         # debug
    aliens_cols = 8
    aliens_x_speed = 1  # скорость перемещения
    aliens_y_speed = 2
    #	aliens_y_speed  = 20        # debug

    aliens_shoot_speed = 6
    aliens_shoot_interval = 800  # интервал между выстрелами пришельцев в мсек

    ship_y_pos = 80  # позиция корабля пришельцев
    ship_speed = 3
    ship_spawn_time_min = 6000  # min, max время появления корабля в мсек (первое появление в 10 раз быстрее)
    ship_spawn_time_max = 10000

    shelters_y_pos = 480  # позиция укрытий на поле
    shelters_x_pos = SCREEN_WIDTH / 15
    shelters_amount = 4  # количество укрытий

    status_y_pos = 10  # позиция панели состояния
    status_color = 'white'  # цвет текста на панели состояния
    live_resource = Player.resource
    live_size = (25, 25)  # размер иконки жизни, 25x25

    def __init__(self):
        # изображение жизней
        self.live_image = pygame.image.load(self.live_resource).convert_alpha()
        self.live_image = pygame.transform.scale(self.live_image, self.live_size)
        self.lives_x_pos = SCREEN_WIDTH - (self.live_image.get_size()[0] * (self.player_lives - 1) + self.live_size[0])

        #
        if GAME_MUSIC is not None:
            self.shoot_sound = pygame.mixer.Sound(Shoot.shoot_resource)
            self.shoot_sound.set_volume(0.5)
            self.explosion_sound = pygame.mixer.Sound(Shoot.explosion_resource)
            self.explosion_sound.set_volume(0.3)

    # инициализация и старт новой игры или следующего уровня
    def start(self, next_level=False):
        change_game_status(GameStatus.Playing)

        # текущий статус: очки, уровень, жизни
        if not next_level:
            self.status_score = 0
            self.status_level = self.player_level
            self.status_lives = self.player_lives
        else:
            self.status_level += 1

        # создаем игрока
        player_sprite = Player((SCREEN_WIDTH / 2, SCREEN_HEIGHT), self.player_speed, self.player_shoot_interval)
        self.player = pygame.sprite.GroupSingle(player_sprite)

        # создаем укрытия
        if not next_level:
            self.blocks = pygame.sprite.Group()
            shelters_offsets = [num * (SCREEN_WIDTH / self.shelters_amount) for num in range(self.shelters_amount)]
            self.shelters_create(*shelters_offsets, x_start=self.shelters_x_pos, y_start=self.shelters_y_pos)

        # создаем пришельцев
        self.aliens = pygame.sprite.Group()
        self.aliens_shoots = pygame.sprite.Group()
        self.aliens_direction = Direction.Right
        self.aliens_create(self.aliens_rows, self.aliens_cols, self.aliens_x_pos, self.aliens_y_pos)

        # группа для корабля пришельцев
        self.aliens_ship = pygame.sprite.GroupSingle()

        if not next_level:
            self.start_events()

    #
    def stop(self):
        change_game_status(GameStatus.GameOver)

        self.stop_events()

    # запускаем события по таймеру
    def start_events(self):
        pygame.time.set_timer(EV_ALIENS_SHOOT, self.aliens_shoot_interval)
        pygame.time.set_timer(EV_ALIENS_SHIP, int(randint(self.ship_spawn_time_min, self.ship_spawn_time_max) / 10))

    def stop_events(self):
        pygame.time.set_timer(EV_ALIENS_SHOOT, 0)
        pygame.time.set_timer(EV_ALIENS_SHIP, 0)

    # создаем укрытия
    def shelters_create(self, *offset, x_start, y_start):
        for x_offset in offset:
            self.blocks.add(Block.create_shelter(x_start, y_start, x_offset))

    # создаем пришельцев
    def aliens_create(self, rows, cols, x_start, y_start):
        x_distance = 60  # TODO calc distance from count (see shelters_offsets)
        y_distance = 48

        for row_index, row in enumerate(range(rows)):
            for col_index, col in enumerate(range(cols)):
                x = x_start + col_index * x_distance
                y = y_start + row_index * y_distance

                # выбираем тип пришельца в зависимости от позиции (номера строки)
                if row_index == 0:
                    _type = 'big'
                elif 1 <= row_index <= 2:
                    _type = 'average'
                else:
                    _type = 'small'

                # устанавливаем скорость пришельцев в зависимости от уровня
                x_speed = self.aliens_x_speed + (int)(self.status_level / 2)
                y_speed = self.aliens_y_speed + (int)(self.status_level)

                alien_sprite = Alien(_type, x, y, x_speed, y_speed)
                self.aliens.add(alien_sprite)

    # пермещаем пришельцев
    def aliens_move(self):
        # двигаем по текущему направлению
        self.aliens.update(self.aliens_direction)

        # проверяем нужно ли развернуть направление и двинуть вниз
        move_down = False
        all_aliens = self.aliens.sprites()

        for alien in all_aliens:
            if alien.rect.right >= SCREEN_WIDTH:
                # достигли правой части экрана
                self.aliens_direction = Direction.Left
                move_down = True
                break
            elif alien.rect.left <= 0:
                # достигли левой части экрана
                self.aliens_direction = Direction.Right
                move_down = True
                break

        if move_down:
            self.aliens.update(Direction.Down)

    # пришельцы стреляют
    def aliens_shoot(self):
        if self.aliens.sprites():
            random_alien = choice(self.aliens.sprites())
            shoot_sprite = Shoot(random_alien.rect.center, self.aliens_shoot_speed)
            self.aliens_shoots.add(shoot_sprite)

            if GAME_MUSIC is not None:
                self.shoot_sound.play()

    # создание корабля пришельцев и обновление таймера
    def aliens_ship_create(self):
        # TODO появление корабля (как и стрельба) привязаны к таймеру, а перемещение к отрисовке
        #      поэтому корабль может не успеть проехать весь экран за ship_speed
        self.aliens_ship.add(AlienShip(Direction.Random, self.ship_y_pos, self.ship_speed))
        pygame.time.set_timer(EV_ALIENS_SHIP, randint(self.ship_spawn_time_min, self.ship_spawn_time_max))

    # панель состояния
    def display_status(self):
        # очки и скорость (уровень)
        status_text = f'очки: {self.status_score}   уровень: {self.status_level}'

        status = GAME_FONT.render(status_text, False, self.status_color)
        status_rect = status.get_rect(topleft=(10, -(self.status_y_pos)))
        screen.blit(status, status_rect)

        # жизни
        live_size = self.live_image.get_size()
        for live in range(self.status_lives - 1):
            x = self.lives_x_pos + (live * (live_size[0] + 10))
            screen.blit(self.live_image, (x, self.status_y_pos))

    # прверяем пересечения
    def collision_checks(self):

        # выстрелы игрока
        if self.player.sprite.shoots:
            for shoot in self.player.sprite.shoots:
                # куски укрытия
                sprite_collide(shoot, self.blocks, True, True)

                # пришельцы
                aliens_hit = sprite_collide(shoot, self.aliens, True, True)
                if aliens_hit:
                    for alien in aliens_hit:
                        self.status_score += alien.score

                    if GAME_MUSIC is not None:
                        self.explosion_sound.play()

                # корабль пришельцев
                if sprite_collide(shoot, self.aliens_ship, True, True):
                    self.status_score += AlienShip.score

        # выстрелы пришельцев
        if self.aliens_shoots:
            for shoot in self.aliens_shoots:
                # куски укрытия
                sprite_collide(shoot, self.blocks, True, True)

                # игрок
                if sprite_collide(shoot, self.player, False, True):
                    self.status_lives -= 1
                    if self.status_lives <= 0:
                        # не осталось жизней
                        self.stop()

        # пришельцы
        if self.aliens:
            for alien in self.aliens:
                # куски укрытия
                sprite_collide(alien, self.blocks, True, False)

                # игрок
                if sprite_collide(alien, self.player, False, False):
                    # убили пришельцы
                    self.stop()

    # запускаем события по таймеру
    def onevent(self, event):
        if event.type == EV_ALIENS_SHOOT:
            self.aliens_shoot()
        elif event.type == EV_ALIENS_SHIP:
            self.aliens_ship_create()

    #
    def update(self):
        # премещаем все
        self.player.update()
        self.aliens_shoots.update()
        self.aliens_move()
        self.aliens_ship.update()

        # проверяем пересечения
        self.collision_checks()

        # отрисовываем
        self.player.sprite.shoots.draw(screen)
        self.player.draw(screen)
        self.blocks.draw(screen)
        self.aliens_shoots.draw(screen)
        self.aliens.draw(screen)
        self.aliens_ship.draw(screen)

        #
        self.display_status()
        if not self.aliens.sprites():
            self.start(True)  # следующий уровень


# экран меню, результатов, проигрыша
class Menu:
    #
    settings_file = 'settings.dat'

    scores_top = []  # первые 5 результатов
    score_last = 0  # последний результат

    menu_color = 'white'  # цвет текста в меню

    def __init__(self, game):
        change_game_status(GameStatus.Main_Menu)

        self.game = game
        self.settings_load()

    # загрузка сохраненных настроек
    def settings_load(self):
        settings = shelve.open(self.settings_file)

        # восстанавливаем результаты, если есть
        if 'scores' in settings:
            self.scores_top = settings['scores']

        settings.close()

    # сохранение настроек
    def settings_save(self):
        settings = shelve.open(self.settings_file)
        settings['scores'] = self.scores_top
        settings.close()

    # сохранение результата
    def scores_add(self, score):
        if self.score_last != score:
            # добавлем если результат отличается от последнего
            self.score_last = score
            self.scores_top.append(score)
            self.scores_top.sort(reverse=True)
            self.scores_top = self.scores_top[:5]

    # главное меню
    def display_menu(self):
        # текст меню
        # TODO выравнивание
        menu_text = '1  - Начать игру\n' \
                    '2 - Таблица результатов\n' \
                    '0 - Выход'
        blit_text(screen, menu_text, (SCREEN_WIDTH / 4, SCREEN_HEIGHT / 3), GAME_FONT, self.menu_color)

        # читаем клавишу
        keys = pygame.key.get_pressed()

        # выбрали пункт 1, запускаем битву
        if keys[pygame.K_1]:
            self.game.start()

        # выбрали пункт 2, показываем результаты
        elif keys[pygame.K_2]:
            change_game_status(GameStatus.Show_Scores)

        # выбрали пункт 0, выходим
        elif keys[pygame.K_0]:
            self.settings_save()
            pygame.quit()
            sys.exit()

    # проиграли :(
    def display_gameover(self):
        gameover_text = 'Пришельцы победили!\n' \
                        f'Вы набрали {self.game.status_score} очков\n\n' \
                        'нажмите ENTER для продолжения'
        # gameover      = GAME_FONT.render(gameover_text, False, self.menu_color)
        # gameover_rect = gameover.get_rect(center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        # screen.blit(gameover, gameover_rect)
        blit_text(screen, gameover_text, (SCREEN_WIDTH / 4, SCREEN_HEIGHT / 4), GAME_FONT, self.menu_color)

        # ждем Enter
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            change_game_status(GameStatus.Main_Menu)
            # сохраняем результат
            self.scores_add(self.game.status_score)

    # результаты
    def display_scores(self):
        scores_text = 'результаты:\n\n'
        for result in self.scores_top:
            scores_text += f'      {result}\n'
        scores_text += '\nнажмите ENTER'
        blit_text(screen, scores_text, (SCREEN_WIDTH / 3, SCREEN_HEIGHT / 5), GAME_FONT, self.menu_color)

        # ждем Enter
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            change_game_status(GameStatus.Main_Menu)

    #
    def update(self):
        if GAME_STATUS == GameStatus.Main_Menu:
            self.display_menu()
        elif GAME_STATUS == GameStatus.GameOver:
            self.display_gameover()
        elif GAME_STATUS == GameStatus.Show_Scores:
            self.display_scores()


# main
font_resource = 'resources/pixeled.ttf'
font_size = 16

music_resource = 'resources/music.wav'

if __name__ == '__main__':
    # инициализируем pygame
    pygame.mixer.pre_init(44100, -16, 2, 4096)
    # pygame.mixer.init()
    pygame.init()
    #	print('mixer', pygame.mixer.get_init())

    # инициализируем основные переменные
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    GAME_FONT = pygame.font.Font(font_resource, font_size)
    if pygame.mixer.get_init() is not None:
        # если есть звук включаем музыку
        GAME_MUSIC = pygame.mixer.Sound(music_resource)
        GAME_MUSIC.set_volume(0.2)
        GAME_MUSIC.play(loops=-1)

    game = Game()
    space = Space()
    menu = Menu(game)
    #	game.start()         # debug
    #	menu.scores_add(100) # debug

    # основной цикл игры
    while True:
        # события
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                menu.settings_save()
                pygame.quit()
                sys.exit()

            elif GAME_STATUS == GameStatus.Playing:
                game.onevent(event)

        # обновление экрана
        screen.fill((20, 20, 20))  # почти черный
        if GAME_STATUS == GameStatus.Playing:
            game.update()
        else:
            menu.update()
        space.draw()

        pygame.display.flip()
        clock.tick(60)
