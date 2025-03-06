import pygame
import random
import os
import numpy as np
import math
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import colorsys

# Initialize pygame
pygame.init()

# Create directories for assets
def create_directories():
    directories = [
        "assets",
        "assets/characters",
        "assets/buildings",
        "assets/buildings/roofs",
        "assets/environment",
        "assets/ui"
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Enhanced color palettes for more visual variety
PALETTES = {
    "character_skin": [(255, 220, 178), (255, 213, 164), (255, 200, 159), 
                      (240, 184, 135), (222, 165, 118), (198, 134, 66),
                      (172, 112, 61), (147, 85, 45)],
    "character_hair": [(43, 29, 14), (67, 44, 13), (113, 65, 25), 
                      (143, 89, 30), (175, 136, 74), (211, 188, 141),
                      (70, 35, 10), (30, 20, 10), (120, 80, 30)],
    "character_clothes": [(45, 49, 66), (86, 90, 105), (152, 93, 93), 
                         (65, 90, 119), (102, 141, 60), (222, 110, 75),
                         (241, 175, 78), (31, 138, 112), (180, 50, 50),
                         (50, 100, 150), (100, 60, 120), (160, 130, 50)],
    # Enhanced building wall colors
    "building_walls": [
        (240, 217, 181), (219, 182, 151), (236, 229, 206),
        (204, 174, 145), (176, 166, 147), (157, 132, 109),
        (220, 200, 180), (200, 185, 160), (180, 160, 140),
        (160, 145, 120), (240, 230, 215), (230, 210, 180),
        (210, 190, 170), (190, 170, 150), (170, 150, 130)
    ],
    # Enhanced roof colors for more variety
    "building_roofs": [
        (172, 89, 74), (140, 76, 54), (92, 62, 42),
        (109, 79, 51), (140, 118, 84), (160, 100, 80),
        (130, 65, 50), (100, 70, 45), (80, 55, 35),
        (120, 85, 55), (150, 125, 90), (170, 110, 90),
        (80, 50, 40), (110, 80, 60), (60, 40, 30)
    ],
    # More varied greens for environment
    "environment_green": [
        (62, 137, 72), (94, 153, 84), (138, 178, 125),
        (49, 135, 118), (83, 160, 121), (30, 100, 50),
        (70, 140, 60), (110, 170, 90), (35, 120, 70),
        (60, 130, 100), (90, 150, 70), (40, 110, 60)
    ],
    # New decorative element colors
    "decorations": [
        (180, 120, 70),  # Wood
        (200, 200, 210), # Metal
        (160, 40, 30),   # Rust
        (220, 220, 180), # Cream
        (160, 180, 200), # Light blue
        (190, 150, 110), # Tan
        (150, 70, 50),   # Terracotta
    ]
}

# Function to create character sprites (48x48 px)
def generate_character_sprites(num_variations=5):
    base_size = 48
    
    for i in range(num_variations):
        # Create base canvas
        character = Image.new('RGBA', (base_size, base_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(character)
        
        # Random attributes
        skin_tone = random.choice(PALETTES["character_skin"])
        hair_color = random.choice(PALETTES["character_hair"])
        primary_color = random.choice(PALETTES["character_clothes"])
        secondary_color = random.choice(PALETTES["character_clothes"])
        
        # Head
        head_size = base_size // 3
        head_pos = (base_size // 2 - head_size // 2, base_size // 4)
        draw.ellipse([head_pos[0], head_pos[1], 
                     head_pos[0] + head_size, head_pos[1] + head_size], 
                     fill=skin_tone)
        
        # Hair - simple cap style
        if random.random() > 0.3:  # 70% chance to have visible hair
            hair_width = head_size + random.randint(2, 6)
            hair_height = head_size // 2
            hair_pos = (head_pos[0] - (hair_width - head_size) // 2, 
                       head_pos[1] - random.randint(0, 4))
            draw.ellipse([hair_pos[0], hair_pos[1], 
                         hair_pos[0] + hair_width, hair_pos[1] + hair_height], 
                         fill=hair_color)
        
        # Body
        body_width = int(head_size * 1.2)
        body_height = int(head_size * 1.5)
        body_pos = (base_size // 2 - body_width // 2, 
                   head_pos[1] + head_size - 2)  # Slight overlap with head
        draw.rectangle([body_pos[0], body_pos[1], 
                       body_pos[0] + body_width, body_pos[1] + body_height], 
                       fill=primary_color)
        
        # Secondary clothing details (like a vest or belt)
        if random.random() > 0.5:
            detail_type = random.choice(["vest", "belt", "sash"])
            
            if detail_type == "vest":
                vest_width = body_width - 4
                draw.rectangle([body_pos[0] + 2, body_pos[1] + 2, 
                               body_pos[0] + vest_width, body_pos[1] + body_height - 2], 
                               fill=secondary_color)
            elif detail_type == "belt":
                belt_height = 4
                belt_pos_y = body_pos[1] + body_height // 2
                draw.rectangle([body_pos[0], belt_pos_y, 
                               body_pos[0] + body_width, belt_pos_y + belt_height], 
                               fill=secondary_color)
            elif detail_type == "sash":
                # Diagonal sash
                sash_width = 4
                draw.line([(body_pos[0], body_pos[1]), 
                          (body_pos[0] + body_width, body_pos[1] + body_height)], 
                          fill=secondary_color, width=sash_width)
        
        # Legs
        leg_width = body_width // 3
        leg_height = head_size // 1.5
        leg_pos_y = body_pos[1] + body_height
        # Left leg
        draw.rectangle([body_pos[0] + body_width // 3 - leg_width // 2, leg_pos_y, 
                       body_pos[0] + body_width // 3 + leg_width // 2, leg_pos_y + leg_height], 
                       fill=primary_color)
        # Right leg
        draw.rectangle([body_pos[0] + body_width * 2 // 3 - leg_width // 2, leg_pos_y, 
                       body_pos[0] + body_width * 2 // 3 + leg_width // 2, leg_pos_y + leg_height], 
                       fill=primary_color)
        
        # Arms (simplified as rectangles for top-down view)
        arm_width = body_width // 4
        arm_height = body_height * 3 // 4
        # Left arm
        draw.rectangle([body_pos[0] - arm_width // 2, body_pos[1] + 4, 
                       body_pos[0] + arm_width // 2, body_pos[1] + arm_height], 
                       fill=primary_color)
        # Right arm
        draw.rectangle([body_pos[0] + body_width - arm_width // 2, body_pos[1] + 4, 
                       body_pos[0] + body_width + arm_width // 2, body_pos[1] + arm_height], 
                       fill=primary_color)
        
        # Simple face (just eyes for top-down view)
        eye_size = 2
        eye_y = head_pos[1] + head_size // 2 - 2
        # Left eye
        draw.ellipse([head_pos[0] + head_size // 3 - eye_size, eye_y, 
                     head_pos[0] + head_size // 3 + eye_size, eye_y + eye_size * 2], 
                     fill=(0, 0, 0))
        # Right eye
        draw.ellipse([head_pos[0] + head_size * 2 // 3 - eye_size, eye_y, 
                     head_pos[0] + head_size * 2 // 3 + eye_size, eye_y + eye_size * 2], 
                     fill=(0, 0, 0))
        
        # Add slight randomness to appearance
        character = character.rotate(random.uniform(-5, 5), resample=Image.BICUBIC, expand=False)
        
        # Save the character
        filename = f"assets/characters/villager_{i+1}.png"
        character.save(filename)
        print(f"Generated character: {filename}")

# Function to generate buildings (scaled 3x from the original)
def generate_buildings(num_variations=4):
    for i in range(num_variations):
        # Randomize building size
        building_type = random.choice(["small", "medium", "large"])
        
        # Scale base sizes by 3x
        if building_type == "small":
            base_size = 96 * 3  # 288
        elif building_type == "medium":
            base_size = 128 * 3  # 384
        else:
            base_size = 192 * 3  # 576
        
        # Create base building image
        building = Image.new('RGBA', (base_size, base_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(building)
        
        # Determine building style
        building_style = random.choice([
            "cottage", "house", "shop", "tavern", "workshop"
        ])
        
        # Wall color
        wall_color = random.choice(PALETTES["building_walls"])
        
        # Base structure
        structure_width = base_size * 7 // 8
        structure_height = base_size * 7 // 8
        structure_pos = ((base_size - structure_width) // 2, (base_size - structure_height) // 2)
        
        # Draw base
        draw.rectangle([structure_pos[0], structure_pos[1], 
                       structure_pos[0] + structure_width, structure_pos[1] + structure_height], 
                       fill=wall_color)
        
        # Add foundation if desired (slightly darker than wall)
        if random.random() > 0.3:  # 70% chance
            foundation_height = base_size // 20
            foundation_color = (
                max(0, wall_color[0] - 30),
                max(0, wall_color[1] - 30),
                max(0, wall_color[2] - 30)
            )
            draw.rectangle([structure_pos[0], structure_pos[1] + structure_height - foundation_height,
                           structure_pos[0] + structure_width, structure_pos[1] + structure_height],
                           fill=foundation_color)
        
        # Add windows and door
        num_windows = random.randint(4, 8)  # More windows for larger buildings
        window_size = base_size // 12
        door_width = base_size // 8
        door_height = base_size // 5
        
        # Door position (centered on bottom)
        door_pos = (structure_pos[0] + (structure_width - door_width) // 2,
                   structure_pos[1] + structure_height - door_height)
        door_color = (random.randint(50, 100), random.randint(30, 60), random.randint(10, 40))
        draw.rectangle([door_pos[0], door_pos[1], 
                       door_pos[0] + door_width, door_pos[1] + door_height], 
                       fill=door_color)
        
        # Door details
        # Door frame
        frame_color = (min(255, door_color[0] + 30), min(255, door_color[1] + 30), min(255, door_color[2] + 30))
        frame_width = 2
        draw.rectangle([door_pos[0] - frame_width, door_pos[1] - frame_width,
                       door_pos[0] + door_width + frame_width, door_pos[1] + door_height + frame_width],
                       outline=frame_color, width=frame_width)
        
        # Door handle
        handle_pos = (door_pos[0] + door_width * 3 // 4, door_pos[1] + door_height // 2)
        handle_size = 4  # Larger handle
        draw.ellipse([handle_pos[0] - handle_size, handle_pos[1] - handle_size,
                     handle_pos[0] + handle_size, handle_pos[1] + handle_size],
                     fill=(200, 200, 200))
        
        # Windows
        window_positions = []
        window_margin = base_size // 16
        
        # Determine window row positions (1, 2, or 3 rows for larger buildings)
        window_rows = 1 if building_type == "small" else (
                      2 if building_type == "medium" else 3)
        
        row_positions = []
        if window_rows == 1:
            row_positions = [structure_pos[1] + structure_height // 3]
        elif window_rows == 2:
            row_positions = [
                structure_pos[1] + structure_height // 4,
                structure_pos[1] + structure_height * 2 // 4
            ]
        else:
            row_positions = [
                structure_pos[1] + structure_height // 5,
                structure_pos[1] + structure_height * 2 // 5,
                structure_pos[1] + structure_height * 3 // 5
            ]
        
        # Distribute windows
        for row_y in row_positions:
            # Determine number of windows for this row
            row_windows = random.randint(2, 3) if building_type == "small" else random.randint(3, 5)
            
            # Position windows evenly
            for w in range(row_windows):
                # Skip the center position on the bottom row if there's a door
                if row_y > structure_pos[1] + structure_height // 2:
                    if w == row_windows // 2 and row_windows % 2 == 1:
                        continue
                
                segment_width = structure_width / (row_windows + 1)
                window_x = structure_pos[0] + segment_width * (w + 1) - window_size // 2
                window_positions.append((window_x, row_y))
        
        # Add shutters to some windows
        has_shutters = random.random() > 0.5
        shutter_color = random.choice([
            (120, 80, 40),  # Brown
            (60, 80, 40),   # Dark green
            (80, 40, 40),   # Dark red
            (40, 60, 80)    # Dark blue
        ])
        
        # Draw windows with possible shutters
        for wx, wy in window_positions:
            window_color = (173, 216, 230, 200)  # Light blue, slightly transparent
            
            # Window styles
            window_style = random.choice(["plain", "cross", "lattice"])
            
            # Draw the window
            draw.rectangle([wx, wy, wx + window_size, wy + window_size], fill=window_color)
            
            # Window frame
            frame_color = (255, 255, 255)
            frame_width = 2
            draw.rectangle([wx - frame_width, wy - frame_width, 
                           wx + window_size + frame_width, wy + window_size + frame_width], 
                           outline=frame_color, width=frame_width)
            
            # Window details based on style
            if window_style == "cross":
                # Cross pattern
                draw.line([(wx, wy + window_size // 2), (wx + window_size, wy + window_size // 2)],
                          fill=frame_color, width=1)
                draw.line([(wx + window_size // 2, wy), (wx + window_size // 2, wy + window_size)],
                          fill=frame_color, width=1)
            elif window_style == "lattice":
                # Lattice pattern
                for j in range(3):
                    offset = window_size * j // 3
                    draw.line([(wx, wy + offset), (wx + window_size, wy + offset)],
                              fill=frame_color, width=1)
                    draw.line([(wx + offset, wy), (wx + offset, wy + window_size)],
                              fill=frame_color, width=1)
            
            # Add shutters if enabled
            if has_shutters:
                shutter_width = window_size // 2
                shutter_height = window_size + 4
                
                # Left shutter
                draw.rectangle([wx - shutter_width - 2, wy - 2,
                               wx - 2, wy + shutter_height - 2],
                               fill=shutter_color)
                
                # Right shutter
                draw.rectangle([wx + window_size + 2, wy - 2,
                               wx + window_size + shutter_width + 2, wy + shutter_height - 2],
                               fill=shutter_color)
                
                # Shutter details (horizontal slats)
                for j in range(3):
                    offset = shutter_height * j // 4
                    # Left shutter slats
                    draw.line([(wx - shutter_width - 2, wy + offset),
                              (wx - 2, wy + offset)],
                              fill=(0, 0, 0), width=1)
                    # Right shutter slats
                    draw.line([(wx + window_size + 2, wy + offset),
                              (wx + window_size + shutter_width + 2, wy + offset)],
                              fill=(0, 0, 0), width=1)
        
        # Add architectural details
        
        # 1. Wall texture
        for _ in range(500):  # More texture points for larger buildings
            px = random.randint(structure_pos[0], structure_pos[0] + structure_width)
            py = random.randint(structure_pos[1], structure_pos[1] + structure_height)
            
            # Skip if pixel is within door or window
            skip = False
            if door_pos[0] <= px <= door_pos[0] + door_width and door_pos[1] <= py <= door_pos[1] + door_height:
                skip = True
            
            for wx, wy in window_positions:
                if wx <= px <= wx + window_size and wy <= py <= wy + window_size:
                    skip = True
                    break
            
            if not skip:
                # Slightly vary the wall color for texture
                texture_color = (
                    max(0, min(255, wall_color[0] + random.randint(-15, 15))),
                    max(0, min(255, wall_color[1] + random.randint(-15, 15))),
                    max(0, min(255, wall_color[2] + random.randint(-15, 15)))
                )
                draw.point((px, py), fill=texture_color)
        
        # 2. Add details based on building style
        if building_style == "cottage":
            # Flower boxes under some windows
            for wx, wy in window_positions:
                if random.random() > 0.6:  # 40% chance for a flower box
                    box_width = window_size + 8
                    box_height = window_size // 3
                    box_x = wx - 4
                    box_y = wy + window_size + 2
                    
                    # Draw box
                    box_color = random.choice(PALETTES["decorations"])
                    draw.rectangle([box_x, box_y, box_x + box_width, box_y + box_height],
                                  fill=box_color)
                    
                    # Draw flowers
                    for _ in range(3):
                        flower_x = box_x + random.randint(4, box_width - 4)
                        flower_y = box_y + 2
                        flower_color = (
                            random.randint(200, 255),
                            random.randint(100, 255),
                            random.randint(100, 255)
                        )
                        flower_size = random.randint(3, 5)
                        draw.ellipse([flower_x - flower_size, flower_y - flower_size,
                                     flower_x + flower_size, flower_y + flower_size],
                                     fill=flower_color)
        
        elif building_style == "tavern":
            # Sign
            sign_width = door_width * 3 // 2
            sign_height = door_width // 2
            sign_x = door_pos[0] - sign_width // 4
            sign_y = door_pos[1] - sign_height - 8
            
            # Sign backing
            sign_color = random.choice(PALETTES["decorations"])
            draw.rectangle([sign_x, sign_y, sign_x + sign_width, sign_y + sign_height],
                          fill=sign_color)
            
            # Sign outline
            sign_border = (
                max(0, sign_color[0] - 50),
                max(0, sign_color[1] - 50),
                max(0, sign_color[2] - 50)
            )
            draw.rectangle([sign_x, sign_y, sign_x + sign_width, sign_y + sign_height],
                          outline=sign_border, width=2)
            
            # Sign support
            support_width = 4
            support_height = 12
            support_x = sign_x + sign_width // 2 - support_width // 2
            support_y = sign_y + sign_height
            draw.rectangle([support_x, support_y, support_x + support_width, support_y + support_height],
                          fill=sign_border)
            
            # Sign symbol (mug)
            mug_color = (255, 240, 200)  # Cream color
            mug_x = sign_x + sign_width // 2
            mug_y = sign_y + sign_height // 2
            mug_size = min(sign_width, sign_height) // 3
            draw.ellipse([mug_x - mug_size, mug_y - mug_size,
                         mug_x + mug_size, mug_y + mug_size],
                         fill=mug_color)
        
        elif building_style == "shop" or building_style == "workshop":
            # Awning over door
            awning_width = door_width * 2
            awning_height = door_width // 2
            awning_x = door_pos[0] - awning_width // 4
            awning_y = door_pos[1] - awning_height
            
            # Awning color
            awning_color = random.choice([
                (180, 50, 50),  # Red
                (50, 100, 180), # Blue
                (180, 150, 50), # Yellow
                (50, 150, 80)   # Green
            ])
            
            # Draw awning (trapezoid shape)
            awning_points = [
                (awning_x, awning_y),
                (awning_x + awning_width, awning_y),
                (awning_x + awning_width + awning_width // 8, awning_y + awning_height),
                (awning_x - awning_width // 8, awning_y + awning_height)
            ]
            draw.polygon(awning_points, fill=awning_color)
            
            # Awning stripes
            stripe_color = (
                max(0, awning_color[0] - 50),
                max(0, awning_color[1] - 50),
                max(0, awning_color[2] - 50)
            )
            
            for i in range(1, 4):
                stripe_y = awning_y + awning_height * i // 4
                draw.line([(awning_x - awning_width // 8 * i // 4, stripe_y),
                          (awning_x + awning_width + awning_width // 8 * i // 4, stripe_y)],
                          fill=stripe_color, width=2)
        
        # Add chimney to some buildings
        if random.random() > 0.5:  # 50% chance
            chimney_width = base_size // 16
            chimney_height = base_size // 10
            chimney_x = random.randint(structure_pos[0] + structure_width // 4, 
                                      structure_pos[0] + structure_width * 3 // 4 - chimney_width)
            chimney_y = structure_pos[1] - chimney_height // 2
            
            chimney_color = (120, 100, 90)  # Stone/brick color
            draw.rectangle([chimney_x, chimney_y, 
                           chimney_x + chimney_width, structure_pos[1]],
                           fill=chimney_color)
            
            # Chimney top
            chimney_top_width = chimney_width + 4
            chimney_top_height = 6
            draw.rectangle([chimney_x - 2, chimney_y, 
                           chimney_x + chimney_width + 2, chimney_y + chimney_top_height],
                           fill=(80, 70, 60))
            
            # Smoke (if building is active)
            if random.random() > 0.5:  # 50% chance of smoke
                smoke_color = (220, 220, 220, 150)  # Light gray, semi-transparent
                smoke_x = chimney_x + chimney_width // 2
                for i in range(3):
                    smoke_y = chimney_y - 10 - i * 8
                    smoke_size = 8 + i * 4
                    draw.ellipse([smoke_x - smoke_size // 2, smoke_y - smoke_size // 2,
                                 smoke_x + smoke_size // 2, smoke_y + smoke_size // 2],
                                 fill=smoke_color)
        
        # Apply a subtle shadow/highlight effect
        building_array = np.array(building)
        # Light comes from top-left, so add highlights to top/left edges and shadows to bottom/right edges
        
        # Create and save the final building
        final_building = Image.fromarray(building_array)
        
        # Add a slight blur to soften the image
        if random.random() > 0.5:  # 50% chance for a subtle blur
            final_building = final_building.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Save building
        filename = f"assets/buildings/building_{building_type}_{i+1}.png"
        final_building.save(filename)
        print(f"Generated building: {filename}")
        
        # Generate matching roof
        generate_matching_roof(final_building, base_size, building_type, i+1)

def generate_matching_roof(building_image, base_size, building_type, index):
    """Generate a roof that matches the building."""
    roof = Image.new('RGBA', (base_size, base_size), (0, 0, 0, 0))
    roof_draw = ImageDraw.Draw(roof)
    
    # Structure dimensions (match with building)
    structure_width = base_size * 7 // 8
    structure_height = base_size * 7 // 8
    structure_pos = ((base_size - structure_width) // 2, (base_size - structure_height) // 2)
    
    # Roof style
    roof_style = random.choice(["flat", "pitched", "pyramid", "mansard", "hipped"])
    roof_color = random.choice(PALETTES["building_roofs"])
    
    if roof_style == "flat":
        # Simple flat roof
        roof_draw.rectangle([structure_pos[0], structure_pos[1], 
                           structure_pos[0] + structure_width, structure_pos[1] + structure_height],
                           fill=roof_color)
        
        # Add some details like vents or a chimney
        if random.random() > 0.5:
            # Roof access or skylight
            feature_width = base_size // 12
            feature_height = base_size // 12
            feature_x = structure_pos[0] + random.randint(feature_width, structure_width - 2*feature_width)
            feature_y = structure_pos[1] + random.randint(feature_height, structure_height - 2*feature_height)
            
            feature_color = (180, 180, 180)  # Light gray
            roof_draw.rectangle([feature_x, feature_y, 
                               feature_