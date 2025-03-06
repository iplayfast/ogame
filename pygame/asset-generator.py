import pygame
import random
import os
import numpy as np
import math
from PIL import Image, ImageDraw
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

# Color palettes for various asset types
PALETTES = {
    "character_skin": [(255, 220, 178), (255, 213, 164), (255, 200, 159), 
                      (240, 184, 135), (222, 165, 118), (198, 134, 66),
                      (172, 112, 61), (147, 85, 45)],
    "character_hair": [(43, 29, 14), (67, 44, 13), (113, 65, 25), 
                      (143, 89, 30), (175, 136, 74), (211, 188, 141)],
    "character_clothes": [(45, 49, 66), (86, 90, 105), (152, 93, 93), 
                         (65, 90, 119), (102, 141, 60), (222, 110, 75),
                         (241, 175, 78), (31, 138, 112)],
    "building_walls": [(240, 217, 181), (219, 182, 151), (236, 229, 206),
                      (204, 174, 145), (176, 166, 147), (157, 132, 109)],
    "building_roofs": [(172, 89, 74), (140, 76, 54), (92, 62, 42),
                      (109, 79, 51), (140, 118, 84)],
    "environment_green": [(62, 137, 72), (94, 153, 84), (138, 178, 125),
                         (49, 135, 118), (83, 160, 121)]
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

# Function to generate buildings (96x96 to 192x192 px)
def generate_buildings(num_variations=4):
    for i in range(num_variations):
        # Randomize building size
        building_type = random.choice(["small", "medium", "large"])
        
        if building_type == "small":
            base_size = 96
        elif building_type == "medium":
            base_size = 128
        else:
            base_size = 192
        
        # Create base building image
        building = Image.new('RGBA', (base_size, base_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(building)
        
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
        
        # Add windows and door
        num_windows = random.randint(2, 5)
        window_size = base_size // 12
        door_width = base_size // 8
        door_height = base_size // 6
        
        # Door position (centered on bottom)
        door_pos = (structure_pos[0] + (structure_width - door_width) // 2,
                   structure_pos[1] + structure_height - door_height)
        door_color = (random.randint(50, 100), random.randint(30, 60), random.randint(10, 40))
        draw.rectangle([door_pos[0], door_pos[1], 
                       door_pos[0] + door_width, door_pos[1] + door_height], 
                       fill=door_color)
        
        # Door handle
        handle_pos = (door_pos[0] + door_width * 3 // 4, door_pos[1] + door_height // 2)
        handle_size = 2
        draw.ellipse([handle_pos[0] - handle_size, handle_pos[1] - handle_size,
                     handle_pos[0] + handle_size, handle_pos[1] + handle_size],
                     fill=(200, 200, 200))
        
        # Windows
        window_positions = []
        window_margin = base_size // 16
        
        # Determine window row positions (1 or 2 rows)
        window_rows = 1 if building_type == "small" else random.randint(1, 2)
        
        if window_rows == 1:
            row_y = structure_pos[1] + structure_height // 3
            row_positions = [row_y]
        else:
            row1_y = structure_pos[1] + structure_height // 4
            row2_y = structure_pos[1] + structure_height // 2
            row_positions = [row1_y, row2_y]
        
        # Distribute windows
        for row_y in row_positions:
            # Determine number of windows for this row
            row_windows = random.randint(2, 3) if building_type == "small" else random.randint(2, 4)
            
            # Position windows evenly
            for w in range(row_windows):
                # Skip the center position on the bottom row if there's a door
                if row_y > structure_pos[1] + structure_height // 2:
                    if w == row_windows // 2 and row_windows % 2 == 1:
                        continue
                
                segment_width = structure_width / (row_windows + 1)
                window_x = structure_pos[0] + segment_width * (w + 1) - window_size // 2
                window_positions.append((window_x, row_y))
        
        # Draw windows
        for wx, wy in window_positions:
            window_color = (173, 216, 230, 200)  # Light blue, slightly transparent
            draw.rectangle([wx, wy, wx + window_size, wy + window_size], fill=window_color)
            
            # Window frame
            frame_color = (255, 255, 255)
            frame_width = 1
            draw.rectangle([wx - frame_width, wy - frame_width, 
                           wx + window_size + frame_width, wy + window_size + frame_width], 
                           outline=frame_color, width=frame_width)
        
        # Add some texture to walls
        for _ in range(100):
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
        
        # Save building
        filename = f"assets/buildings/building_{building_type}_{i+1}.png"
        building.save(filename)
        print(f"Generated building: {filename}")
        
        # Generate matching roof
        roof = Image.new('RGBA', (base_size, base_size), (0, 0, 0, 0))
        roof_draw = ImageDraw.Draw(roof)
        
        # Roof style
        roof_style = random.choice(["flat", "pitched", "pyramid"])
        roof_color = random.choice(PALETTES["building_roofs"])
        
        if roof_style == "flat":
            # Simple flat roof
            roof_draw.rectangle([structure_pos[0], structure_pos[1], 
                               structure_pos[0] + structure_width, structure_pos[1] + structure_height],
                               fill=roof_color)
            
            # Add some details like vents or a chimney
            if random.random() > 0.5:
                chimney_width = base_size // 16
                chimney_height = base_size // 12
                chimney_x = structure_pos[0] + random.randint(0, structure_width - chimney_width)
                chimney_y = structure_pos[1] + random.randint(0, structure_height - chimney_height)
                roof_draw.rectangle([chimney_x, chimney_y, 
                                   chimney_x + chimney_width, chimney_y + chimney_height],
                                   fill=(100, 100, 100))
            
        elif roof_style == "pitched":
            # Pitched roof (simple triangle)
            roof_height = structure_height // 2
            
            # Create a polygon for the roof
            roof_points = [
                (structure_pos[0], structure_pos[1] + structure_height),  # Bottom left
                (structure_pos[0] + structure_width // 2, structure_pos[1]),  # Top center
                (structure_pos[0] + structure_width, structure_pos[1] + structure_height)  # Bottom right
            ]
            roof_draw.polygon(roof_points, fill=roof_color)
            
        elif roof_style == "pyramid":
            # Pyramid roof for square buildings
            peak_height = structure_height // 2
            
            # Create a polygon for each face of the pyramid
            # Front face
            front_face = [
                (structure_pos[0], structure_pos[1] + structure_height),  # Bottom left
                (structure_pos[0] + structure_width // 2, structure_pos[1] + structure_height - peak_height),  # Top center
                (structure_pos[0] + structure_width, structure_pos[1] + structure_height)  # Bottom right
            ]
            roof_draw.polygon(front_face, fill=roof_color)
            
            # Add shading to give 3D effect
            darker_roof = (
                max(0, roof_color[0] - 30),
                max(0, roof_color[1] - 30),
                max(0, roof_color[2] - 30)
            )
            
            # Left face (darker for shading)
            left_face = [
                (structure_pos[0], structure_pos[1]),  # Top left
                (structure_pos[0] + structure_width // 2, structure_pos[1] + structure_height - peak_height),  # Top center
                (structure_pos[0], structure_pos[1] + structure_height)  # Bottom left
            ]
            roof_draw.polygon(left_face, fill=darker_roof)
        
        # Save roof
        roof_filename = f"assets/buildings/roofs/roof_{building_type}_{i+1}.png"
        roof.save(roof_filename)
        print(f"Generated roof: {roof_filename}")

# Function to generate environmental elements
def generate_environment():
    # Generate trees (64x64 px)
    for i in range(5):
        tree_size = 64
        tree = Image.new('RGBA', (tree_size, tree_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(tree)
        
        # Tree trunk
        trunk_width = tree_size // 8
        trunk_height = tree_size // 2
        trunk_pos = (tree_size // 2 - trunk_width // 2, tree_size - trunk_height)
        
        trunk_color = (139, 69, 19)  # Brown
        # Vary the trunk color slightly
        trunk_color = (
            max(0, min(255, trunk_color[0] + random.randint(-20, 20))),
            max(0, min(255, trunk_color[1] + random.randint(-10, 10))),
            max(0, min(255, trunk_color[2] + random.randint(-10, 10)))
        )
        
        draw.rectangle([trunk_pos[0], trunk_pos[1], 
                       trunk_pos[0] + trunk_width, trunk_pos[1] + trunk_height], 
                       fill=trunk_color)
        
        # Tree foliage
        foliage_style = random.choice(["round", "pine", "oak"])
        foliage_color = random.choice(PALETTES["environment_green"])
        
        # Add some variation to the foliage color
        foliage_color = (
            max(0, min(255, foliage_color[0] + random.randint(-15, 15))),
            max(0, min(255, foliage_color[1] + random.randint(-15, 15))),
            max(0, min(255, foliage_color[2] + random.randint(-15, 15)))
        )
        
        if foliage_style == "round":
            # Simple round canopy
            canopy_size = tree_size * 2 // 3
            canopy_pos = (tree_size // 2 - canopy_size // 2, tree_size // 8)
            draw.ellipse([canopy_pos[0], canopy_pos[1], 
                         canopy_pos[0] + canopy_size, canopy_pos[1] + canopy_size], 
                         fill=foliage_color)
            
        elif foliage_style == "pine":
            # Triangular pine tree
            triangle_width = tree_size * 2 // 3
            triangle_height = tree_size * 2 // 3
            
            # Multiple layers of triangles
            layers = random.randint(2, 3)
            for layer in range(layers):
                layer_y = tree_size // 2 - triangle_height + (triangle_height // layers) * layer
                layer_width = triangle_width - (triangle_width // 4) * layer
                
                triangle_points = [
                    (tree_size // 2 - layer_width // 2, layer_y + triangle_height // layers),  # Bottom left
                    (tree_size // 2, layer_y),  # Top center
                    (tree_size // 2 + layer_width // 2, layer_y + triangle_height // layers)  # Bottom right
                ]
                
                draw.polygon(triangle_points, fill=foliage_color)
                
        elif foliage_style == "oak":
            # More complex tree shape with irregular canopy
            center_x, center_y = tree_size // 2, tree_size // 3
            radius = tree_size // 3
            
            # Create several overlapping circles for an irregular shape
            for _ in range(5):
                offset_x = random.randint(-radius // 3, radius // 3)
                offset_y = random.randint(-radius // 3, radius // 3)
                circle_size = random.randint(radius - 5, radius + 5)
                
                draw.ellipse([center_x - circle_size // 2 + offset_x, 
                             center_y - circle_size // 2 + offset_y,
                             center_x + circle_size // 2 + offset_x, 
                             center_y + circle_size // 2 + offset_y], 
                             fill=foliage_color)
        
        # Save tree
        filename = f"assets/environment/tree_{i+1}.png"
        tree.save(filename)
        print(f"Generated tree: {filename}")
    
    # Generate grass/bush tiles (32x32 px)
    for i in range(3):
        grass_size = 32
        grass = Image.new('RGBA', (grass_size, grass_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(grass)
        
        # Base grass color
        base_color = random.choice(PALETTES["environment_green"])
        
        # Fill the tile with the base color
        draw.rectangle([0, 0, grass_size, grass_size], fill=(100, 200, 100, 100))
        
        # Add grass blades or bushes
        if i == 0:  # Simple grass
            for _ in range(20):
                start_x = random.randint(0, grass_size)
                start_y = random.randint(grass_size // 2, grass_size)
                end_x = start_x + random.randint(-5, 5)
                end_y = start_y - random.randint(5, 15)
                
                # Vary the grass color slightly
                blade_color = (
                    max(0, min(255, base_color[0] + random.randint(-20, 20))),
                    max(0, min(255, base_color[1] + random.randint(-20, 20))),
                    max(0, min(255, base_color[2] + random.randint(-20, 20)))
                )
                
                draw.line([start_x, start_y, end_x, end_y], fill=blade_color, width=2)
                
        elif i == 1:  # Small bushes
            for _ in range(3):
                bush_x = random.randint(4, grass_size - 8)
                bush_y = random.randint(4, grass_size - 8)
                bush_size = random.randint(6, 10)
                
                # Vary the bush color slightly
                bush_color = (
                    max(0, min(255, base_color[0] + random.randint(-20, 20))),
                    max(0, min(255, base_color[1] + random.randint(-20, 20))),
                    max(0, min(255, base_color[2] + random.randint(-20, 20)))
                )
                
                draw.ellipse([bush_x, bush_y, bush_x + bush_size, bush_y + bush_size], 
                            fill=bush_color)
        
        else:  # Flowers or detailed grass
            for _ in range(10):
                flower_x = random.randint(2, grass_size - 4)
                flower_y = random.randint(2, grass_size - 4)
                flower_size = random.randint(2, 4)
                
                # Random bright flower colors
                flower_color = (
                    random.randint(200, 255),
                    random.randint(100, 255),
                    random.randint(100, 255)
                )
                
                draw.ellipse([flower_x, flower_y, 
                             flower_x + flower_size, flower_y + flower_size], 
                             fill=flower_color)
                
                # Stem
                stem_color = (0, 100, 0)
                draw.line([flower_x + flower_size // 2, flower_y + flower_size, 
                          flower_x + flower_size // 2, flower_y + flower_size + random.randint(2, 6)], 
                          fill=stem_color, width=1)
        
        # Save grass/bush tile
        filename = f"assets/environment/grass_{i+1}.png"
        grass.save(filename)
        print(f"Generated grass/bush: {filename}")
    
    # Generate path tiles (32x32 px)
    for i in range(2):
        path_size = 32
        path = Image.new('RGBA', (path_size, path_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(path)
        
        # Base path color
        path_color = (210, 180, 140)  # Tan/dirt color
        
        if i == 0:  # Dirt path
            # Fill with base color
            draw.rectangle([0, 0, path_size, path_size], fill=path_color)
            
            # Add texture with small darker spots
            for _ in range(30):
                spot_x = random.randint(0, path_size - 2)
                spot_y = random.randint(0, path_size - 2)
                spot_size = random.randint(1, 3)
                
                # Darker variation of path color
                spot_color = (
                    max(0, path_color[0] - random.randint(20, 40)),
                    max(0, path_color[1] - random.randint(20, 40)),
                    max(0, path_color[2] - random.randint(20, 40))
                )
                
                draw.ellipse([spot_x, spot_y, spot_x + spot_size, spot_y + spot_size], 
                            fill=spot_color)
        
        else:  # Stone path
            # Base color - slightly darker
            stone_base = (180, 180, 180)
            draw.rectangle([0, 0, path_size, path_size], fill=stone_base)
            
            # Add individual stones
            for _ in range(10):
                stone_x = random.randint(0, path_size - 8)
                stone_y = random.randint(0, path_size - 8)
                stone_width = random.randint(5, 8)
                stone_height = random.randint(5, 8)
                
                # Stone color variation
                stone_color = (
                    random.randint(150, 200),
                    random.randint(150, 200),
                    random.randint(150, 200)
                )
                
                # Slightly rounded stone shape
                draw.rounded_rectangle([stone_x, stone_y, 
                                      stone_x + stone_width, stone_y + stone_height], 
                                      radius=2, fill=stone_color)
                
                # Add highlight
                highlight_color = (
                    min(255, stone_color[0] + 30),
                    min(255, stone_color[1] + 30),
                    min(255, stone_color[2] + 30)
                )
                
                # Small highlight on top-left corner
                draw.rounded_rectangle([stone_x + 1, stone_y + 1, 
                                      stone_x + 3, stone_y + 3], 
                                      radius=1, fill=highlight_color)
        
        # Save path tile
        filename = f"assets/environment/path_{i+1}.png"
        path.save(filename)
        print(f"Generated path: {filename}")
    
    # Generate water tiles (32x32 px, multiple frames for animation)
    water_size = 32
    num_frames = 4
    
    for frame in range(num_frames):
        water = Image.new('RGBA', (water_size, water_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(water)
        
        # Base water color
        water_color = (64, 164, 223, 200)  # Blue with transparency
        
        # Fill with base color
        draw.rectangle([0, 0, water_size, water_size], fill=water_color)
        
        # Add wave patterns based on frame
        wave_offset = frame * (math.pi / 2)
        
        for y in range(water_size):
            for x in range(water_size):
                # Create wave pattern using sine functions
                wave1 = math.sin((x / water_size * 4 * math.pi) + wave_offset) * 10
                wave2 = math.sin((y / water_size * 3 * math.pi) + wave_offset) * 10
                
                wave_value = (wave1 + wave2) / 2
                
                # Adjust pixel alpha based on wave
                pixel_alpha = int(200 + wave_value)
                pixel_alpha = max(150, min(230, pixel_alpha))
                
                # Vary the blue slightly
                blue_variation = int(200 + wave_value)
                blue_variation = max(180, min(240, blue_variation))
                
                pixel_color = (64, 164, blue_variation, pixel_alpha)
                
                # Apply the pixel color if it differs from base
                if pixel_color != water_color:
                    water.putpixel((x, y), pixel_color)
        
        # Save water frame
        filename = f"assets/environment/water_frame_{frame+1}.png"
        water.save(filename)
        print(f"Generated water frame: {filename}")

# Generate UI elements
def generate_ui_elements():
    # Status icons (16x16 px)
    icons = [
        ("health", (255, 0, 0)),    # Red heart
        ("energy", (0, 200, 255)),  # Blue energy
        ("mood", (255, 255, 0)),    # Yellow mood
        ("money", (0, 200, 0))      # Green money
    ]
    
    for icon_name, icon_color in icons:
        icon_size = 16
        icon = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(icon)
        
        if icon_name == "health":
            # Heart shape
            heart_points = [
                (icon_size//2, icon_size//4),
                (icon_size//4, icon_size//2),
                (icon_size//2, 3*icon_size//4),
                (3*icon_size//4, icon_size//2)
            ]
            draw.polygon(heart_points, fill=icon_color)
            
        elif icon_name == "energy":
            # Lightning bolt
            bolt_points = [
                (icon_size//2, 2),
                (icon_size-4, icon_size//2),
                (icon_size//2, icon_size//2),
                (4, icon_size-2)
            ]
            draw.polygon(bolt_points, fill=icon_color)
            
        elif icon_name == "mood":
            # Smiley face
            draw.ellipse([2, 2, icon_size-2, icon_size-2], outline=icon_color, width=2)
            # Eyes
            draw.ellipse([4, 5, 6, 7], fill=icon_color)
            draw.ellipse([icon_size-6, 5, icon_size-4, 7], fill=icon_color)
            # Smile
            draw.arc([4, 4, icon_size-4, icon_size-4], 0, 180, fill=icon_color, width=2)
            
        elif icon_name == "money":
            # Coin
            draw.ellipse([2, 2, icon_size-2, icon_size-2], fill=icon_color)
            # "$" symbol
            draw.line([(icon_size//2, 4), (icon_size//2, icon_size-4)], fill=(255, 255, 255), width=2)
            draw.line([(icon_size//2-2, 5), (icon_size//2+2, 5)], fill=(255, 255, 255), width=1)
            draw.line([(icon_size//2-2, icon_size-5), (icon_size//2+2, icon_size-5)], fill=(255, 255, 255), width=1)
        
        # Save icon
        filename = f"assets/ui/icon_{icon_name}.png"
        icon.save(filename)
        print(f"Generated UI icon: {filename}")
    
    # Dialog box template (resizable, 9-slice)
    dialog_size = 64
    dialog = Image.new('RGBA', (dialog_size, dialog_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(dialog)
    
    # Background with transparency
    background_color = (50, 50, 50, 220)
    draw.rectangle([0, 0, dialog_size, dialog_size], fill=background_color)
    
    # Border
    border_color = (200, 200, 200, 255)
    border_width = 2
    draw.rectangle([0, 0, dialog_size-1, dialog_size-1], outline=border_color, width=border_width)
    
    # Corner decorations
    corner_size = 8
    for x, y in [(0, 0), (0, dialog_size-corner_size), (dialog_size-corner_size, 0), (dialog_size-corner_size, dialog_size-corner_size)]:
        draw.rectangle([x, y, x+corner_size, y+corner_size], outline=border_color, width=1)
    
    # Save dialog box template
    filename = "assets/ui/dialog_template.png"
    dialog.save(filename)
    print(f"Generated UI dialog template: {filename}")

# Main function to generate all assets
def generate_all_assets():
    print("Starting asset generation for village simulation...")
    create_directories()
    
    # Generate all asset types
    generate_character_sprites(5)
    generate_buildings(4)
    generate_environment()
    generate_ui_elements()
    
    print("Asset generation complete!")

if __name__ == "__main__":
    generate_all_assets()