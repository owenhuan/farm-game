import pygame
import time
import math

pygame.init()

# Constants
WIDTH, HEIGHT = 800, 700
TILE_SIZE = 64
GRID_SIZE = 7
FARM_Y_OFFSET = 120
SHOP_HEIGHT = 80
COLLAPSED_HEIGHT = 30
MENU_HEIGHT = 40
MUSIC_VOLUMES = [0.0, 0.25, 0.5, 0.75, 1.0]  # Keep 0.0 but skip it
music_volume_index = 1
SCORE_FILE = "scores.txt"

# Colors / palette
SKY_COLOR = (130, 195, 255)
GROUND_COLOR = (90, 175, 100)
SUN_COLOR = (255, 245, 170)
GRASS_GREEN = (76, 175, 80)
BROWN = (120, 72, 40)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SHOP_BG = (239, 228, 176)
SHOP_HOVER = (255, 243, 200)
RED = (255, 100, 100)
INSTRUCTIONS_BG = (250, 245, 235)
PAUSE_COLOR = (255, 215, 0)

# Fonts
timer_font_small = pygame.font.SysFont('arial', 12, bold=True)
timer_font_day = pygame.font.SysFont('arial', 20, bold=True)
font = pygame.font.SysFont('arial', 14)
small_font = pygame.font.SysFont('arial', 12)
big_font = pygame.font.SysFont('arial', 19)

#menu
MENU_BUTTONS = {
    "Pause": pygame.Rect(10, 5, 70, 30),  
    "Help": pygame.Rect(90, 5, 70, 30),
    "Quit": pygame.Rect(170, 5, 70, 30),
    "Music": pygame.Rect(250, 5, 80, 30),
    "Vol": pygame.Rect(340, 5, 90, 30),
    "Rank": pygame.Rect(WIDTH - 100, 5, 90, 30),
}

# Plant growth shapes and colors
PLANT_SHAPES = {
    "corn": {"seed": (139, 69, 19), "sprout": (0, 150, 0), "ready": (255, 235, 59)},
    "watermelon": {"seed": (80, 40, 20), "sprout": (6, 87, 15), "ready": (200, 0, 50)},
    "pumpkin": {"seed": (100, 60, 20), "sprout": (20, 140, 0), "ready": (255, 140, 0)},
    "tomato": {"seed": (120, 70, 30), "sprout": (0, 130, 20), "ready": (220, 20, 60)},
    "grape": {"seed": (60, 30, 10), "sprout": (10, 120, 10), "ready": (128, 0, 128)},
    "super": {"seed": (100, 100, 100), "sprout": (100, 200, 255), "ready": (255, 255, 0)}
}

# Shop costs (Super seed cost reduced to $20)
SHOP_COSTS = {"corn": 5, "watermelon": 7, "pumpkin": 8, "tomato": 10, "grape": 12, "super": 20}

# Growth times (seconds)
GROWTH_TIMES = {
    "corn": {"seed_to_sprout": 8, "sprout_to_ready": 8, "harvest": 6},
    "watermelon": {"seed_to_sprout": 11, "sprout_to_ready": 11, "harvest": 12},
    "pumpkin": {"seed_to_sprout": 14, "sprout_to_ready": 14, "harvest": 15},
    "tomato": {"seed_to_sprout": 12, "sprout_to_ready": 12, "harvest": 18},
    "grape": {"seed_to_sprout": 17, "sprout_to_ready": 17, "harvest": 20},
    "super": {"seed_to_sprout": 20, "sprout_to_ready": 20, "harvest": 50}  
}

SEED_LETTERS = ["C", "W", "P", "T", "G", "S"]

# Initialize display
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Planting Game - Farm & Harvest (ALL FIXES IMPLEMENTED)")
clock = pygame.time.Clock()

# Pre-render static text
SHOP_TITLE = big_font.render("SHOP", True, BLACK)
TOGGLE_TEXT = big_font.render("S", True, BLACK)
HELP_TEXT = big_font.render("?", True, BLACK)
HELP_BIG_TEXT = big_font.render("?", True, BLACK)
PAUSE_TEXT = big_font.render("||", True, BLACK)
PAUSE_ON_TEXT = big_font.render("▶", True, BLACK)
CLOSE_TEXT = font.render("X", True, WHITE)
REPLAY_TEXT = big_font.render("REPLAY", True, WHITE)
QUIT_TEXT = big_font.render("QUIT", True, WHITE)
GAME_OVER_TITLE = big_font.render("GAME OVER", True, WHITE)
YOU_WIN_TITLE = big_font.render("YOU WIN!", True, (0, 255, 0))
INSTRUCTIONS_TITLE = big_font.render("GAME INSTRUCTIONS", True, BLACK)

# Game state - Consistent 15 starting coins
coins = 500
corn_seeds = watermelon_seeds = pumpkin_seeds = tomato_seeds = grape_seeds = super_seeds = 0
crops = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
plant_time = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

# UI state
shop_collapsed = False
show_instructions = False
game_won = False
game_over = False
show_game_over = False
is_paused = False
music_volume_index = 2  # corresponds to 0.5 in MUSIC_VOLUMES
is_music_on = True
entering_name = False
player_name = ""
score_saved = False
scoreboard = []  # list of (name, score)
player_rank = None
show_scoreboard = False

# Day system - 8 days (0-7)
DAY_DURATION = 2
day_start_time = time.time()
current_day = 0
daily_start_coins = 15
daily_quotas = [20, 30, 50, 80, 120, 170, 230]

# Cached surfaces
coins_surface = day_surface = quota_surface = seeds_surface = None
seed_count_surfaces = [None] * 6
day_timer_surface = None

#load background music
pygame.mixer.init()
pygame.mixer.music.load("background.mp3")  # your file name
pygame.mixer.music.play(-1)  # -1 = loop forever
pygame.mixer.music.set_volume(MUSIC_VOLUMES[music_volume_index])


def load_scores():
    scores = []
    try:
        with open(SCORE_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) != 2:
                    continue
                name, score_str = parts
                try:
                    score = int(score_str)
                except ValueError:
                    continue
                scores.append((name, score))
    except FileNotFoundError:
        pass
    return scores


def save_score_and_rank(name, score):
    scores = load_scores()
    scores.append((name, score))
    # Sort descending by score
    scores.sort(key=lambda s: s[1], reverse=True)
    # Write back to file
    with open(SCORE_FILE, "w") as f:
        for n, sc in scores:
            f.write(f"{n},{sc}\n")
    # Find this player's rank
    rank = None
    for i, (n, sc) in enumerate(scores):
        if n == name and sc == score:
            rank = i + 1
            break
    return scores, rank


def prepare_win_score_prompt():
    """Prepare high-score info when the player wins.

    Decides if the player is eligible for top-5 and, if so,
    enables name entry. Also loads the existing scoreboard for
    display on the win popup.
    """
    global entering_name, player_name, score_saved, scoreboard, player_rank

    existing_scores = load_scores()

    # Compute potential rank if this score were added
    marker_name = "__CURRENT__"
    temp = existing_scores + [(marker_name, coins)]
    temp.sort(key=lambda s: s[1], reverse=True)

    potential_rank = None
    for i, (n, sc) in enumerate(temp):
        if n == marker_name and sc == coins:
            potential_rank = i + 1
            break

    scoreboard = existing_scores  # show existing scores
    player_name = ""
    score_saved = False
    player_rank = potential_rank

    # Only allow saving if player would be in top 5
    if potential_rank is not None and potential_rank <= 5:
        entering_name = True
    else:
        entering_name = False


def get_shop_buttons():
    if shop_collapsed:
        return {
            'toggle': pygame.Rect(10, 5 + MENU_HEIGHT, 20, 20),
            'coins': pygame.Rect(35, 2 + MENU_HEIGHT, 50, 26),
            'day': pygame.Rect(90, 2 + MENU_HEIGHT, 45, 26),
            'quota': pygame.Rect(140, 2 + MENU_HEIGHT, 45, 26),
            'timer': pygame.Rect(195, 2 + MENU_HEIGHT, 55, 26),
            'seeds': pygame.Rect(255, 2 + MENU_HEIGHT, 45, 26)
        }

    return {
        'corn 5$': pygame.Rect(10, 15 + MENU_HEIGHT, 70, 50),
        'watermelon 7$': pygame.Rect(85, 15 + MENU_HEIGHT, 70, 50),
        'pumpkin 8$': pygame.Rect(160, 15 + MENU_HEIGHT, 70, 50),
        'tomato 10$': pygame.Rect(235, 15 + MENU_HEIGHT, 70, 50),
        'grape 12$': pygame.Rect(310, 15 + MENU_HEIGHT, 70, 50),
        'super 20$': pygame.Rect(385, 15 + MENU_HEIGHT, 70, 50),
        'coins': pygame.Rect(460, 15 + MENU_HEIGHT, 70, 25),
        'day': pygame.Rect(535, 15 + MENU_HEIGHT, 45, 25),
        'quota': pygame.Rect(585, 15 + MENU_HEIGHT, 45, 25),
        'timer': pygame.Rect(635, 15 + MENU_HEIGHT, 70, 25),
        'seeds': pygame.Rect(710, 15 + MENU_HEIGHT, 55, 25)
    }


def check_daily_quota():
    global daily_start_coins, current_day, game_over, game_won, show_game_over
    time_elapsed = time.time() - day_start_time
    days_passed = int(time_elapsed // DAY_DURATION)
    max_day_index = len(daily_quotas) - 1

    # Only act when we've advanced past the current_day boundary
    if days_passed > current_day:
        print(f"Day {current_day} ended. Checking quota...")
        if current_day <= max_day_index:
            required = daily_quotas[current_day]
            # Check TOTAL coins vs quota (not earned)
            if coins >= required:
                print(f"✓ Day {current_day} PASSED! (Coins: {coins} >= {required})")
                if current_day == max_day_index:
                    # Last day passed -> WIN
                    game_won = True
                    show_game_over = True
                    # Prepare win popup + potential ranking info
                    prepare_win_score_prompt()
                else:
                    # Move to next day
                    current_day += 1
                    daily_start_coins = coins
            else:
                # Failed quota
                game_over = True
                show_game_over = True
                print(f"✗ Day {current_day} FAILED! (Coins: {coins} < {required})")
                # On failure, just load existing scores; no name entry
                from_scores = load_scores()
                globals()["scoreboard"] = from_scores
                globals()["entering_name"] = False
                globals()["player_name"] = ""
                globals()["score_saved"] = False
                globals()["player_rank"] = None
        return True
    return False


def update_cached_text():
    global coins_surface, day_surface, quota_surface, seeds_surface, seed_count_surfaces, day_timer_surface
    
    coins_surface = font.render(f"Coins:{coins}", True, BLACK)
    day_surface = font.render(f"Day:{current_day + 1}", True, BLACK)
    
    if current_day < len(daily_quotas):
        quota_surface = font.render(f"Q:{daily_quotas[current_day]}", True, BLACK)
    else:
        quota_surface = font.render("WIN!", True, (0, 255, 0))
    
    total_seeds = corn_seeds + watermelon_seeds + pumpkin_seeds + tomato_seeds + grape_seeds + super_seeds
    seeds_surface = font.render(f"Seeds:{total_seeds}", True, BLACK)
    
    seed_counts = [corn_seeds, watermelon_seeds, pumpkin_seeds, tomato_seeds, grape_seeds, super_seeds]
    for i, count in enumerate(seed_counts):
        seed_count_surfaces[i] = font.render(str(count), True, RED)
    
    # Pause-safe timer
    if is_paused:
        day_timer_surface = timer_font_day.render("PAUSED", True, (255, 100, 100))
    else:
        time_left = max(0, DAY_DURATION - ((time.time() - day_start_time) % DAY_DURATION))
        minutes, seconds = divmod(int(time_left), 60)
        day_timer_surface = timer_font_day.render(f"{minutes:02d}:{seconds:02d}", True, WHITE)



def draw_growth_stage(tile_x, tile_y, crop_type, state):
    center_x, center_y = tile_x + TILE_SIZE // 2, tile_y + TILE_SIZE // 2
    colors = PLANT_SHAPES[crop_type]
    
    if state == "seed":
        if crop_type == "corn":
            pygame.draw.rect(WIN, colors["seed"], (center_x-14, center_y-6, 28, 12))
            pygame.draw.rect(WIN, BLACK, (center_x-14, center_y-6, 28, 12), 2)
        elif crop_type == "watermelon":
            pygame.draw.ellipse(WIN, colors["seed"], (center_x-16, center_y-6, 32, 12))
            pygame.draw.ellipse(WIN, BLACK, (center_x-16, center_y-6, 32, 12), 2)
        elif crop_type == "pumpkin":
            pts = [(center_x, center_y-10), (center_x-12, center_y+10), (center_x+12, center_y+10), (center_x, center_y-5)]
            pygame.draw.polygon(WIN, colors["seed"], pts)
            pygame.draw.polygon(WIN, BLACK, pts, 2)
        elif crop_type == "tomato":
            pygame.draw.circle(WIN, colors["seed"], (center_x, center_y), 8)
            pygame.draw.circle(WIN, colors["seed"], (center_x-12, center_y+4), 6)
            pygame.draw.circle(WIN, BLACK, (center_x, center_y), 8, 2)
        elif crop_type == "grape":
            pygame.draw.circle(WIN, colors["seed"], (center_x, center_y), 6)
            pygame.draw.circle(WIN, colors["seed"], (center_x+10, center_y-4), 5)
            pygame.draw.circle(WIN, BLACK, (center_x, center_y), 6, 2)
        else:  # super
            pts = [(center_x, center_y-12), (center_x-12, center_y), (center_x, center_y+12), (center_x+12, center_y)]
            pygame.draw.polygon(WIN, colors["seed"], pts)
            pygame.draw.polygon(WIN, BLACK, pts, 2)
    
    elif state == "sprout":
        if crop_type == "corn":
            pygame.draw.rect(WIN, colors["sprout"], (center_x-3, center_y, 6, 25))
            pygame.draw.ellipse(WIN, colors["sprout"], (center_x-12, center_y-8, 18, 10))
        elif crop_type == "watermelon":
            pygame.draw.circle(WIN, colors["sprout"], (center_x, center_y+15), 10)
            pygame.draw.line(WIN, colors["sprout"], (center_x, center_y+5), (center_x+15, center_y-10), 6)
        elif crop_type == "pumpkin":
            pygame.draw.rect(WIN, colors["sprout"], (center_x-6, center_y+2, 12, 22))
            pygame.draw.circle(WIN, (255, 200, 0), (center_x, center_y-12), 5)
        elif crop_type == "tomato":
            pygame.draw.line(WIN, colors["sprout"], (center_x, center_y+12), (center_x, center_y-15), 5)
            pygame.draw.ellipse(WIN, colors["sprout"], (center_x-15, center_y-5, 16, 12))
            pygame.draw.ellipse(WIN, colors["sprout"], (center_x+2, center_y-3, 16, 12))
        elif crop_type == "grape":
            pygame.draw.line(WIN, colors["sprout"], (center_x-8, center_y+10), (center_x+12, center_y-12), 4)
            pygame.draw.line(WIN, colors["sprout"], (center_x+2, center_y+8), (center_x-10, center_y-8), 4)
        else:
            pygame.draw.circle(WIN, colors["sprout"], (center_x, center_y+10), 8)
            pygame.draw.line(WIN, colors["sprout"], (center_x-12, center_y-10), (center_x+12, center_y+10), 6)
    
    elif state == "ready":
        if crop_type == "corn":
            pygame.draw.ellipse(WIN, colors["ready"], (center_x-18, center_y-15, 36, 30))
            pygame.draw.line(WIN, (139, 69, 19), (center_x-15, center_y-20), (center_x+15, center_y+5), 3)
        elif crop_type == "watermelon":
            pygame.draw.ellipse(WIN, colors["ready"], (center_x-20, center_y-10, 40, 20))
            pygame.draw.arc(WIN, BLACK, (center_x-20, center_y-10, 40, 20), 0, 3.14, 3)
        elif crop_type == "pumpkin":
            pygame.draw.circle(WIN, colors["ready"], (center_x, center_y), 22)
            pygame.draw.line(WIN, (100, 60, 20), (center_x, center_y-22), (center_x+8, center_y-18), 4)
        elif crop_type == "tomato":
            pygame.draw.circle(WIN, colors["ready"], (center_x, center_y+2), 20)
            pygame.draw.polygon(WIN, (0, 150, 0), [(center_x-8, center_y-18), (center_x+8, center_y-18), (center_x, center_y-28)])
        elif crop_type == "grape":
            pygame.draw.circle(WIN, colors["ready"], (center_x, center_y), 18)
            pygame.draw.circle(WIN, colors["ready"], (center_x+12, center_y-6), 12)
            pygame.draw.circle(WIN, colors["ready"], (center_x-12, center_y+6), 12)
        else:
            pts = [
                (center_x, center_y-25), (center_x+8, center_y-8),
                (center_x+25, center_y), (center_x+8, center_y+8),
                (center_x, center_y+25), (center_x-8, center_y+8),
                (center_x-25, center_y), (center_x-8, center_y-8)
            ]
            pygame.draw.polygon(WIN, colors["ready"], pts)
            pygame.draw.polygon(WIN, WHITE, pts, 3)

def draw_crop_timer(tile_x, tile_y, plant_time_val, crop_type, row, col):
    # Don't show timers when paused
    if is_paused:
        return
    
    current_time = time.time()
    time_elapsed = current_time - plant_time_val
    growth_data = GROWTH_TIMES[crop_type]
    state = crops[row][col]["state"]
    
    if state == "ready":
        reward = growth_data["harvest"]
        text = timer_font_small.render(f"${reward}", True, (0, 255, 0))
        WIN.blit(text, (tile_x + TILE_SIZE//2 - text.get_width()//2, tile_y + 5))
        return
    
    if state == "seed":
        time_remaining = growth_data["seed_to_sprout"] - time_elapsed
        stage = "S"
    elif state == "sprout":
        time_remaining = growth_data["sprout_to_ready"] - time_elapsed
        stage = "R"
    else:
        return
    
    if time_remaining > 0:
        seconds = max(0, int(time_remaining))
        text = timer_font_small.render(f"{stage}:{seconds}s", True, WHITE)
        bg = pygame.Surface((text.get_width() + 6, text.get_height() + 4))
        bg.set_alpha(220)
        bg.fill((50, 50, 50))
        text_x = tile_x + TILE_SIZE//2 - text.get_width()//2
        WIN.blit(bg, (text_x - 1, tile_y + 4))
        WIN.blit(text, (text_x, tile_y + 5))


def draw_background():
    # Sky
    WIN.fill(SKY_COLOR)
    # Ground / horizon
    pygame.draw.rect(WIN, GROUND_COLOR, (0, HEIGHT // 2 + 40, WIDTH, HEIGHT // 2 - 40))
    # Sun in top-right
    pygame.draw.circle(WIN, SUN_COLOR, (WIDTH - 80, 80), 40)
    
def draw_menu_bar():
    # background bar
    pygame.draw.rect(WIN, (180, 180, 180), (0, 0, WIDTH, MENU_HEIGHT))
    pygame.draw.rect(WIN, BLACK, (0, 0, WIDTH, MENU_HEIGHT), 3)

    mouse_pos = pygame.mouse.get_pos()
    for label, rect in MENU_BUTTONS.items():
        # Base colors
        if rect.collidepoint(mouse_pos):
            color = SHOP_HOVER
        else:
            color = SHOP_BG

        # MUSIC BUTTON: Dim when music off
        if label == "Music" and not is_music_on:
            color = (170, 170, 170)

        # Special styling for Pause button
        if label == "Pause":
            # Running: bright gold; Paused: softer grey-gold
            color = (255, 230, 120) if not is_paused else (210, 210, 210)

        pygame.draw.rect(WIN, color, rect, border_radius=6)
        pygame.draw.rect(WIN, BLACK, rect, 2, border_radius=6)

        if label == "Vol":
            # Shows ONLY 25%, 50%, 75%, 100% (no 0%)
            volume_percent = int(MUSIC_VOLUMES[music_volume_index] * 100)
            display = f"Vol {volume_percent}%"
            text_surf = font.render(display, True, BLACK)
            WIN.blit(text_surf, text_surf.get_rect(center=rect.center))
        elif label == "Pause":
            # Custom icons: || when running, triangle ▶ when paused
            cx, cy = rect.center
            if not is_paused:
                # Two pause bars
                bar_w = 6
                bar_h = rect.height - 10
                gap = 4
                left_bar = pygame.Rect(cx - bar_w - gap//2, cy - bar_h//2, bar_w, bar_h)
                right_bar = pygame.Rect(cx + gap//2, cy - bar_h//2, bar_w, bar_h)
                pygame.draw.rect(WIN, BLACK, left_bar)
                pygame.draw.rect(WIN, BLACK, right_bar)
            else:
                # Sideways play triangle
                tri_w = rect.width // 3
                tri_h = rect.height - 10
                points = [
                    (cx - tri_w//3, cy - tri_h//2),  # top-left
                    (cx + tri_w*2//3, cy),            # middle-right
                    (cx - tri_w//3, cy + tri_h//2),  # bottom-left
                ]
                pygame.draw.polygon(WIN, BLACK, points)
        else:
            display = label
            text_surf = font.render(display, True, BLACK)
            WIN.blit(text_surf, text_surf.get_rect(center=rect.center))


def draw_shop():
    buttons = get_shop_buttons()
    mouse_pos = pygame.mouse.get_pos()
    height = COLLAPSED_HEIGHT if shop_collapsed else SHOP_HEIGHT
    
    # Draw shop below the top menu bar
    pygame.draw.rect(WIN, SHOP_BG, (0, MENU_HEIGHT, WIDTH, height))
    pygame.draw.rect(WIN, BROWN, (0, MENU_HEIGHT, WIDTH, height), 5)
    
    if shop_collapsed:
        btn = buttons['toggle']
        pygame.draw.rect(WIN, SHOP_HOVER if btn.collidepoint(mouse_pos) else SHOP_BG, btn)
        pygame.draw.rect(WIN, BROWN, btn, 2)
        WIN.blit(TOGGLE_TEXT, TOGGLE_TEXT.get_rect(center=btn.center))
        
        for name in ['coins', 'day', 'quota', 'timer', 'seeds']:
            btn = buttons[name]
            color = SHOP_HOVER if btn.collidepoint(mouse_pos) else SHOP_BG
            pygame.draw.rect(WIN, color, btn)
            pygame.draw.rect(WIN, BROWN, btn, 2)
            text = {
                'coins': coins_surface,
                'day': day_surface,
                'quota': quota_surface,
                'timer': day_timer_surface,
                'seeds': seeds_surface
            }[name]
            WIN.blit(text, text.get_rect(center=btn.center))
        
        # Seed letters with counts
        for i, letter in enumerate(SEED_LETTERS):
            x = 355 + i * 22
            WIN.blit(font.render(letter, True, BLACK), (x + 2, 3 + MENU_HEIGHT))
            if seed_count_surfaces[i]:
                WIN.blit(seed_count_surfaces[i], (x + 2, 18 + MENU_HEIGHT))
    
    else:
        # Stats buttons (coins, day, quota, timer, seeds)
        for name in ['coins', 'day', 'quota', 'timer', 'seeds']:
            btn = buttons[name]
            color = SHOP_HOVER if btn.collidepoint(mouse_pos) else SHOP_BG
            pygame.draw.rect(WIN, color, btn)
            pygame.draw.rect(WIN, BROWN, btn, 2)
            text = {
                'coins': coins_surface,
                'day': day_surface,
                'quota': quota_surface,
                'timer': day_timer_surface,
                'seeds': seeds_surface
            }[name]
            WIN.blit(text, text.get_rect(center=btn.center))
        
        # Seed buttons: clearer layout for name, price, and count
        seeds = [
            ("corn", 5), ("watermelon", 7), ("pumpkin", 8), 
            ("tomato", 10), ("grape", 12), ("super", 20)
        ]
        
        for i, (seed_type, cost) in enumerate(seeds):
            btn = buttons[f"{seed_type} {cost}$"]
            color = SHOP_HOVER if btn.collidepoint(mouse_pos) else SHOP_BG
            pygame.draw.rect(WIN, color, btn)
            pygame.draw.rect(WIN, BROWN, btn, 4)  # THICK 4px BORDER
            
            # Use slightly smaller font so text isn't squeezed
            if seed_type == "watermelon":
                name_label = "Watermelon"
            else:
                name_label = seed_type.capitalize()

            name_text = small_font.render(name_label, True, BLACK)
            price_text = small_font.render(f"${cost}", True, (0, 150, 0))
            count = globals()[f"{seed_type}_seeds"]
            count_text = small_font.render(f"x{count}", True, RED)
            
            # Comfortable vertical spacing inside each 50px-tall button
            name_y = btn.y + 4  # Top label
            price_y = btn.centery - price_text.get_height()//2  # Middle price
            count_y = btn.bottom - count_text.get_height() - 4  # Bottom count
            
            WIN.blit(name_text, (btn.centerx - name_text.get_width()//2, name_y))
            WIN.blit(price_text, (btn.centerx - price_text.get_width()//2, price_y))
            WIN.blit(count_text, (btn.centerx - count_text.get_width()//2, count_y))



def draw_end_screen():
    global scoreboard, player_rank, score_saved
    if not show_game_over:
        return
    
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 150, 0) if game_won else (100, 0, 0))
    WIN.blit(overlay, (0, 0))
    
    panel = pygame.Rect(150, 200, 500, 350)
    color = (50, 200, 50) if game_won else (200, 50, 50)
    pygame.draw.rect(WIN, color, panel)
    pygame.draw.rect(WIN, BLACK if game_won else RED, panel, 5)
    
    title = YOU_WIN_TITLE if game_won else GAME_OVER_TITLE
    WIN.blit(title, (panel.centerx - title.get_width()//2, panel.y + 20))
    
    if game_won:
        WIN.blit(big_font.render(f"FINAL SCORE: {coins} coins!", True, WHITE), (panel.x + 30, panel.y + 80))
        WIN.blit(font.render("All 7 days completed!", True, WHITE), (panel.x + 30, panel.y + 120))
    else:
        req = daily_quotas[current_day]
        WIN.blit(big_font.render(f"DAY {current_day + 1} FAILED", True, WHITE), (panel.x + 30, panel.y + 80))
        WIN.blit(font.render(f"Needed: {req} coins", True, WHITE), (panel.x + 30, panel.y + 120))
        WIN.blit(font.render(f"Have: {coins} coins", True, WHITE), (panel.x + 30, panel.y + 150))  

    # Show rank if saved
    if score_saved and player_rank is not None:
        rank_text = font.render(f"Your rank: #{player_rank}", True, WHITE)
        WIN.blit(rank_text, (panel.x + 30, panel.y + 180))

    # High score table (top 5)
    if scoreboard:
        hs_title = font.render("High Scores:", True, WHITE)
        WIN.blit(hs_title, (panel.x + 260, panel.y + 80))
        for i, (name, sc) in enumerate(scoreboard[:5]):
            entry = font.render(f"{i+1}. {name} - {sc}", True, WHITE)
            WIN.blit(entry, (panel.x + 260, panel.y + 110 + i * 20))

    
    replay_rect = pygame.Rect(panel.x + 50, panel.y + 220, 190, 60)
    pygame.draw.rect(WIN, (50, 200, 50), replay_rect)
    pygame.draw.rect(WIN, BLACK, replay_rect, 3)
    WIN.blit(REPLAY_TEXT, (replay_rect.centerx - REPLAY_TEXT.get_width()//2, replay_rect.centery - 10))
    
    quit_rect = pygame.Rect(panel.x + 260, panel.y + 220, 190, 60)
    pygame.draw.rect(WIN, RED, quit_rect)
    pygame.draw.rect(WIN, BLACK, quit_rect, 3)
    WIN.blit(QUIT_TEXT, (quit_rect.centerx - QUIT_TEXT.get_width()//2, quit_rect.centery - 10))


def draw_name_input():
    if not entering_name or score_saved:
        return
    box = pygame.Rect(200, 220, 400, 160)
    pygame.draw.rect(WIN, WHITE, box)
    pygame.draw.rect(WIN, BLACK, box, 3)
    title = big_font.render("Enter your name:", True, BLACK)
    WIN.blit(title, (box.centerx - title.get_width()//2, box.y + 20))
    display_name = player_name if player_name else "_"
    name_surf = big_font.render(display_name, True, BLACK)
    WIN.blit(name_surf, (box.centerx - name_surf.get_width()//2, box.y + 70))
    hint = font.render("Press Enter to save score", True, BLACK)
    WIN.blit(hint, (box.centerx - hint.get_width()//2, box.y + 120))


def draw_scoreboard_popup():
    if not show_scoreboard:
        return
    # Semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(160)
    overlay.fill(INSTRUCTIONS_BG)
    WIN.blit(overlay, (0, 0))

    panel = pygame.Rect(140, 120, 520, 440)
    pygame.draw.rect(WIN, WHITE, panel)
    pygame.draw.rect(WIN, BROWN, panel, 4)

    title = big_font.render("Ranking Board", True, BLACK)
    WIN.blit(title, (panel.centerx - title.get_width()//2, panel.y + 20))

    # Load latest scores if empty
    global scoreboard
    if not scoreboard:
        scoreboard = load_scores()

    # Show top 5
    header = font.render("Top 5 Players (by coins):", True, BLACK)
    WIN.blit(header, (panel.x + 20, panel.y + 70))

    if not scoreboard:
        empty = font.render("No scores yet.", True, BLACK)
        WIN.blit(empty, (panel.x + 20, panel.y + 100))
    else:
        for i, (name, sc) in enumerate(scoreboard[:5]):
            entry = font.render(f"{i+1}. {name} - {sc}", True, BLACK)
            WIN.blit(entry, (panel.x + 40, panel.y + 100 + i * 24))

    # Close button
    close_rect = pygame.Rect(panel.right - 35, panel.y + 15, 20, 20)
    pygame.draw.rect(WIN, RED, close_rect)
    pygame.draw.rect(WIN, BLACK, close_rect, 2)
    WIN.blit(CLOSE_TEXT, CLOSE_TEXT.get_rect(center=close_rect.center))

def get_farm_position():
    return (
        (WIDTH - GRID_SIZE * TILE_SIZE) // 2,
        MENU_HEIGHT + (COLLAPSED_HEIGHT if shop_collapsed else SHOP_HEIGHT) + FARM_Y_OFFSET
    )

def draw_farm():
    farm_x, farm_y = get_farm_position()
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            x, y = farm_x + col * TILE_SIZE, farm_y + row * TILE_SIZE
            # Grass base
            pygame.draw.rect(WIN, GRASS_GREEN, (x, y, TILE_SIZE, TILE_SIZE))
            # Soil patch for visual depth
            pygame.draw.rect(WIN, (166, 124, 82), (x + 8, y + 8, TILE_SIZE - 16, TILE_SIZE - 16))
            if crops[row][col]:
                draw_growth_stage(x, y, crops[row][col]["type"], crops[row][col]["state"])
                draw_crop_timer(x, y, plant_time[row][col], crops[row][col]["type"], row, col)
            pygame.draw.rect(WIN, BROWN, (x, y, TILE_SIZE, TILE_SIZE), 3)

def update_crops():
    current_time = time.time()
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if crops[row][col]:
                crop = crops[row][col]
                elapsed = current_time - plant_time[row][col]
                growth = GROWTH_TIMES[crop["type"]]
                if crop["state"] == "seed" and elapsed > growth["seed_to_sprout"]:
                    crop["state"] = "sprout"
                elif crop["state"] == "sprout" and elapsed > growth["sprout_to_ready"]:
                    crop["state"] = "ready"
def update_paused_text():
    global coins_surface, day_surface, quota_surface, seeds_surface, seed_count_surfaces, day_timer_surface, earned_today_surface
    
    coins_surface = font.render(f"Coins:{coins}", True, BLACK)
    day_surface = font.render(f"Day:{current_day + 1}", True, BLACK)
    
    if current_day < len(daily_quotas):
        quota_surface = font.render(f"Q:{daily_quotas[current_day]}", True, BLACK)
    else:
        quota_surface = font.render("WIN!", True, (0, 255, 0))
    
    earned_today = coins - daily_start_coins
    color = (0, 255, 0) if earned_today >= daily_quotas[min(current_day, len(daily_quotas)-1)] else RED
    earned_today_surface = font.render(f"E:{earned_today}", True, color)
    
    total_seeds = corn_seeds + watermelon_seeds + pumpkin_seeds + tomato_seeds + grape_seeds + super_seeds
    seeds_surface = font.render(f"Seeds:{total_seeds}", True, BLACK)
    
    seed_counts = [corn_seeds, watermelon_seeds, pumpkin_seeds, tomato_seeds, grape_seeds, super_seeds]
    for i, count in enumerate(seed_counts):
        seed_count_surfaces[i] = font.render(str(count), True, RED)
    
    #Freeze day timer when paused
    if is_paused:
        day_timer_surface = timer_font_day.render("PAUSED", True, (255, 100, 100))
    else:
        time_left = max(0, DAY_DURATION - ((time.time() - day_start_time) % DAY_DURATION))
        minutes, seconds = divmod(int(time_left), 60)
        day_timer_surface = timer_font_day.render(f"{minutes:02d}:{seconds:02d}", True, WHITE)

# MAIN LOOP 
run = True
while run:
    # Handle events FIRST
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.KEYDOWN:
            # Handle name entry first when game is over
            if entering_name and show_game_over:
                if event.key == pygame.K_RETURN:
                    if player_name.strip():
                        scoreboard, player_rank = save_score_and_rank(player_name.strip(), coins)
                        score_saved = True
                        entering_name = False
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                else:
                    if len(player_name) < 12 and event.unicode.isprintable():
                        player_name += event.unicode
                continue
            if event.key == pygame.K_ESCAPE:
                run = False
            elif event.key == pygame.K_s and not (show_game_over or show_instructions):
                shop_collapsed = not shop_collapsed
            elif event.key == pygame.K_h:
                show_instructions = not show_instructions
            elif show_game_over:
                if event.key == pygame.K_r:
                    # Reset game
                    coins = 15
                    daily_start_coins = 15
                    corn_seeds = watermelon_seeds = pumpkin_seeds = tomato_seeds = grape_seeds = super_seeds = 0
                    crops = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
                    plant_time = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
                    current_day = 0
                    day_start_time = time.time()
                    game_over = game_won = show_game_over = False
                    entering_name = False
                    score_saved = False
                    player_name = ""
                    player_rank = None
                elif event.key == pygame.K_q:
                    run = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            if show_game_over:
                panel = pygame.Rect(150, 200, 500, 350)
                if pygame.Rect(panel.x + 50, panel.y + 220, 190, 60).collidepoint(mx, my):
                    # Replay
                    coins = 15
                    daily_start_coins = 15
                    corn_seeds = watermelon_seeds = pumpkin_seeds = tomato_seeds = grape_seeds = super_seeds = 0
                    crops = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
                    plant_time = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
                    current_day = 0
                    day_start_time = time.time()
                    game_over = game_won = show_game_over = False
                    entering_name = False
                    score_saved = False
                    player_name = ""
                    player_rank = None
                elif pygame.Rect(panel.x + 260, panel.y + 220, 190, 60).collidepoint(mx, my):
                    run = False
                continue
            
            if show_instructions:
                close_rect = pygame.Rect(665, 160, 25, 25)
                if close_rect.collidepoint(mx, my):
                    show_instructions = False
                    continue

            # SCOREBOARD POPUP HANDLING
            if show_scoreboard:
                panel = pygame.Rect(140, 120, 520, 440)
                close_rect = pygame.Rect(panel.right - 35, panel.y + 15, 20, 20)
                if close_rect.collidepoint(mx, my):
                    show_scoreboard = False
                # Ignore other clicks when scoreboard is open
                continue
            
            # TOP MENU BAR HANDLING (Pause, Help, Quit, Music, Vol, Rank)
            if my < MENU_HEIGHT and not show_game_over and not show_instructions:
                if MENU_BUTTONS["Pause"].collidepoint(mx, my):
                    is_paused = not is_paused
                elif MENU_BUTTONS["Help"].collidepoint(mx, my):
                    show_instructions = True
                    show_scoreboard = False
                elif MENU_BUTTONS["Music"].collidepoint(mx, my):
                    if is_music_on:
                        pygame.mixer.music.pause()
                        is_music_on = False
                    else:
                        pygame.mixer.music.unpause()
                        is_music_on = True
                elif MENU_BUTTONS["Vol"].collidepoint(mx, my):
                    # FIXED: 25%→50%→75%→100%
                    music_volume_index = (music_volume_index + 1) % 4
                    pygame.mixer.music.set_volume(MUSIC_VOLUMES[music_volume_index])
                elif MENU_BUTTONS["Rank"].collidepoint(mx, my):
                    # Toggle ranking popup; hide instructions when showing it
                    show_scoreboard = not show_scoreboard
                    if show_scoreboard:
                        show_instructions = False
                        scoreboard = load_scores()
                elif MENU_BUTTONS["Quit"].collidepoint(mx, my):
                    run = False
                continue
            
            # SHOP BUTTONS (NO pause/help - moved to menu bar)
            if not show_instructions:
                shop_height = MENU_HEIGHT + (COLLAPSED_HEIGHT if shop_collapsed else SHOP_HEIGHT)
                if my < shop_height:
                    buttons = get_shop_buttons()
                    if shop_collapsed:
                        if buttons['toggle'].collidepoint(mx, my):
                            shop_collapsed = not shop_collapsed
                        # NO pause/help buttons here anymore
                    else:
                        # Seed buying (BLOCKED when paused)
                        if is_paused:
                            continue
                        seed_buttons = {
                            'corn': (buttons['corn 5$'], SHOP_COSTS["corn"]),
                            'watermelon': (buttons['watermelon 7$'], SHOP_COSTS["watermelon"]),
                            'pumpkin': (buttons['pumpkin 8$'], SHOP_COSTS["pumpkin"]),
                            'tomato': (buttons['tomato 10$'], SHOP_COSTS["tomato"]),
                            'grape': (buttons['grape 12$'], SHOP_COSTS["grape"]),
                            'super': (buttons['super 20$'], SHOP_COSTS["super"]),
                        }
                        for seed_name, (btn, cost) in seed_buttons.items():
                            if btn.collidepoint(mx, my) and coins >= cost:
                                globals()[f"{seed_name}_seeds"] += 1
                                coins -= cost
                                update_cached_text()
                                break
                        # NO pause/help buttons here anymore
                else:
                    # FARM PLANTING/HARVESTING
                    farm_x, farm_y = get_farm_position()
                    if (farm_x <= mx < farm_x + GRID_SIZE * TILE_SIZE and 
                        farm_y <= my < farm_y + GRID_SIZE * TILE_SIZE):
                        grid_x = (mx - farm_x) // TILE_SIZE
                        grid_y = (my - farm_y) // TILE_SIZE
                        if 0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE:
                            row, col = grid_y, grid_x
                            if crops[row][col] and crops[row][col]["state"] == "ready":
                                seed_type = crops[row][col]["type"]
                                coins += GROWTH_TIMES[seed_type]["harvest"]
                                crops[row][col] = None
                                update_cached_text()
                            elif crops[row][col] is None and not is_paused:
                                # Auto-plant cheapest seeds first
                                for seed_type, var_name in [
                                    ("corn", "corn_seeds"),
                                    ("watermelon", "watermelon_seeds"),
                                    ("pumpkin", "pumpkin_seeds"),
                                    ("tomato", "tomato_seeds"),
                                    ("grape", "grape_seeds"),
                                    ("super", "super_seeds"),
                                ]:
                                    if globals()[var_name] > 0:
                                        globals()[var_name] -= 1
                                        crops[row][col] = {"type": seed_type, "state": "seed"}
                                        plant_time[row][col] = time.time()
                                        update_cached_text()
                                        break
    
    # GAME LOGIC (PAUSED = STOPPED)
    if not is_paused and not show_game_over and not show_instructions:
        check_daily_quota()
        update_crops()
        update_cached_text()
    else:
        update_paused_text()
    
    # DRAW EVERYTHING
    draw_background()
    draw_menu_bar()
    if not show_game_over:
        draw_shop()
    draw_farm()
    draw_end_screen()
    draw_name_input()
    draw_scoreboard_popup()
    
    # Instructions overlay
    if show_instructions:
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(INSTRUCTIONS_BG)
        WIN.blit(overlay, (0, 0))
        panel = pygame.Rect(100, 150, 600, 450)
        pygame.draw.rect(WIN, WHITE, panel)
        pygame.draw.rect(WIN, BROWN, panel, 5)
        WIN.blit(INSTRUCTIONS_TITLE, (panel.x + 20, panel.y + 20))
        instructions = [
            "1. Buy seeds from SHOP buttons",
            "2. Click empty farm tiles to plant", 
            "3. Watch plants grow!",
            "4. Click READY crops ($ shown) to harvest",
            "5. MEET DAILY QUOTA or GAME OVER!",
            "6. S = toggle shop, H = help, ESC = quit",
            "7. ||/▶ = PAUSE (top menu!)",
            "",
            "Corn:8s=$6 | Watermelon:11s=$12 | Pumpkin:14s=$15",
            "Tomato:12s=$18 | Grape:17s=$20 | Super:20s=$50 ($20)",
            "",
            f"Day {current_day+1} quota: {daily_quotas[current_day]}"
        ]
        for i, text in enumerate(instructions):
            WIN.blit(font.render(text, True, BLACK), (panel.x + 20, panel.y + 70 + i * 18))
        
        close_rect = pygame.Rect(665, 160, 25, 25)
        pygame.draw.rect(WIN, RED, close_rect)
        pygame.draw.rect(WIN, BLACK, close_rect, 2)
        WIN.blit(CLOSE_TEXT, CLOSE_TEXT.get_rect(center=close_rect.center))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
