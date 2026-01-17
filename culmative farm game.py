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

# Colors
GRASS_GREEN = (34, 139, 34)
BROWN = (139, 69, 19)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SHOP_BG = (200, 180, 140)
SHOP_HOVER = (220, 200, 160)
RED = (255, 100, 100)
INSTRUCTIONS_BG = (240, 240, 240)
PAUSE_COLOR = (255, 215, 0)

# Fonts
timer_font_small = pygame.font.SysFont('arial', 12, bold=True)
timer_font_day = pygame.font.SysFont('arial', 20, bold=True)
font = pygame.font.SysFont('arial', 14)
big_font = pygame.font.SysFont('arial', 19)

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
coins = 15
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

# Day system - 8 days (0-7)
DAY_DURATION = 90
day_start_time = time.time()
current_day = 0
daily_start_coins = 15
daily_quotas = [20, 30, 50, 80, 120, 170, 230, 300]

# Cached surfaces
coins_surface = day_surface = quota_surface = seeds_surface = None
seed_count_surfaces = [None] * 6
day_timer_surface = None

#load background music
pygame.mixer.init()
pygame.mixer.music.load("background.mp3")  # your file name
pygame.mixer.music.play(-1)  # -1 = loop forever

pygame.mixer.music.set_volume(0.5)  # 50% volume


def get_shop_buttons():
    if shop_collapsed:
        return {
            'toggle': pygame.Rect(10, 5, 20, 20),
            'coins': pygame.Rect(35, 2, 50, 26),
            'day': pygame.Rect(90, 2, 45, 26),
            'quota': pygame.Rect(140, 2, 45, 26),
            'timer': pygame.Rect(195, 2, 55, 26),  
            'seeds': pygame.Rect(255, 2, 45, 26),
            'pause': pygame.Rect(305, 2, 30, 26),
            'help': pygame.Rect(WIDTH-35, 5, 20, 20)
        }
    return {
        'corn 5$': pygame.Rect(10, 15, 70, 50),
        'watermelon 7$': pygame.Rect(85, 15, 70, 50),
        'pumpkin 8$': pygame.Rect(160, 15, 70, 50),
        'tomato 10$': pygame.Rect(235, 15, 70, 50),
        'grape 12$': pygame.Rect(310, 15, 70, 50),
        'super 20$': pygame.Rect(385, 15, 70, 50),
        'coins': pygame.Rect(460, 15, 70, 25),
        'day': pygame.Rect(535, 15, 45, 25),
        'quota': pygame.Rect(585, 15, 45, 25),
        'timer': pygame.Rect(635, 15, 70, 25),
        'seeds': pygame.Rect(710, 15, 55, 25),
        'pause': pygame.Rect(600, 45, 40, 25),
        'help': pygame.Rect(WIDTH-35, 15, 25, 45)
    }


def check_daily_quota():
    global daily_start_coins, current_day, game_over, game_won, show_game_over
    time_elapsed = time.time() - day_start_time
    days_passed = int(time_elapsed // DAY_DURATION)
    new_day = min(days_passed, 7)
    
    if new_day > current_day:
        print(f"Day {current_day} ended. Checking quota...")
        if current_day < len(daily_quotas):
            required = daily_quotas[current_day]
            # FIXED: Check TOTAL coins vs quota (not earned)
            if coins >= required:
                print(f"✓ Day {current_day} PASSED! (Coins: {coins} >= {required})")
                if current_day == 7:
                    game_won = True
                    show_game_over = True
                else:
                    current_day = new_day
                    daily_start_coins = coins  # Track starting total for next day
            else:
                game_over = True
                show_game_over = True
                print(f"✗ Day {current_day} FAILED! (Coins: {coins} < {required})")
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

def draw_shop():
    buttons = get_shop_buttons()
    mouse_pos = pygame.mouse.get_pos()
    height = COLLAPSED_HEIGHT if shop_collapsed else SHOP_HEIGHT
    
    pygame.draw.rect(WIN, SHOP_BG, (0, 0, WIDTH, height))
    pygame.draw.rect(WIN, BROWN, (0, 0, WIDTH, height), 5)
    
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
        
        # FIXED: Seed letters with counts
        for i, letter in enumerate(SEED_LETTERS):
            x = 355 + i * 22
            WIN.blit(font.render(letter, True, BLACK), (x + 2, 3))
            if seed_count_surfaces[i]:
                WIN.blit(seed_count_surfaces[i], (x + 2, 18))
        
        # FIXED: Pause button with visual feedback
        btn = buttons['pause']
        color = SHOP_HOVER if btn.collidepoint(mouse_pos) else SHOP_BG
        pygame.draw.rect(WIN, color, btn)
        pygame.draw.rect(WIN, BROWN, btn, 2)
        pause_surf = PAUSE_ON_TEXT if is_paused else PAUSE_TEXT
        WIN.blit(pause_surf, pause_surf.get_rect(center=btn.center))
        
        btn = buttons['help']
        pygame.draw.rect(WIN, SHOP_HOVER if btn.collidepoint(mouse_pos) else SHOP_BG, btn)
        pygame.draw.rect(WIN, BROWN, btn, 2)
        WIN.blit(HELP_TEXT, HELP_TEXT.get_rect(center=btn.center))
    
    else:
        WIN.blit(SHOP_TITLE, (10, 22))
        
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
        
            seeds = [
            ("corn", 5), ("watermelon", 7), ("pumpkin", 8), 
            ("tomato", 10), ("grape", 12), ("super", 20)]

        for i, (seed_type, cost) in enumerate(seeds):
            btn = buttons[f"{seed_type} {cost}$"]
            color = SHOP_HOVER if btn.collidepoint(mouse_pos) else SHOP_BG
            pygame.draw.rect(WIN, color, btn)
            pygame.draw.rect(WIN, BROWN, btn, 2)
            
            # Name text
            name_text = font.render(seed_type.capitalize(), True, BLACK)
            
            # Price text
            price_text = font.render(f"${cost}", True, (0, 150, 0))
            
            # Count text
            count = globals()[f"{seed_type}_seeds"]
            count_text = font.render(str(count), True, RED)
            
            # Position texts (name top, price middle, count bottom)
            name_y = btn.y + 8
            price_y = btn.centery - price_text.get_height()//2
            count_y = btn.bottom - 18
            
            WIN.blit(name_text, (btn.centerx - name_text.get_width()//2, name_y))
            WIN.blit(price_text, (btn.centerx - price_text.get_width()//2, price_y))
            WIN.blit(count_text, (btn.centerx - count_text.get_width()//2, count_y))

        
        #Expanded pause button
        btn = buttons['pause']
        color = SHOP_HOVER if btn.collidepoint(mouse_pos) else SHOP_BG
        pygame.draw.rect(WIN, color, btn)
        pygame.draw.rect(WIN, BROWN, btn, 2)
        pause_surf = PAUSE_ON_TEXT if is_paused else PAUSE_TEXT
        WIN.blit(pause_surf, pause_surf.get_rect(center=btn.center))
        
        btn = buttons['help']
        pygame.draw.rect(WIN, SHOP_HOVER if btn.collidepoint(mouse_pos) else SHOP_BG, btn)
        pygame.draw.rect(WIN, BROWN, btn, 2)
        WIN.blit(HELP_BIG_TEXT, HELP_BIG_TEXT.get_rect(center=btn.center))

def draw_end_screen():
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

    
    replay_rect = pygame.Rect(panel.x + 50, panel.y + 220, 190, 60)
    pygame.draw.rect(WIN, (50, 200, 50), replay_rect)
    pygame.draw.rect(WIN, BLACK, replay_rect, 3)
    WIN.blit(REPLAY_TEXT, (replay_rect.centerx - REPLAY_TEXT.get_width()//2, replay_rect.centery - 10))
    
    quit_rect = pygame.Rect(panel.x + 260, panel.y + 220, 190, 60)
    pygame.draw.rect(WIN, RED, quit_rect)
    pygame.draw.rect(WIN, BLACK, quit_rect, 3)
    WIN.blit(QUIT_TEXT, (quit_rect.centerx - QUIT_TEXT.get_width()//2, quit_rect.centery - 10))

def get_farm_position():
    return (
        (WIDTH - GRID_SIZE * TILE_SIZE) // 2,
        (COLLAPSED_HEIGHT if shop_collapsed else SHOP_HEIGHT) + FARM_Y_OFFSET
    )

def draw_farm():
    farm_x, farm_y = get_farm_position()
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            x, y = farm_x + col * TILE_SIZE, farm_y + row * TILE_SIZE
            pygame.draw.rect(WIN, GRASS_GREEN, (x, y, TILE_SIZE, TILE_SIZE))
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
            if event.key == pygame.K_ESCAPE:
                run = False
            elif event.key == pygame.K_s and not (show_game_over or show_instructions):
                shop_collapsed = not shop_collapsed
            elif event.key == pygame.K_h:
                show_instructions = not show_instructions
            elif show_game_over:
                if event.key == pygame.K_r:
                    # Reset game (same as before)
                    coins = 15
                    daily_start_coins = 15
                    corn_seeds = watermelon_seeds = pumpkin_seeds = tomato_seeds = grape_seeds = super_seeds = 0
                    crops = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
                    plant_time = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
                    current_day = 0
                    day_start_time = time.time()
                    game_over = game_won = show_game_over = False
                elif event.key == pygame.K_q:
                    run = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            if show_game_over:
                panel = pygame.Rect(150, 200, 500, 350)
                if pygame.Rect(panel.x + 50, panel.y + 220, 190, 60).collidepoint(mx, my):
                    coins = 15
                    daily_start_coins = 15
                    corn_seeds = watermelon_seeds = pumpkin_seeds = tomato_seeds = grape_seeds = super_seeds = 0
                    crops = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
                    plant_time = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
                    current_day = 0
                    day_start_time = time.time()
                    game_over = game_won = show_game_over = False
                elif pygame.Rect(panel.x + 260, panel.y + 220, 190, 60).collidepoint(mx, my):
                    run = False
                continue
            
            if show_instructions:
                close_rect = pygame.Rect(665, 160, 25, 25)
                if close_rect.collidepoint(mx, my):
                    show_instructions = False
                    continue
            
            if not show_instructions:
                shop_height = COLLAPSED_HEIGHT if shop_collapsed else SHOP_HEIGHT
                if my < shop_height:
                    buttons = get_shop_buttons()
                    if shop_collapsed:
                        if buttons['toggle'].collidepoint(mx, my):
                            shop_collapsed = not shop_collapsed
                        elif buttons['pause'].collidepoint(mx, my):  # FIXED: Pause toggle
                            is_paused = not is_paused
                        elif buttons['help'].collidepoint(mx, my):
                            show_instructions = True
                    else:
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
                                if is_paused:
                                    continue
                                globals()[f"{seed_name}_seeds"] += 1
                                coins -= cost
                                update_cached_text()
                                break

                        if buttons['pause'].collidepoint(mx, my):  #Pause toggle
                            is_paused = not is_paused
                        elif buttons['help'].collidepoint(mx, my):
                            show_instructions = True
                else:
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
                            elif crops[row][col] is None:
                                # FIXED: Cheap seeds first (corn → super)
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
    
    if not is_paused and not show_game_over and not show_instructions:
        check_daily_quota()
        update_crops()
    
    update_cached_text()
    # Draw everything
    WIN.fill((135, 206, 235))
    if not show_game_over:
        draw_shop()
    draw_farm()
    draw_end_screen()
    
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
            "7. ||/▶ = PAUSE (click button too!)",
            "",
            "Corn:8s=$6 | Watermelon:11s=$12 | Pumpkin:14s=$15",
            "Tomato:12s=$18 | Grape:17s=$20 | Super:20s=$50 ($20)",
            "",
            f"Day {current_day+1} quota: {daily_quotas[current_day]} earned today"
        ]
        for i, text in enumerate(instructions):
            WIN.blit(font.render(text, True, BLACK), (panel.x + 20, panel.y + 70 + i * 18))
        
        close_rect = pygame.Rect(665, 160, 25, 25)
        pygame.draw.rect(WIN, RED, close_rect)
        pygame.draw.rect(WIN, BLACK, close_rect, 2)
        WIN.blit(CLOSE_TEXT, CLOSE_TEXT.get_rect(center=close_rect.center))
        mouse_pos = pygame.mouse.get_pos()
        if close_rect.collidepoint(mouse_pos):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
