import pygame
import random
import math

class BuildingInteriors:
    def __init__(self, tile_size=32):
        """Initialize the building interiors system.
        
        Args:
            tile_size: Size of a tile in pixels
        """
        self.tile_size = tile_size
        self.interiors = {}  # Dictionary to store interior data for each building
        
        # Define colors
        self.wall_color = (60, 60, 60)
        self.floor_color = (120, 100, 80)
        self.border_color = (40, 40, 40)
        
        # Furniture colors by type
        self.furniture_colors = {
            'bed': (150, 150, 200),
            'table': (120, 80, 50),
            'chair': (140, 100, 60),
            'hearth': (200, 100, 50),
            'oven': (180, 100, 60),
            'counter': (160, 120, 80),
            'chest': (110, 70, 40),
            'bookshelf': (130, 90, 50),
            'barrel': (120, 90, 70),
            'anvil': (80, 80, 90),
            'forge': (200, 80, 40),
            'workbench': (130, 100, 60)
        }
    
    def generate_interiors(self, buildings):
        """Generate interiors for all buildings.
        
        Args:
            buildings: List of building dictionaries
        """
        for i, building in enumerate(buildings):
            building_type = building.get('building_type', 'House')
            size = building['size']
            position = building['position']
            
            # Adjust scale based on building size
            if size == 'small':
                scale = 1
            elif size == 'medium':
                scale = 2
            else:  # large
                scale = 3
                
            pixels_size = scale * self.tile_size
            
            # Generate interior based on building type
            if building_type in ['House', 'Cottage', 'Manor']:
                self.interiors[i] = self._generate_house_interior(
                    position, pixels_size, scale)
            elif building_type in ['Bakery']:
                self.interiors[i] = self._generate_bakery_interior(
                    position, pixels_size, scale)
            elif building_type in ['Inn', 'Tavern']:
                self.interiors[i] = self._generate_inn_interior(
                    position, pixels_size, scale)
            elif building_type in ['Store', 'Market']:
                self.interiors[i] = self._generate_store_interior(
                    position, pixels_size, scale)
            elif building_type in ['Smithy', 'Workshop']:
                self.interiors[i] = self._generate_workshop_interior(
                    position, pixels_size, scale, building_type)
            else:
                # Default interior for other types
                self.interiors[i] = self._generate_basic_interior(
                    position, pixels_size, scale)
    
    def _generate_house_interior(self, position, size, scale):
        """Generate interior for a house-type building.
        
        Args:
            position: (x, y) position of building
            size: Size of building in pixels
            scale: Scale factor (1 for small, 2 for medium, 3 for large)
            
        Returns:
            Dictionary with interior data
        """
        interior = {
            'walls': [],
            'furniture': []
        }
        
        # Calculate padding from edge
        padding = max(2, int(size * 0.1))
        inner_size = size - padding * 2
        
        # Add bed
        bed_width = max(6, int(inner_size * 0.25))
        bed_height = max(12, int(inner_size * 0.4))
        bed_x = position[0] + padding + inner_size - bed_width - 2
        bed_y = position[1] + padding + 2
        
        interior['furniture'].append({
            'type': 'bed',
            'rect': pygame.Rect(bed_x, bed_y, bed_width, bed_height),
            'color': self.furniture_colors['bed']
        })
        
        # Add table if medium or large
        if scale >= 2:
            table_size = max(8, int(inner_size * 0.3))
            table_x = position[0] + padding + 2
            table_y = position[1] + padding + inner_size - table_size - 2
            
            interior['furniture'].append({
                'type': 'table',
                'rect': pygame.Rect(table_x, table_y, table_size, table_size),
                'color': self.furniture_colors['table']
            })
            
            # Add chair(s)
            chair_size = max(4, int(table_size * 0.4))
            
            # Chair on right side of table
            chair_x = table_x + table_size + 1
            chair_y = table_y + (table_size - chair_size) // 2
            
            interior['furniture'].append({
                'type': 'chair',
                'rect': pygame.Rect(chair_x, chair_y, chair_size, chair_size),
                'color': self.furniture_colors['chair']
            })
        
        # Add hearth on left side
        hearth_size = max(6, int(inner_size * 0.25))
        hearth_x = position[0] + padding + 2
        hearth_y = position[1] + padding + 2
        
        interior['furniture'].append({
            'type': 'hearth',
            'rect': pygame.Rect(hearth_x, hearth_y, hearth_size, hearth_size),
            'color': self.furniture_colors['hearth']
        })
        
        # Add chest if large house
        if scale >= 3:
            chest_width = max(6, int(inner_size * 0.2))
            chest_height = max(4, int(inner_size * 0.12))
            chest_x = position[0] + padding + inner_size - chest_width - 2
            chest_y = position[1] + padding + inner_size - chest_height - 2
            
            interior['furniture'].append({
                'type': 'chest',
                'rect': pygame.Rect(chest_x, chest_y, chest_width, chest_height),
                'color': self.furniture_colors['chest']
            })
            
            # Add bookshelf
            shelf_width = max(4, int(inner_size * 0.15))
            shelf_height = max(10, int(inner_size * 0.3))
            shelf_x = position[0] + padding + inner_size // 2 - shelf_width // 2
            shelf_y = position[1] + padding + 2
            
            interior['furniture'].append({
                'type': 'bookshelf',
                'rect': pygame.Rect(shelf_x, shelf_y, shelf_width, shelf_height),
                'color': self.furniture_colors['bookshelf']
            })
        
        return interior
    
    def _generate_bakery_interior(self, position, size, scale):
        """Generate interior for a bakery.
        
        Args:
            position: (x, y) position of building
            size: Size of building in pixels
            scale: Scale factor (1 for small, 2 for medium, 3 for large)
            
        Returns:
            Dictionary with interior data
        """
        interior = {
            'walls': [],
            'furniture': []
        }
        
        # Calculate padding from edge
        padding = max(2, int(size * 0.1))
        inner_size = size - padding * 2
        
        # Add oven
        oven_size = max(10, int(inner_size * 0.3))
        oven_x = position[0] + padding + inner_size - oven_size - 2
        oven_y = position[1] + padding + 2
        
        interior['furniture'].append({
            'type': 'oven',
            'rect': pygame.Rect(oven_x, oven_y, oven_size, oven_size),
            'color': self.furniture_colors['oven']
        })
        
        # Add counter
        counter_height = max(6, int(inner_size * 0.15))
        counter_width = max(12, int(inner_size * 0.6))
        counter_x = position[0] + padding + 2
        counter_y = position[1] + padding + inner_size - counter_height - 2
        
        interior['furniture'].append({
            'type': 'counter',
            'rect': pygame.Rect(counter_x, counter_y, counter_width, counter_height),
            'color': self.furniture_colors['counter']
        })
        
        # Add table for dough
        table_size = max(8, int(inner_size * 0.25))
        table_x = position[0] + padding + 2
        table_y = position[1] + padding + 2
        
        interior['furniture'].append({
            'type': 'table',
            'rect': pygame.Rect(table_x, table_y, table_size, table_size),
            'color': self.furniture_colors['table']
        })
        
        # Add barrels if larger building
        if scale >= 2:
            barrel_size = max(6, int(inner_size * 0.15))
            
            # First barrel
            barrel_x = position[0] + padding + inner_size - barrel_size - 2
            barrel_y = position[1] + padding + inner_size - barrel_size - 2
            
            interior['furniture'].append({
                'type': 'barrel',
                'rect': pygame.Rect(barrel_x, barrel_y, barrel_size, barrel_size),
                'color': self.furniture_colors['barrel']
            })
            
            # Second barrel if enough space
            if scale >= 3:
                barrel_x -= barrel_size + 2
                
                interior['furniture'].append({
                    'type': 'barrel',
                    'rect': pygame.Rect(barrel_x, barrel_y, barrel_size, barrel_size),
                    'color': self.furniture_colors['barrel']
                })
        
        return interior
    
    def _generate_inn_interior(self, position, size, scale):
        """Generate interior for an inn or tavern.
        
        Args:
            position: (x, y) position of building
            size: Size of building in pixels
            scale: Scale factor (1 for small, 2 for medium, 3 for large)
            
        Returns:
            Dictionary with interior data
        """
        interior = {
            'walls': [],
            'furniture': []
        }
        
        # Calculate padding from edge
        padding = max(2, int(size * 0.1))
        inner_size = size - padding * 2
        
        # Add counter/bar
        counter_height = max(6, int(inner_size * 0.15))
        counter_width = max(20, int(inner_size * 0.7))
        counter_x = position[0] + padding + inner_size // 2 - counter_width // 2
        counter_y = position[1] + padding + 2
        
        interior['furniture'].append({
            'type': 'counter',
            'rect': pygame.Rect(counter_x, counter_y, counter_width, counter_height),
            'color': self.furniture_colors['counter']
        })
        
        # Add tables
        table_size = max(8, int(inner_size * 0.2))
        
        # Table positions - arrange in a grid
        num_tables = min(4, scale * 2)  # More tables for larger inns
        tables_per_row = 2
        
        for i in range(num_tables):
            row = i // tables_per_row
            col = i % tables_per_row
            
            spacing_x = (inner_size - table_size * tables_per_row) // (tables_per_row + 1)
            spacing_y = (inner_size - counter_height - table_size * (num_tables // tables_per_row)) // ((num_tables // tables_per_row) + 1)
            
            table_x = position[0] + padding + spacing_x + col * (table_size + spacing_x)
            table_y = position[1] + padding + counter_height + spacing_y + row * (table_size + spacing_y)
            
            interior['furniture'].append({
                'type': 'table',
                'rect': pygame.Rect(table_x, table_y, table_size, table_size),
                'color': self.furniture_colors['table']
            })
            
            # Add chairs around this table
            chair_size = max(4, int(table_size * 0.4))
            
            # Chair positions (top, right, bottom, left)
            chair_positions = [
                (table_x + (table_size - chair_size) // 2, table_y - chair_size - 1),
                (table_x + table_size + 1, table_y + (table_size - chair_size) // 2),
                (table_x + (table_size - chair_size) // 2, table_y + table_size + 1),
                (table_x - chair_size - 1, table_y + (table_size - chair_size) // 2)
            ]
            
            # Add 2-4 chairs around each table
            num_chairs = random.randint(2, 4)
            chair_indices = random.sample(range(4), num_chairs)
            
            for idx in chair_indices:
                chair_x, chair_y = chair_positions[idx]
                
                # Check if chair is within bounds
                if (position[0] + padding <= chair_x < position[0] + padding + inner_size - chair_size and
                    position[1] + padding <= chair_y < position[1] + padding + inner_size - chair_size):
                    interior['furniture'].append({
                        'type': 'chair',
                        'rect': pygame.Rect(chair_x, chair_y, chair_size, chair_size),
                        'color': self.furniture_colors['chair']
                    })
        
        # Add barrels
        if scale >= 2:
            barrel_size = max(6, int(inner_size * 0.15))
            barrel_x = position[0] + padding + inner_size - barrel_size - 2
            barrel_y = position[1] + padding + 2
            
            interior['furniture'].append({
                'type': 'barrel',
                'rect': pygame.Rect(barrel_x, barrel_y, barrel_size, barrel_size),
                'color': self.furniture_colors['barrel']
            })
            
            # Second barrel
            if scale >= 3:
                barrel_x -= barrel_size + 2
                
                interior['furniture'].append({
                    'type': 'barrel',
                    'rect': pygame.Rect(barrel_x, barrel_y, barrel_size, barrel_size),
                    'color': self.furniture_colors['barrel']
                })
        
        # Add hearth if large inn
        if scale >= 3:
            hearth_size = max(8, int(inner_size * 0.2))
            hearth_x = position[0] + padding + 2
            hearth_y = position[1] + padding + 2
            
            interior['furniture'].append({
                'type': 'hearth',
                'rect': pygame.Rect(hearth_x, hearth_y, hearth_size, hearth_size),
                'color': self.furniture_colors['hearth']
            })
        
        return interior
    
    def _generate_store_interior(self, position, size, scale):
        """Generate interior for a store or market.
        
        Args:
            position: (x, y) position of building
            size: Size of building in pixels
            scale: Scale factor (1 for small, 2 for medium, 3 for large)
            
        Returns:
            Dictionary with interior data
        """
        interior = {
            'walls': [],
            'furniture': []
        }
        
        # Calculate padding from edge
        padding = max(2, int(size * 0.1))
        inner_size = size - padding * 2
        
        # Add counter
        counter_height = max(6, int(inner_size * 0.15))
        counter_width = max(16, int(inner_size * 0.6))
        counter_x = position[0] + padding + inner_size // 2 - counter_width // 2
        counter_y = position[1] + padding + inner_size // 2
        
        interior['furniture'].append({
            'type': 'counter',
            'rect': pygame.Rect(counter_x, counter_y, counter_width, counter_height),
            'color': self.furniture_colors['counter']
        })
        
        # Add shelves along walls
        shelf_width = max(4, int(inner_size * 0.15))
        shelf_height = max(inner_size - 10, inner_size * 0.8)
        
        # Left shelf
        shelf_x = position[0] + padding + 2
        shelf_y = position[1] + padding + (inner_size - shelf_height) // 2
        
        interior['furniture'].append({
            'type': 'bookshelf',  # Using bookshelf for store shelves
            'rect': pygame.Rect(shelf_x, shelf_y, shelf_width, shelf_height),
            'color': self.furniture_colors['bookshelf']
        })
        
        # Right shelf
        shelf_x = position[0] + padding + inner_size - shelf_width - 2
        
        interior['furniture'].append({
            'type': 'bookshelf',
            'rect': pygame.Rect(shelf_x, shelf_y, shelf_width, shelf_height),
            'color': self.furniture_colors['bookshelf']
        })
        
        # Add barrels or chests
        if scale >= 2:
            item_size = max(6, int(inner_size * 0.15))
            
            # First item (barrel)
            item_x = position[0] + padding + 2 + shelf_width + 2
            item_y = position[1] + padding + 2
            
            interior['furniture'].append({
                'type': 'barrel',
                'rect': pygame.Rect(item_x, item_y, item_size, item_size),
                'color': self.furniture_colors['barrel']
            })
            
            # Second item (chest)
            if scale >= 3:
                chest_width = max(8, int(inner_size * 0.2))
                chest_height = max(6, int(inner_size * 0.15))
                chest_x = position[0] + padding + inner_size - shelf_width - chest_width - 4
                chest_y = position[1] + padding + 2
                
                interior['furniture'].append({
                    'type': 'chest',
                    'rect': pygame.Rect(chest_x, chest_y, chest_width, chest_height),
                    'color': self.furniture_colors['chest']
                })
        
        return interior
    
    def _generate_workshop_interior(self, position, size, scale, building_type):
        """Generate interior for a workshop or smithy.
        
        Args:
            position: (x, y) position of building
            size: Size of building in pixels
            scale: Scale factor (1 for small, 2 for medium, 3 for large)
            building_type: Type of building ('Smithy' or other workshop)
            
        Returns:
            Dictionary with interior data
        """
        interior = {
            'walls': [],
            'furniture': []
        }
        
        # Calculate padding from edge
        padding = max(2, int(size * 0.1))
        inner_size = size - padding * 2
        
        # Add workbench
        bench_width = max(18, int(inner_size * 0.6))
        bench_height = max(8, int(inner_size * 0.2))
        bench_x = position[0] + padding + (inner_size - bench_width) // 2
        bench_y = position[1] + padding + inner_size - bench_height - 2
        
        interior['furniture'].append({
            'type': 'workbench',
            'rect': pygame.Rect(bench_x, bench_y, bench_width, bench_height),
            'color': self.furniture_colors['workbench']
        })
        
        # For smithy, add forge and anvil
        if 'Smithy' in building_type:
            # Add forge
            forge_size = max(10, int(inner_size * 0.25))
            forge_x = position[0] + padding + 2
            forge_y = position[1] + padding + 2
            
            interior['furniture'].append({
                'type': 'forge',
                'rect': pygame.Rect(forge_x, forge_y, forge_size, forge_size),
                'color': self.furniture_colors['forge']
            })
            
            # Add anvil
            anvil_width = max(8, int(inner_size * 0.2))
            anvil_height = max(4, int(inner_size * 0.1))
            anvil_x = position[0] + padding + forge_size + 4
            anvil_y = position[1] + padding + forge_size - anvil_height - 2
            
            interior['furniture'].append({
                'type': 'anvil',
                'rect': pygame.Rect(anvil_x, anvil_y, anvil_width, anvil_height),
                'color': self.furniture_colors['anvil']
            })
        else:
            # Add tables for other workshop types
            table_size = max(12, int(inner_size * 0.3))
            table_x = position[0] + padding + (inner_size - table_size) // 2
            table_y = position[1] + padding + 2
            
            interior['furniture'].append({
                'type': 'table',
                'rect': pygame.Rect(table_x, table_y, table_size, table_size),
                'color': self.furniture_colors['table']
            })
        
        # Add storage along one wall
        shelf_width = max(4, int(inner_size * 0.15))
        shelf_height = max(inner_size - 20, inner_size * 0.6)
        shelf_x = position[0] + padding + inner_size - shelf_width - 2
        shelf_y = position[1] + padding + (inner_size - shelf_height) // 2
        
        if scale >= 2:
            interior['furniture'].append({
                'type': 'bookshelf',  # Using bookshelf for storage
                'rect': pygame.Rect(shelf_x, shelf_y, shelf_width, shelf_height),
                'color': self.furniture_colors['bookshelf']
            })
        
        return interior
    
    def _generate_basic_interior(self, position, size, scale):
        """Generate a basic interior for any building type.
        
        Args:
            position: (x, y) position of building
            size: Size of building in pixels
            scale: Scale factor (1 for small, 2 for medium, 3 for large)
            
        Returns:
            Dictionary with interior data
        """
        interior = {
            'walls': [],
            'furniture': []
        }
        
        # Calculate padding from edge
        padding = max(2, int(size * 0.1))
        inner_size = size - padding * 2
        
        # Add a table in the center
        table_size = max(12, int(inner_size * 0.4))
        table_x = position[0] + padding + (inner_size - table_size) // 2
        table_y = position[1] + padding + (inner_size - table_size) // 2
        
        interior['furniture'].append({
            'type': 'table',
            'rect': pygame.Rect(table_x, table_y, table_size, table_size),
            'color': self.furniture_colors['table']
        })
        
        # Add some basic furniture based on building size
        if scale >= 2:
            # Add chest
            chest_width = max(8, int(inner_size * 0.2))
            chest_height = max(5, int(inner_size * 0.15))
            chest_x = position[0] + padding + 2
            chest_y = position[1] + padding + 2
            
            interior['furniture'].append({
                'type': 'chest',
                'rect': pygame.Rect(chest_x, chest_y, chest_width, chest_height),
                'color': self.furniture_colors['chest']
            })
        
        if scale >= 3:
            # Add hearth for large buildings
            hearth_size = max(8, int(inner_size * 0.2))
            hearth_x = position[0] + padding + inner_size - hearth_size - 2
            hearth_y = position[1] + padding + 2
            
            interior['furniture'].append({
                'type': 'hearth',
                'rect': pygame.Rect(hearth_x, hearth_y, hearth_size, hearth_size),
                'color': self.furniture_colors['hearth']
            })
        
        return interior
    
    def render_interiors(self, surface, buildings, camera_x, camera_y):
        """Render interiors for all visible buildings.
        
        Args:
            surface: Surface to render on
            buildings: List of building dictionaries
            camera_x: Camera X position
            camera_y: Camera Y position
        """
        for i, building in enumerate(buildings):
            # Skip if building doesn't have interior data
            if i not in self.interiors:
                continue
                
            position = building['position']
            size = building['size']
            
            # Adjust scale based on building size
            if size == 'small':
                scale = 1
                pixels_size = self.tile_size
            elif size == 'medium':
                scale = 2
                pixels_size = self.tile_size * 2
            else:  # large
                scale = 3
                pixels_size = self.tile_size * 3
            
            # Check if building is visible on screen
            if (position[0] + pixels_size < camera_x or 
                position[0] > camera_x + surface.get_width() or
                position[1] + pixels_size < camera_y or
                position[1] > camera_y + surface.get_height()):
                continue
            
            # Draw floor
            floor_rect = pygame.Rect(
                position[0] - camera_x,
                position[1] - camera_y,
                pixels_size,
                pixels_size
            )
            pygame.draw.rect(surface, self.floor_color, floor_rect)
            pygame.draw.rect(surface, self.border_color, floor_rect, 1)
            
            # Draw interior walls if any
            interior = self.interiors[i]
            for wall in interior['walls']:
                points = [(p[0] - camera_x, p[1] - camera_y) for p in wall['points']]
                pygame.draw.polygon(surface, wall['color'], points)
            
            # Draw furniture
            for furniture in interior['furniture']:
                furniture_rect = pygame.Rect(
                    furniture['rect'].x - camera_x,
                    furniture['rect'].y - camera_y,
                    furniture['rect'].width,
                    furniture['rect'].height
                )
                pygame.draw.rect(surface, furniture['color'], furniture_rect)
                pygame.draw.rect(surface, self.border_color, furniture_rect, 1)
                
                # Add details based on furniture type
                furniture_type = furniture['type']
                
                if furniture_type == 'bed':
                    # Draw pillow
                    pillow_width = min(4, furniture['rect'].width // 2)
                    pillow_height = min(3, furniture['rect'].height // 3)
                    pillow_rect = pygame.Rect(
                        furniture['rect'].x - camera_x + (furniture['rect'].width - pillow_width) // 2,
                        furniture['rect'].y - camera_y + 2,
                        pillow_width,
                        pillow_height
                    )
                    pygame.draw.rect(surface, (240, 240, 240), pillow_rect)
                
                elif furniture_type == 'table':
                    # Draw table surface lines
                    line_color = (min(furniture['color'][0] - 20, 255),
                                min(furniture['color'][1] - 20, 255),
                                min(furniture['color'][2] - 20, 255))
                    
                    # Horizontal line
                    pygame.draw.line(
                        surface,
                        line_color,
                        (furniture_rect.left, furniture_rect.centery),
                        (furniture_rect.right, furniture_rect.centery),
                        1
                    )
                    
                    # Vertical line
                    pygame.draw.line(
                        surface,
                        line_color,
                        (furniture_rect.centerx, furniture_rect.top),
                        (furniture_rect.centerx, furniture_rect.bottom),
                        1
                    )
                
                elif furniture_type == 'hearth':
                    # Draw fire
                    fire_color = (220, 130, 30)
                    fire_rect = pygame.Rect(
                        furniture_rect.left + 2,
                        furniture_rect.top + 2,
                        furniture_rect.width - 4,
                        furniture_rect.height - 4
                    )
                    pygame.draw.rect(surface, fire_color, fire_rect)
                
                elif furniture_type == 'oven':
                    # Draw oven door
                    door_color = (60, 60, 60)
                    door_rect = pygame.Rect(
                        furniture_rect.left + furniture_rect.width // 4,
                        furniture_rect.top + furniture_rect.height // 4,
                        furniture_rect.width // 2,
                        furniture_rect.height // 2
                    )
                    pygame.draw.rect(surface, door_color, door_rect)
                    pygame.draw.rect(surface, (0, 0, 0), door_rect, 1)
                
                elif furniture_type == 'bookshelf':
                    # Draw shelf lines
                    shelf_color = (min(furniture['color'][0] - 30, 255),
                                min(furniture['color'][1] - 30, 255),
                                min(furniture['color'][2] - 30, 255))
                    
                    # Draw horizontal shelf lines
                    num_shelves = 3
                    for i in range(1, num_shelves):
                        y_pos = furniture_rect.top + (furniture_rect.height * i) // num_shelves
                        pygame.draw.line(
                            surface,
                            shelf_color,
                            (furniture_rect.left, y_pos),
                            (furniture_rect.right, y_pos),
                            1
                        )
                
                elif furniture_type == 'forge':
                    # Draw fire
                    fire_color = (220, 130, 30)
                    fire_rect = pygame.Rect(
                        furniture_rect.left + 2,
                        furniture_rect.top + 2,
                        furniture_rect.width - 4,
                        furniture_rect.height - 4
                    )
                    pygame.draw.rect(surface, fire_color, fire_rect)
                    
                    # Draw chimney
                    chimney_width = max(3, furniture_rect.width // 4)
                    chimney_height = max(4, furniture_rect.height // 3)
                    chimney_rect = pygame.Rect(
                        furniture_rect.left + (furniture_rect.width - chimney_width) // 2,
                        furniture_rect.top - chimney_height + 2,
                        chimney_width,
                        chimney_height
                    )
                    
                    if 0 <= chimney_rect.left and 0 <= chimney_rect.top and chimney_rect.right <= surface.get_width() and chimney_rect.bottom <= surface.get_height():
                        pygame.draw.rect(surface, (80, 80, 80), chimney_rect)
                        pygame.draw.rect(surface, (0, 0, 0), chimney_rect, 1)
    
    def get_furniture_in_building(self, building_id, furniture_type=None):
        """Get a list of furniture in a building.
        
        Args:
            building_id: Building ID
            furniture_type: Optional type to filter by
            
        Returns:
            List of furniture dictionaries
        """
        if building_id not in self.interiors:
            return []
            
        if furniture_type is None:
            return self.interiors[building_id]['furniture']
        else:
            return [f for f in self.interiors[building_id]['furniture'] 
                  if f['type'] == furniture_type]
    
    def get_furniture_at_position(self, position, building_id):
        """Get furniture at a specific position in a building.
        
        Args:
            position: (x, y) position to check
            building_id: Building ID
            
        Returns:
            Furniture dictionary or None if no furniture at position
        """
        if building_id not in self.interiors:
            return None
            
        for furniture in self.interiors[building_id]['furniture']:
            if furniture['rect'].collidepoint(position):
                return furniture
                
        return None
                    fire