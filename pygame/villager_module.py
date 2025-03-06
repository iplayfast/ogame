import pygame
import random
import math

class Villager(pygame.sprite.Sprite):
    def __init__(self, x, y, assets, tile_size=32):
        super().__init__()
        
        self.TILE_SIZE = tile_size
        
        # Select a random villager sprite
        villager_keys = list(assets['characters'].keys())
        if villager_keys:
            sprite_key = random.choice(villager_keys)
            self.base_image = assets['characters'][sprite_key]
            self.image = self.base_image.copy()
            self.rect = self.image.get_rect(center=(x, y))
        else:
            # Fallback if no sprites available
            self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255, 0, 0), (12, 12), 12)
            self.rect = self.image.get_rect(center=(x, y))
            self.base_image = self.image.copy()
        
        # Villager properties
        self.name = self.generate_name()
        self.job = random.choice([
            "Farmer", "Blacksmith", "Merchant", "Guard", "Baker",
            "Tailor", "Carpenter", "Miner", "Hunter", "Innkeeper"
        ])
        self.mood = random.choice([
            "Happy", "Content", "Neutral", "Tired", "Excited",
            "Curious", "Busy", "Relaxed", "Bored", "Worried"
        ])
        self.health = random.randint(70, 100)
        self.energy = random.randint(50, 100)
        self.money = random.randint(10, 100)
        
        # Movement
        self.position = pygame.math.Vector2(x, y)
        self.destination = None
        self.path = []
        self.speed = random.uniform(0.3, 1.0)  # Villager movement speed
        self.idle_timer = 0
        
        # Interaction
        self.is_selected = False
        self.is_talking = False
        self.talk_timer = 0
        self.talk_cooldown = random.randint(5000, 15000)  # 5-15 seconds between talks
        
        # Make sure conversations is not empty before choosing
        if assets['sounds']['conversations']:
            self.conversation_sound = random.choice(assets['sounds']['conversations'])
        else:
            # Create a dummy sound if needed
            self.conversation_sound = pygame.mixer.Sound(buffer=bytearray(100))
        
        # Activity tracking
        self.current_activity = "Wandering"
        self.activity_timer = 0
        
        # Update timestamp
        self.last_update = pygame.time.get_ticks()
    
    def generate_name(self):
        """Generate a random villager name."""
        first_names = [
            "Aiden", "Bela", "Clara", "Doran", "Eliza", "Finn", "Greta", "Hilda", 
            "Ivan", "Julia", "Kai", "Lily", "Milo", "Nina", "Otto", "Petra", 
            "Quinn", "Rosa", "Sven", "Tilly", "Ulric", "Vera", "Wren", "Xander", 
            "Yara", "Zeke"
        ]
        
        last_names = [
            "Smith", "Miller", "Fisher", "Baker", "Cooper", "Fletcher", "Thatcher",
            "Wood", "Stone", "Field", "Hill", "Brook", "River", "Dale", "Ford",
            "Green", "White", "Black", "Brown", "Gray", "Reed", "Swift", "Strong"
        ]
        
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    def update(self, village_data, current_time, assets):
        # Calculate delta time
        dt = current_time - self.last_update
        self.last_update = current_time
        
        # Update talking state
        self.talk_timer += dt
        if self.talk_timer > self.talk_cooldown:
            self.talk_timer = 0
            self.is_talking = random.random() < 0.3  # 30% chance to be talking
        
        # Update activity
        self.activity_timer += dt
        if self.activity_timer > 10000:  # Change activity every 10 seconds
            self.activity_timer = 0
            self.current_activity = random.choice([
                "Wandering", "Working", "Shopping", "Resting", "Socializing"
            ])
        
        # Handle movement
        if self.destination is None or self.idle_timer > 0:
            # If no destination or idle, handle idle timer
            if self.idle_timer > 0:
                self.idle_timer -= dt
            else:
                # Find new destination
                self.find_new_destination(village_data)
                self.idle_timer = 0
        else:
            # Move toward destination
            dx = self.destination[0] - self.position.x
            dy = self.destination[1] - self.position.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < 2:  # Close enough to destination
                self.position.x = self.destination[0]
                self.position.y = self.destination[1]
                self.destination = None
                self.idle_timer = random.randint(2000, 5000)  # Idle for 2-5 seconds
            else:
                # Move toward destination
                move_x = dx / distance * self.speed * (dt / 16.67)
                move_y = dy / distance * self.speed * (dt / 16.67)
                
                self.position.x += move_x
                self.position.y += move_y
                
                # Update rect position
                self.rect.centerx = int(self.position.x)
                self.rect.centery = int(self.position.y)
    
    def find_new_destination(self, village_data):
        """Find a new destination for the villager."""
        destination_type = random.choice(["random", "building", "path"])
        
        if destination_type == "building" and village_data['buildings']:
            # Head to a random building
            building = random.choice(village_data['buildings'])
            offset_x = random.randint(-self.TILE_SIZE, self.TILE_SIZE)
            offset_y = random.randint(-self.TILE_SIZE, self.TILE_SIZE)
            self.destination = (
                building['position'][0] + offset_x,
                building['position'][1] + offset_y
            )
        elif destination_type == "path" and village_data['paths']:
            # Head to a random path
            path = random.choice(village_data['paths'])
            self.destination = path['position']
        else:
            # Head to a random position
            self.destination = (
                random.randint(0, village_data['size']),
                random.randint(0, village_data['size'])
            )
    
    def get_status(self):
        """Get villager status for display."""
        return {
            "Name": self.name,
            "Job": self.job,
            "Mood": self.mood,
            "Health": self.health,
            "Energy": self.energy,
            "Money": self.money,
            "Activity": self.current_activity
        }
    
    def draw_selection_indicator(self, surface, camera_offset_x, camera_offset_y):
        """Draw a selection indicator around the villager if selected."""
        if self.is_selected:
            # Draw circle around villager
            center_x = self.rect.centerx - camera_offset_x
            center_y = self.rect.centery - camera_offset_y
            radius = max(self.rect.width, self.rect.height) // 2 + 5
            pygame.draw.circle(surface, (255, 255, 255), (center_x, center_y), radius, 2)
            
            # Draw speech indicator if talking
            if self.is_talking:
                bubble_x = center_x + radius
                bubble_y = center_y - radius
                pygame.draw.circle(surface, (255, 255, 255), (bubble_x, bubble_y), 8)
                pygame.draw.circle(surface, (0, 0, 0), (bubble_x, bubble_y), 8, 1)
                
                # Speech dots
                for i in range(3):
                    dot_x = bubble_x - 4 + i * 4
                    dot_y = bubble_y
                    pygame.draw.circle(surface, (0, 0, 0), (dot_x, dot_y), 1)
