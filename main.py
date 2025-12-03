import pygame, sys, math, time, random, os, json

# -------------------- CONFIG / CONSTANTS --------------------

WIDTH, HEIGHT = 960, 640
FPS = 60
TILE = 40

BG = (5, 5, 20)
GRID = (25, 25, 60)
WALL = (10, 10, 40)
PLAYER_COLOR = (255, 0, 140)
GUARD_COLOR = (0, 255, 255)
VISION_COLOR = (0, 255, 255, 50)
TREASURE_COLOR = (255, 255, 0)
EXIT_COLOR = (0, 255, 0)
TEXT_COLOR = (230, 230, 230)
KEY_COLOR = (255, 165, 0)
DOOR_COLOR = (139, 69, 19)
POWERUP_COLOR = (0, 255, 0)

PLAYER_SPEED = 3
CROUCH_SPEED = 1.4

# Difficulty settings (vision range, detection time, guard speed, EMP availability, time limit multiplier)
DIFFICULTIES = {
    "Easy":     {"vision": 220, "detect": 1.6, "guard": 1.7, "emp": True,  "time_mult": 1.5},
    "Medium":   {"vision": 260, "detect": 1.1, "guard": 2.2, "emp": True,  "time_mult": 1.0},
    "Hard":     {"vision": 300, "detect": 0.85,"guard": 2.7, "emp": True,  "time_mult": 0.8},
    "Extreme":  {"vision": 330, "detect": 0.6, "guard": 3.1, "emp": False, "time_mult": 0.6},
    "Nightmare":{"vision": 360, "detect": 0.4, "guard": 3.5, "emp": False, "time_mult": 0.4},
}

# LEVELS: 8 levels with treasures, doors, keys, powerups
LEVELS = [
    # Level 1 – Simple
    [
        "########################",
        "#P.....T..............E#",
        "#.#####....######......#",
        "#.....#....#....G......#",
        "#.###.#....#######.###.#",
        "#.....#............###.#",
        "#.####.#######..G......#",
        "#......................#",
        "########################",
    ],
    # Level 2 – Walls and Guards
    [
        "########################",
        "#P....T.....#.........E#",
        "#.#####.....#..####..G.#",
        "#.....#.....#..#....####",
        "#.###.#.########.###...#",
        "#...#.#........#...#...#",
        "#.###.#....G..#.#.##...#",
        "#......................#",
        "########################",
    ],
    # Level 3 – Doors and Keys
    [
        "########################",
        "#P....K.....#.........E#",
        "#.#####.....D..####..G.#",
        "#.....#.....#..#....####",
        "#.###.#.########.###...#",
        "#...#.#........#...#...#",
        "#.###.#....G..#.#.##...#",
        "#......................#",
        "########################",
    ],
    # Level 4 – Multiple Treasures
    [
        "########################",
        "#P....T.....T.........E#",
        "#.#####.....#..####..G.#",
        "#.....#.....#..#....####",
        "#.###.#.########.###...#",
        "#...#.#........#...#...#",
        "#.###.#....G..#.#.##...#",
        "#......................#",
        "########################",
    ],
    # Level 5 – Complex Maze
    [
        "########################",
        "#P..T.#.....#.........E#",
        "#.####.#.....#..####..G#",
        "#.....#.#....#..#....###",
        "#.###.#.#.########.###.#",
        "#...#.#.#........#...#.#",
        "#.###.#.#....G..#.#.##.#",
        "#.....#................#",
        "########################",
    ],
    # Level 6 – Power-ups (speed)
    [
        "########################",
        "#P....S.....#.........E#",
        "#.#####.....#..####..G.#",
        "#.....#.....#..#....####",
        "#.###.#.########.###...#",
        "#...#.#........#...#...#",
        "#.###.#....G..#.#.##...#",
        "#......................#",
        "########################",
    ],
    # Level 7 – High Security (extra guard)
    [
        "########################",
        "#P....T.....#.........E#",
        "#.#####.....#..####..G.#",
        "#.....#.....#..#....####",
        "#.###.#.########.###...#",
        "#...#.#........#...#...#",
        "#.###.#....G..#.#.##...#",
        "#.....G................#",
        "########################",
    ],
    # Level 8 – Final Heist (doors, keys, speed)
    [
        "########################",
        "#P..T.K.....D.........E#",
        "#.####.#.....#..####..G#",
        "#.....#.#....#..#....###",
        "#.###.#.#.########.###.#",
        "#...#.#.#........#...#.#",
        "#.###.#.#....G..#.#.##.#",
        "#.....#.....S..........#",
        "########################",
    ]
]

# -------------------- MAP / LEVEL UTILS --------------------

def load_level(map_data):
    walls = []
    guards = []
    player_pos = None
    treasures = []
    exit_rect = None
    keys = []
    doors = []
    powerups = []

    for y, row in enumerate(map_data):
        for x, ch in enumerate(row):
            wx, wy = x * TILE, y * TILE
            tile_rect = pygame.Rect(wx, wy, TILE, TILE)

            if ch == "#":
                walls.append(tile_rect)
            elif ch == "P":
                player_pos = pygame.Vector2(tile_rect.center)
            elif ch == "T":
                treasures.append(pygame.Rect(wx + 8, wy + 8, 24, 24))
            elif ch == "E":
                exit_rect = pygame.Rect(wx + 8, wy + 8, 24, 24)
            elif ch == "G":
                guards.append(pygame.Vector2(tile_rect.center))
            elif ch == "K":
                keys.append(pygame.Rect(wx + 8, wy + 8, 24, 24))
            elif ch == "D":
                doors.append(pygame.Rect(wx, wy, TILE, TILE))
            elif ch == "S":
                powerups.append({"type": "speed", "rect": pygame.Rect(wx + 8, wy + 8, 24, 24)})

    return walls, player_pos, guards, treasures, exit_rect, keys, doors, powerups

def line_of_sight(start, end, walls):
    """Raycast with wall blocking – used for sight and sound."""
    steps = int(start.distance_to(end) / 6)
    if steps <= 0:
        return True
    direction = (end - start) / steps
    point = pygame.Vector2(start)
    for _ in range(steps):
        for w in walls:
            if w.collidepoint(point.x, point.y):
                return False
        point += direction
    return True

# -------------------- PARTICLES --------------------

class Particle:
    def __init__(self, pos, vel, color, lifetime=0.5):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.color = color
        self.lifetime = lifetime
        self.start_time = time.time()

    def update(self):
        self.pos += self.vel
        self.vel *= 0.95

    def is_alive(self):
        return (time.time() - self.start_time) < self.lifetime

    def draw(self, screen):
        t = (time.time() - self.start_time) / self.lifetime
        alpha = max(0, int(255 * (1 - t)))
        surf = pygame.Surface((4, 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (2, 2), 2)
        screen.blit(surf, (self.pos.x, self.pos.y))

# -------------------- PLAYER --------------------

class Player:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.size = 22
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.crouch = False
        self.vel = pygame.Vector2(0, 0)
        self.speed_boost = 1.0
        self.speed_end = 0
        self.invisible = False
        self.invis_end = 0
        self.anim_frame = 0
        self.anim_timer = 0
        self.update_rect()

    def update_rect(self):
        self.rect.center = (self.pos.x, self.pos.y)

    def move(self, dx, dy, walls):
        # apply speed boost duration
        if time.time() > self.speed_end:
            self.speed_boost = 1.0
        if time.time() > self.invis_end:
            self.invisible = False

        target_vel = pygame.Vector2(dx, dy) * self.speed_boost
        self.vel = (self.vel * 0.6) + (target_vel * 0.4)  # smoothed

        temp = self.rect.copy()
        temp.centerx += self.vel.x
        if not any(temp.colliderect(w) for w in walls):
            self.pos.x += self.vel.x

        temp = self.rect.copy()
        temp.centery += self.vel.y
        if not any(temp.colliderect(w) for w in walls):
            self.pos.y += self.vel.y

        self.update_rect()
        # simple animation cycle
        if self.vel.length_squared() > 0.1:
            self.anim_timer += 1
            if self.anim_timer > 8:
                self.anim_frame = (self.anim_frame + 1) % 4
                self.anim_timer = 0
        else:
            self.anim_frame = 0

    def draw(self, screen):
        # invisibility hides player (for guards), but still render faint outline for user?
        if self.invisible and time.time() < self.invis_end:
            alpha = 80
        else:
            alpha = 255

        col = (255, 50, 160) if self.crouch else PLAYER_COLOR

        base_surf = pygame.Surface((self.rect.width + 10, self.rect.height + 10), pygame.SRCALPHA)
        pygame.draw.rect(base_surf, (100, 0, 70, alpha), base_surf.get_rect(), border_radius=8)
        pygame.draw.rect(base_surf, (*col, alpha), base_surf.get_rect().inflate(-8, -8), border_radius=6)

        # legs animation
        leg_offset = (self.anim_frame - 1.5) * 2
        cx = base_surf.get_width() // 2
        by = base_surf.get_height() - 3
        pygame.draw.line(base_surf, (*col, alpha), (cx - 4, by), (cx - 4 + leg_offset, by + 5), 2)
        pygame.draw.line(base_surf, (*col, alpha), (cx + 4, by), (cx + 4 - leg_offset, by + 5), 2)

        screen.blit(base_surf, base_surf.get_rect(center=self.rect.center))

# -------------------- GUARD --------------------

class Guard:
    def __init__(self, pos, patrol_range, vision_range, speed, pattern="horizontal"):
        self.pos = pygame.Vector2(pos)
        self.speed = speed
        self.vision = vision_range
        self.pattern = pattern
        self.rect = pygame.Rect(0, 0, 24, 24)
        self.alert = False
        self.alert_timer = 0
        self.chase_target = None
        self.facing = pygame.Vector2(1, 0)

        # define patrol bounds
        if self.pattern == "horizontal":
            self.start_x = self.pos.x - patrol_range / 2
            self.end_x = self.pos.x + patrol_range / 2
            self.start_y = self.end_y = self.pos.y
            self.vel = pygame.Vector2(self.speed, 0)
        elif self.pattern == "vertical":
            self.start_y = self.pos.y - patrol_range / 2
            self.end_y = self.pos.y + patrol_range / 2
            self.start_x = self.end_x = self.pos.x
            self.vel = pygame.Vector2(0, self.speed)
        else:  # box pattern
            self.start_x = self.pos.x - patrol_range / 2
            self.end_x = self.pos.x + patrol_range / 2
            self.start_y = self.pos.y - patrol_range / 2
            self.end_y = self.pos.y + patrol_range / 2
            self.vel = pygame.Vector2(self.speed, 0)

        self.update_rect()

    def update_rect(self):
        self.rect.center = (self.pos.x, self.pos.y)

    def update(self, player_pos=None):
        if self.alert and player_pos is not None:
            # chase player
            diff = player_pos - self.pos
            if diff.length_squared() > 1:
                direction = diff.normalize()
                self.vel = direction * (self.speed * 1.6)
                self.facing = direction
            self.pos += self.vel
            self.alert_timer -= 1 / FPS
            if self.alert_timer <= 0:
                self.alert = False
        else:
            # patrol patterns
            if self.pattern == "horizontal":
                self.pos += self.vel
                if self.pos.x <= self.start_x:
                    self.pos.x = self.start_x
                    self.vel.x = self.speed
                    self.facing = pygame.Vector2(1, 0)
                elif self.pos.x >= self.end_x:
                    self.pos.x = self.end_x
                    self.vel.x = -self.speed
                    self.facing = pygame.Vector2(-1, 0)
            elif self.pattern == "vertical":
                self.pos += self.vel
                if self.pos.y <= self.start_y:
                    self.pos.y = self.start_y
                    self.vel.y = self.speed
                    self.facing = pygame.Vector2(0, 1)
                elif self.pos.y >= self.end_y:
                    self.pos.y = self.end_y
                    self.vel.y = -self.speed
                    self.facing = pygame.Vector2(0, -1)
            else:  # box
                self.pos += self.vel
                if self.vel.x > 0 and self.pos.x >= self.end_x:
                    self.pos.x = self.end_x
                    self.vel = pygame.Vector2(0, self.speed)
                    self.facing = pygame.Vector2(0, 1)
                elif self.vel.y > 0 and self.pos.y >= self.end_y:
                    self.pos.y = self.end_y
                    self.vel = pygame.Vector2(-self.speed, 0)
                    self.facing = pygame.Vector2(-1, 0)
                elif self.vel.x < 0 and self.pos.x <= self.start_x:
                    self.pos.x = self.start_x
                    self.vel = pygame.Vector2(0, -self.speed)
                    self.facing = pygame.Vector2(0, -1)
                elif self.vel.y < 0 and self.pos.y <= self.start_y:
                    self.pos.y = self.start_y
                    self.vel = pygame.Vector2(self.speed, 0)
                    self.facing = pygame.Vector2(1, 0)

        self.update_rect()

    def sees_player(self, player, walls, emp_active):
        if emp_active:
            return False
        if player.invisible and time.time() < player.invis_end:
            return False

        vec = player.pos - self.pos
        dist = vec.length()
        if dist == 0 or dist > self.vision:
            return False

        direction_to_player = vec.normalize()
        dot = max(-1, min(1, self.facing.dot(direction_to_player)))
        angle = math.acos(dot)
        max_angle = math.radians(80) / 2
        if angle > max_angle:
            return False

        if not line_of_sight(self.pos, player.pos, walls):
            return False

        return True

    def alert_nearby(self, guards):
        for g in guards:
            if g is not self and self.pos.distance_to(g.pos) < 120:
                g.alert = True
                g.alert_timer = 3.0
                g.chase_target = self.pos

    def draw(self, screen):
        col = (255, 120, 120) if self.alert else GUARD_COLOR
        pygame.draw.rect(screen, col, self.rect, border_radius=4)

        # vision cone
        cone_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        base_angle = math.atan2(self.facing.y, self.facing.x) - math.radians(80) / 2
        pts = [self.pos.xy]
        for i in range(40):
            ang = base_angle + (math.radians(80) * i / 40)
            x = self.pos.x + math.cos(ang) * self.vision
            y = self.pos.y + math.sin(ang) * self.vision
            pts.append((x, y))
        pygame.draw.polygon(cone_surf, VISION_COLOR, pts)
        screen.blit(cone_surf, (0, 0))

# -------------------- GAME CLASS --------------------

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pixel Bank Heist – Full Heist Edition")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("segoeui", 20)
        self.big = pygame.font.SysFont("segoeui", 42, bold=True)
        self.small = pygame.font.SysFont("segoeui", 14)

        # Music / sounds are optional – game runs without files
        try:
            pygame.mixer.music.load("sounds/bg_music.mp3")
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
            self.sounds = {
                "alarm":   pygame.mixer.Sound("sounds/alarm.wav"),
                "emp":     pygame.mixer.Sound("sounds/emp.wav"),
                "win":     pygame.mixer.Sound("sounds/win.wav"),
                "lose":    pygame.mixer.Sound("sounds/lose.wav"),
                "collect": pygame.mixer.Sound("sounds/collect.wav"),
            }
        except:
            self.sounds = {}

        self.state = "difficulty"
        self.level_index = 0
        self.diff_name = "Medium"
        self.diff_settings = DIFFICULTIES[self.diff_name]

        self.detect_meter = 0.0
        self.emp_available = self.diff_settings["emp"]
        self.emp_end_time = 0
        self.start_time = time.time()
        self.time_limit = 120 * self.diff_settings["time_mult"]

        self.score = 0
        self.screen_shake = 0
        self.particles = []

        self.high_scores = self.load_high_scores()

        self.load_level()

    def load_high_scores(self):
        if os.path.exists("highscores.json"):
            try:
                with open("highscores.json", "r") as f:
                    return json.load(f)
            except:
                return {k: 0 for k in DIFFICULTIES.keys()}
        return {k: 0 for k in DIFFICULTIES.keys()}

    def save_high_scores(self):
        with open("highscores.json", "w") as f:
            json.dump(self.high_scores, f)

    def load_level(self):
        self.diff_settings = DIFFICULTIES[self.diff_name]
        walls, player_pos, guard_positions, treasures, exit_rect, keys, doors, powerups = load_level(
            LEVELS[self.level_index]
        )
        self.walls = walls[:]  # copy
        self.player = Player(player_pos)
        self.treasures = treasures
        self.exit_rect = exit_rect
        self.keys = keys
        self.doors = doors
        self.powerups = powerups

        # doors act like walls until key is used
        self.walls.extend(self.doors)

        self.has_key = False

        self.detect_meter = 0.0
        self.emp_available = self.diff_settings["emp"]
        self.emp_end_time = 0
        self.start_time = time.time()
        self.time_limit = 120 * self.diff_settings["time_mult"]

        self.particles.clear()
        self.screen_shake = 0

        self.guards = []
        for i, g_pos in enumerate(guard_positions):
            pattern = ["horizontal", "vertical", "box"][i % 3]
            g = Guard(
                g_pos,
                patrol_range=220,
                vision_range=self.diff_settings["vision"],
                speed=self.diff_settings["guard"],
                pattern=pattern,
            )
            self.guards.append(g)

    # ----------------- SOUND PROPAGATION (S2) -----------------

    def emit_sound(self, source_pos, radius):
        """Advanced sound: sound travels with LOS, walls block."""
        for g in self.guards:
            if g.alert:
                continue
            dist = g.pos.distance_to(source_pos)
            if dist <= radius and line_of_sight(source_pos, g.pos, self.walls):
                g.alert = True
                g.alert_timer = 2.5
                g.chase_target = source_pos

    # ----------------- STATE LOOPS -----------------

    def run(self):
        while True:
            if self.state == "difficulty":
                self.difficulty_menu()
            elif self.state == "menu":
                self.menu_loop()
            elif self.state == "play":
                self.play_loop()
            elif self.state == "caught":
                self.caught_loop()
            elif self.state == "win":
                self.win_loop()
            elif self.state == "gameover":
                self.gameover_loop()

    def difficulty_menu(self):
        options = list(DIFFICULTIES.keys())
        index = options.index(self.diff_name)
        while self.state == "difficulty":
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_UP:
                        index = (index - 1) % len(options)
                    elif e.key == pygame.K_DOWN:
                        index = (index + 1) % len(options)
                    elif e.key == pygame.K_RETURN:
                        self.diff_name = options[index]
                        self.state = "menu"

            self.screen.fill(BG)
            self.draw_center("Select Difficulty", self.big, (255, 0, 180), -120)

            for i, name in enumerate(options):
                color = (0, 255, 200) if i == index else TEXT_COLOR
                self.draw_center(name, self.font, color, -40 + i * 30)

            self.draw_center("↑ / ↓ and Enter", self.font, (200, 200, 200), 110)

            pygame.display.flip()
            self.clock.tick(FPS)

    def menu_loop(self):
        while self.state == "menu":
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    self.load_level()
                    self.state = "play"

            self.screen.fill(BG)
            self.draw_center("PIXEL BANK HEIST", self.big, (255, 0, 180), -80)
            self.draw_center(f"Difficulty: {self.diff_name}", self.font, TEXT_COLOR, -20)
            self.draw_center(f"High Score: {self.high_scores.get(self.diff_name,0)}", self.font, (0, 255, 200), 10)
            self.draw_center("Press any key to start the heist", self.font, (220, 220, 220), 60)
            pygame.display.flip()
            self.clock.tick(FPS)

    def play_loop(self):
        while self.state == "play":
            dt = self.clock.tick(FPS) / 1000.0
            emp_active = time.time() < self.emp_end_time

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_e and self.emp_available:
                        self.emp_available = False
                        self.emp_end_time = time.time() + 3
                        if "emp" in self.sounds: self.sounds["emp"].play()
                        self.emit_sound(self.player.pos, 120)  # EMP sound
                    if e.key == pygame.K_ESCAPE:
                        self.state = "menu"

            keys = pygame.key.get_pressed()
            self.player.crouch = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

            base_speed = CROUCH_SPEED if self.player.crouch else PLAYER_SPEED
            dx = (keys[pygame.K_d] - keys[pygame.K_a]) * base_speed
            dy = (keys[pygame.K_s] - keys[pygame.K_w]) * base_speed
            if dx != 0 and dy != 0:
                dx *= 0.7071
                dy *= 0.7071

            prev_pos = self.player.pos.copy()
            self.player.move(dx, dy, self.walls)

            # sound from running (only if not crouching)
            if not self.player.crouch and (self.player.pos - prev_pos).length() > 0.5:
                self.emit_sound(self.player.pos, 130)

            seen = False
            for g in self.guards:
                g.update(self.player.pos if g.alert else None)
                if g.sees_player(self.player, self.walls, emp_active):
                    seen = True
                    if not g.alert:
                        g.alert = True
                        g.alert_timer = 2.5
                        g.alert_nearby(self.guards)
                    # small camera shake when spotted
                    self.screen_shake = 6

            # detection logic
            if seen:
                if self.player.crouch:
                    self.detect_meter += 0.8 / FPS
                else:
                    self.detect_meter += 1.8 / FPS
            else:
                self.detect_meter = max(0.0, self.detect_meter - 1.0 / FPS)

            if self.detect_meter >= self.diff_settings["detect"]:
                if "alarm" in self.sounds: self.sounds["alarm"].play()
                self.state = "caught"

            # treasure collection
            for t in self.treasures[:]:
                if self.player.rect.colliderect(t):
                    self.treasures.remove(t)
                    if "collect" in self.sounds: self.sounds["collect"].play()
                    # treasure sound / particles
                    for _ in range(15):
                        vel = pygame.Vector2(random.uniform(-1,1), random.uniform(-1,1)) * 2
                        self.particles.append(Particle(self.player.pos, vel, (255,255,0)))

            # keys
            for krect in self.keys[:]:
                if self.player.rect.colliderect(krect):
                    self.keys.remove(krect)
                    self.has_key = True
                    # unlock all doors (remove from walls)
                    for d in self.doors:
                        if d in self.walls:
                            self.walls.remove(d)
                    if "collect" in self.sounds: self.sounds["collect"].play()

            # powerups
            for p in self.powerups[:]:
                if self.player.rect.colliderect(p["rect"]):
                    if p["type"] == "speed":
                        self.player.speed_boost = 1.8
                        self.player.speed_end = time.time() + 5
                    # could add invisibility, etc. later
                    self.powerups.remove(p)
                    if "collect" in self.sounds: self.sounds["collect"].play()

            # time limit
            elapsed = time.time() - self.start_time
            if elapsed > self.time_limit:
                if "alarm" in self.sounds: self.sounds["alarm"].play()
                self.state = "gameover"

            # exit condition: all treasures collected + exit reached
            if self.exit_rect and not self.treasures and self.player.rect.colliderect(self.exit_rect):
                # scoring: based on remaining time and difficulty
                remaining = max(0, self.time_limit - elapsed)
                gained = int(1000 + remaining * 5 - self.detect_meter * 50)
                self.score += max(0, gained)
                if "win" in self.sounds: self.sounds["win"].play()
                self.next_level_or_finish()
                return

            self.update_particles()
            self.draw(emp_active)

    def next_level_or_finish(self):
        if self.level_index < len(LEVELS) - 1:
            self.level_index += 1
            self.load_level()
            self.state = "play"
        else:
            # update high score
            prev = self.high_scores.get(self.diff_name, 0)
            if self.score > prev:
                self.high_scores[self.diff_name] = self.score
                self.save_high_scores()
            self.state = "gameover"

    def caught_loop(self):
        while self.state == "caught":
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    self.load_level()
                    self.state = "play"

            self.screen.fill(BG)
            self.draw_center("CAUGHT BY SECURITY 🚨", self.big, (255, 80, 80), -40)
            self.draw_center("Press any key to retry this level", self.font, TEXT_COLOR, 20)
            pygame.display.flip()
            self.clock.tick(FPS)

    def win_loop(self):
        # unused – we directly go via next_level_or_finish
        pass

    def gameover_loop(self):
        while self.state == "gameover":
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    # back to difficulty select
                    self.score = 0
                    self.level_index = 0
                    self.state = "difficulty"

            self.screen.fill(BG)
            self.draw_center("HEIST COMPLETE", self.big, (0, 255, 160), -60)
            self.draw_center(f"Total Score: {self.score}", self.font, TEXT_COLOR, 0)
            self.draw_center(f"High Score ({self.diff_name}): {self.high_scores.get(self.diff_name,0)}",
                             self.font, (0,255,200), 30)
            self.draw_center("Press any key to go back to difficulty menu", self.font, (220,220,220), 70)
            pygame.display.flip()
            self.clock.tick(FPS)

    # ----------------- DRAWING & HUD -----------------

    def update_particles(self):
        for p in self.particles[:]:
            p.update()
            if not p.is_alive():
                self.particles.remove(p)

    def draw(self, emp_active):
        # render to scene surface for screen shake
        scene = pygame.Surface((WIDTH, HEIGHT))
        scene.fill(BG)

        # grid
        for x in range(0, WIDTH, TILE):
            pygame.draw.line(scene, GRID, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, TILE):
            pygame.draw.line(scene, GRID, (0, y), (WIDTH, y))

        # walls & doors
        for w in self.walls:
            pygame.draw.rect(scene, WALL, w)
        for d in self.doors:
            pygame.draw.rect(scene, DOOR_COLOR, d)

        # exit
        if self.exit_rect:
            pygame.draw.rect(scene, EXIT_COLOR, self.exit_rect)

        # treasures
        for t in self.treasures:
            pygame.draw.rect(scene, TREASURE_COLOR, t)

        # keys
        for k in self.keys:
            pygame.draw.rect(scene, KEY_COLOR, k)

        # powerups
        for p in self.powerups:
            pygame.draw.rect(scene, POWERUP_COLOR, p["rect"])

        # guards & vision
        for g in self.guards:
            g.draw(scene)

        # player
        self.player.draw(scene)

        # particles
        for p in self.particles:
            p.draw(scene)

        # apply screen shake
        if self.screen_shake > 0:
            offset_x = random.randint(-self.screen_shake, self.screen_shake)
            offset_y = random.randint(-self.screen_shake, self.screen_shake)
            self.screen_shake = max(0, self.screen_shake - 1)
        else:
            offset_x = offset_y = 0

        self.screen.blit(scene, (offset_x, offset_y))

        # HUD overlay
        # detection bar
        pygame.draw.rect(self.screen, (60, 0, 0), (20, 20, 200, 16), border_radius=4)
        ratio = min(1.0, self.detect_meter / self.diff_settings["detect"])
        pygame.draw.rect(self.screen, (255, 0, 0), (20, 20, 200 * ratio, 16), border_radius=4)

        # time left
        elapsed = time.time() - self.start_time
        remaining = max(0, int(self.time_limit - elapsed))
        time_text = f"Time: {remaining}s"
        self.screen.blit(self.font.render(time_text, True, TEXT_COLOR), (20, 45))

        # level & difficulty
        top_info = f"Level {self.level_index + 1}/{len(LEVELS)} | {self.diff_name}"
        self.screen.blit(self.font.render(top_info, True, TEXT_COLOR), (20, 70))

        # objectives info
        obj = f"Treasures left: {len(self.treasures)}"
        if self.keys:
            obj += " | Key: ❌"
        elif self.has_key:
            obj += " | Key: ✅"
        self.screen.blit(self.font.render(obj, True, (0, 255, 200)), (20, 95))

        # EMP info
        emp_text = "EMP: ACTIVE ⚡" if emp_active else f"EMP: {'READY' if self.emp_available else 'USED / N/A'}"
        self.screen.blit(self.font.render(emp_text, True, TEXT_COLOR), (20, 120))

        # controls
        controls = "Controls: WASD move | SHIFT crouch | E EMP | ESC menu"
        self.screen.blit(self.small.render(controls, True, (200, 200, 200)), (20, HEIGHT - 30))

        pygame.display.flip()

    def draw_center(self, text, font, color, offset_y):
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + offset_y))
        self.screen.blit(surf, rect)

# -------------------- ENTRY POINT --------------------

if __name__ == "__main__":
    Game().run()
