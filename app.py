import cv2
import mediapipe as mp
import pygame
import numpy as np
import sys

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Initialize Pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
GROUND_HEIGHT = 350
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Hand-Controlled Dino Game")
clock = pygame.time.Clock()

# Dino class
class Dino:
    def __init__(self):
        self.x = 50
        self.y = GROUND_HEIGHT
        self.width = 50
        self.height = 80
        self.is_jumping = False
        self.jump_vel = 0
        self.gravity = 1
        self.jump_power = -15
        
    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.jump_vel = self.jump_power
            
    def update(self):
        if self.is_jumping:
            self.y += self.jump_vel
            self.jump_vel += self.gravity
            
            if self.y >= GROUND_HEIGHT:
                self.y = GROUND_HEIGHT
                self.is_jumping = False
                self.jump_vel = 0
                
    def draw(self, surface):
        pygame.draw.rect(surface, BLACK, (self.x, self.y - self.height, self.width, self.height))
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y - self.height, self.width, self.height)

# Obstacle class
class Obstacle:
    def __init__(self):
        self.width = 30
        self.height = 50
        self.x = SCREEN_WIDTH
        self.y = GROUND_HEIGHT - self.height
        self.speed = 5
        
    def update(self):
        self.x -= self.speed
        
    def draw(self, surface):
        pygame.draw.rect(surface, GRAY, (self.x, self.y, self.width, self.height))
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
        
    def is_off_screen(self):
        return self.x < -self.width

# Game state
dino = Dino()
obstacles = []
obstacle_timer = 0
score = 0
game_over = False
font = pygame.font.SysFont(None, 36)

# Webcam setup
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

def process_gestures(hand_landmarks):
    # Simple gesture detection - check if hand is raised (y coordinate of wrist)
    wrist_y = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y
    middle_finger_tip_y = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y
    
    # Jump if wrist is above middle finger tip (hand raised)
    if wrist_y < middle_finger_tip_y - 0.1:
        dino.jump()

def draw_webcam_frame(frame, surface):
    # Convert OpenCV frame to Pygame surface
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.rot90(frame)
    frame = pygame.surfarray.make_surface(frame)
    
    # Draw webcam feed in top-right corner
    scaled_frame = pygame.transform.scale(frame, (160, 120))
    surface.blit(scaled_frame, (SCREEN_WIDTH - 160, 0))

# Main game loop
while True:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            cap.release()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not game_over:
                dino.jump()
            if event.key == pygame.K_r and game_over:
                # Reset game
                dino = Dino()
                obstacles = []
                score = 0
                game_over = False
    
    # Read webcam frame
    ret, frame = cap.read()
    if not ret:
        continue
    
    # Process hand tracking
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw hand landmarks on webcam feed
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Process gestures
            if not game_over:
                process_gestures(hand_landmarks)
    
    # Game logic
    if not game_over:
        # Update dino
        dino.update()
        
        # Spawn obstacles
        obstacle_timer += 1
        if obstacle_timer >= 120:  # Every 2 seconds at 60 FPS
            obstacles.append(Obstacle())
            obstacle_timer = 0
            
        # Update obstacles
        for obstacle in obstacles[:]:
            obstacle.update()
            if obstacle.is_off_screen():
                obstacles.remove(obstacle)
                score += 1
                
            # Check collision
            if dino.get_rect().colliderect(obstacle.get_rect()):
                game_over = True
    
    # Drawing
    screen.fill(WHITE)
    
    # Draw ground
    pygame.draw.line(screen, BLACK, (0, GROUND_HEIGHT), (SCREEN_WIDTH, GROUND_HEIGHT), 2)
    
    # Draw game elements
    dino.draw(screen)
    for obstacle in obstacles:
        obstacle.draw(screen)
        
    # Draw webcam feed
    draw_webcam_frame(frame, screen)
    
    # Draw score
    score_text = font.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (10, 10))
    
    # Draw game over message
    if game_over:
        game_over_text = font.render("Game Over! Press R to restart", True, BLACK)
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - 180, SCREEN_HEIGHT//2 - 18))
    
    pygame.display.flip()
    clock.tick(FPS)