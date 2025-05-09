import traceback
import sys

import pygame
import math

class Renderer:
    def __init__(self, screen, assets, screen_width, screen_height, tile_size):
        """Initialize the renderer.
        
        Args:
            screen: Pygame screen object
            assets: Dictionary of game assets
            screen_width: Width of the game screen
            screen_height: Height of the game screen
            tile_size: Size of a tile in pixels
        """
        self.screen = screen
        self.assets = assets
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.tile_size = tile_size
        
        # Define colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GREEN = (100, 200, 100)
        self.BLUE = (100, 100, 200)
    
    def render_village(self, village_data, villagers, camera_x, camera_y, ui_manager, selected_villager, 
                    hovered_building, show_debug, clock, water_frame, 
                    console_active=False, console_height=0, time_manager=None):
        """Render the entire village and UI."""
        try:
            
            self.screen.fill(self.GREEN)
            
            
            # Calculate visible area based on camera position
            
            visible_left = camera_x // self.tile_size
            visible_right = (camera_x + self.screen_width) // self.tile_size + 1
            visible_top = camera_y // self.tile_size
            visible_bottom = (camera_y + self.screen_height) // self.tile_size + 1
            
            # Limit to village size
            
            visible_left = max(0, visible_left)
            visible_right = min(village_data['width'] // self.tile_size, visible_right)
            visible_top = max(0, visible_top)
            visible_bottom = min(village_data['height'] // self.tile_size, visible_bottom)
            
            # Render all world elements
            
            self._render_terrain(village_data, visible_left, visible_right, visible_top, visible_bottom, camera_x, camera_y)
            
            
            self._render_paths(village_data, visible_left, visible_right, visible_top, visible_bottom, camera_x, camera_y)
            
            
            self._render_water(village_data, visible_left, visible_right, visible_top, visible_bottom, camera_x, camera_y, water_frame)
            
            
            self._render_bridges(village_data, visible_left, visible_right, visible_top, visible_bottom, camera_x, camera_y)
            
            # Get current shadow length from time manager if available
            shadow_length = 0
            if time_manager:            
                shadow_length = time_manager.get_shadow_length()
                
            # Render shadows first if it's daytime
            if shadow_length > 0:            
                self._render_shadows(village_data, villagers, visible_left, visible_right, visible_top, visible_bottom, 
                                    camera_x, camera_y, shadow_length)
                
            
            self._render_buildings(village_data, visible_left, visible_right, visible_top, visible_bottom, camera_x, camera_y, ui_manager)
            
            
            self._render_trees(village_data, visible_left, visible_right, visible_top, visible_bottom, camera_x, camera_y)
            
            
            self._render_villagers(villagers, camera_x, camera_y)
            
            # Apply day/night lighting overlay
            if time_manager:
            
                darkness_overlay = time_manager.get_darkness_overlay(self.screen_width, self.screen_height)
                self.screen.blit(darkness_overlay, (0, 0))
            
            # Render UI elements
            
            ui_manager.draw_selected_villager_info(selected_villager, self.tile_size)
            
            # Only draw minimap if console is not active or if it doesn't overlap console area
            if not console_active:
            
                ui_manager.draw_minimap(village_data, villagers, camera_x, camera_y, self.tile_size)
            else:
                # Draw minimap in upper right corner instead if console is active
            
                ui_manager.draw_minimap(village_data, villagers, camera_x, camera_y, self.tile_size, 
                                    position='upper_right')
            
            if hovered_building:
            
                ui_manager.draw_building_info(hovered_building, camera_x, camera_y)
                
            if show_debug:
            
                ui_manager.draw_debug_info(clock, villagers, camera_x, camera_y, village_data['width'],village_data['height'])
                
            # Draw time of day if time manager exists
            if time_manager:
            
                # Create a background for the time display
                time_text = time_manager.get_time_string()
                time_surface = ui_manager.font.render(time_text, True, self.WHITE)
                time_x = 10
                time_y = self.screen_height - 30
                
                # Don't draw over console
                if console_active and time_y > self.screen_height - console_height:
                    time_y = self.screen_height - console_height - 30
                
                bg_rect = pygame.Rect(time_x - 5, time_y - 5, 
                                    time_surface.get_width() + 10, 
                                    time_surface.get_height() + 10)
                pygame.draw.rect(self.screen, (0, 0, 0, 150), bg_rect)
                pygame.draw.rect(self.screen, (100, 100, 100), bg_rect, 1)
                
                # Draw the time string
                self.screen.blit(time_surface, (time_x, time_y))            
        except Exception as e:
            print(f"ERROR in render_village: {e}")
            import traceback
            traceback.print_exc()

    
    def update_viewport(self, screen_width, screen_height):
        """Update renderer viewport when screen size changes.
        
        Args:
            screen_width: New screen width
            screen_height: New screen height
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # IMPORTANT: The screen reference might have changed, update it
        self.screen = pygame.display.get_surface()
        
        # If we have an overlay surface that depends on screen size, update it
        if hasattr(self, 'overlay_surface'):
            self.overlay_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        
        print(f"Renderer viewport updated to {screen_width}x{screen_height}")


    def _render_terrain(self, village_data, visible_left, visible_right, visible_top, visible_bottom, camera_x, camera_y):
        """Render terrain (grass)."""
        for y in range(visible_top, visible_bottom):
            for x in range(visible_left, visible_right):
                pos = (x * self.tile_size, y * self.tile_size)
                if pos in village_data['terrain']:
                    terrain_tile = village_data['terrain'][pos]
                    if terrain_tile['type'] == 'grass':
                        variant = terrain_tile['variant']
                        try:
                            grass_img = self.assets['environment'][f'grass_{variant}']
                            self.screen.blit(grass_img, (pos[0] - camera_x, pos[1] - camera_y))
                        except KeyError:
                            # Fallback if grass texture is missing
                            pygame.draw.rect(self.screen, self.GREEN, 
                                           (pos[0] - camera_x, pos[1] - camera_y, 
                                            self.tile_size, self.tile_size))
    
    def _render_paths(self, village_data, visible_left, visible_right, visible_top, visible_bottom, camera_x, camera_y):
        """Render paths."""
        for path in village_data['paths']:
            x, y = path['position']
            if (visible_left * self.tile_size <= x <= visible_right * self.tile_size and
                visible_top * self.tile_size <= y <= visible_bottom * self.tile_size):
                try:
                    path_img = self.assets['environment'][f"path_{path['variant']}"]
                    self.screen.blit(path_img, (x - camera_x, y - camera_y))
                except KeyError:
                    # Fallback if path texture is missing
                    pygame.draw.rect(self.screen, (200, 180, 140), 
                                   (x - camera_x, y - camera_y, 
                                    self.tile_size, self.tile_size))
    
    def _render_water(self, village_data, visible_left, visible_right, visible_top, visible_bottom, camera_x, camera_y, water_frame):
        """Render water with animation."""
        for water_tile in village_data['water']:
            x, y = water_tile['position']
            if (visible_left * self.tile_size <= x <= visible_right * self.tile_size and
                visible_top * self.tile_size <= y <= visible_bottom * self.tile_size):
                try:
                    if self.assets['environment']['water']:
                        water_img = self.assets['environment']['water'][water_frame]
                        self.screen.blit(water_img, (x - camera_x, y - camera_y))
                except (KeyError, IndexError):
                    # Fallback if water texture is missing
                    pygame.draw.rect(self.screen, self.BLUE, 
                                   (x - camera_x, y - camera_y, 
                                    self.tile_size, self.tile_size))
                                    
    def _render_shadows(self, village_data, villagers, visible_left, visible_right, visible_top, visible_bottom, 
                       camera_x, camera_y, shadow_length):
        """Render shadows for trees, buildings, and villagers."""
        # Shadow color with transparency
        shadow_color = (0, 0, 0, 80)
        
        # Create shadow offset based on time of day
        # Morning: shadows to the west (right)
        # Afternoon: shadows to the east (left)
        shadow_angle = math.pi / 4  # 45 degrees
        shadow_dx = math.cos(shadow_angle) * shadow_length * self.tile_size
        shadow_dy = math.sin(shadow_angle) * shadow_length * self.tile_size
        
        # Create a surface for shadows
        shadow_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        
        # Render building shadows
        for building in village_data['buildings']:
            x, y = building['position']
            if ((visible_left - 3) * self.tile_size <= x <= visible_right * self.tile_size and
                (visible_top - 3) * self.tile_size <= y <= visible_bottom * self.tile_size):
                
                # Get building size
                building_size = self.tile_size * 3 if building['size'] == 'large' else (
                              self.tile_size * 2 if building['size'] == 'medium' else self.tile_size)
                
                # Calculate shadow points
                shadow_x = x - camera_x + shadow_dx
                shadow_y = y - camera_y + shadow_dy
                
                # Draw shadow as a polygon
                points = [
                    (x - camera_x, y - camera_y + building_size),  # Bottom left of building
                    (x - camera_x + building_size, y - camera_y + building_size),  # Bottom right of building
                    (shadow_x + building_size, shadow_y + building_size),  # Bottom right of shadow
                    (shadow_x, shadow_y + building_size)  # Bottom left of shadow
                ]
                
                pygame.draw.polygon(shadow_surface, shadow_color, points)
        
        # Render tree shadows
        for tree in village_data['trees']:
            x, y = tree['position']
            if (visible_left * self.tile_size <= x <= visible_right * self.tile_size and
                visible_top * self.tile_size <= y <= visible_bottom * self.tile_size):
                
                # Calculate shadow points for a circular shadow
                center_x = x - camera_x + self.tile_size // 2
                center_y = y - camera_y + self.tile_size // 2
                shadow_x = center_x + shadow_dx
                shadow_y = center_y + shadow_dy
                
                # Draw an elliptical shadow
                ellipse_rect = pygame.Rect(
                    shadow_x - self.tile_size // 2, 
                    shadow_y - self.tile_size // 4,
                    self.tile_size,
                    self.tile_size // 2
                )
                
                pygame.draw.ellipse(shadow_surface, shadow_color, ellipse_rect)
        
        # Render villager shadows
        for villager in villagers:
            if (camera_x - self.tile_size <= villager.rect.x <= camera_x + self.screen_width and
                camera_y - self.tile_size <= villager.rect.y <= camera_y + self.screen_height):
                
                # Calculate shadow position
                center_x = villager.rect.centerx - camera_x
                center_y = villager.rect.bottom - camera_y
                shadow_x = center_x + shadow_dx
                shadow_y = center_y + shadow_dy
                
                # Draw an elliptical shadow
                ellipse_rect = pygame.Rect(
                    shadow_x - 10, 
                    shadow_y - 5,
                    20,
                    10
                )
                
                pygame.draw.ellipse(shadow_surface, shadow_color, ellipse_rect)
        
        # Blit the shadow surface onto the screen
        self.screen.blit(shadow_surface, (0, 0))

    def _render_buildings(self, village_data, visible_left, visible_right, visible_top, visible_bottom, camera_x, camera_y, ui_manager, selected_villager=None):
        """Render buildings and their indicators with improved safety."""
        try:
            # Check surface validity before proceeding
            if self.screen is None or not pygame.display.get_surface():
                print("Cannot render buildings - invalid screen surface")
                return
                
            # Initialize the home and workplace IDs
            home_id = None
            workplace_id = None
            
            # Get home and workplace IDs if a villager is selected
            if selected_villager:
                if hasattr(selected_villager, 'home') and selected_villager.home and 'id' in selected_villager.home:
                    home_id = selected_villager.home['id']
                    
                if hasattr(selected_villager, 'workplace') and selected_villager.workplace and 'id' in selected_villager.workplace:
                    workplace_id = selected_villager.workplace['id']
            
            # First pass: draw normal buildings
            for building_index, building in enumerate(village_data['buildings']):
                try:
                    # Skip if this is a special highlight building (we'll draw it in second pass)
                    if home_id is not None and building_index == home_id:
                        continue
                        
                    if workplace_id is not None and building_index == workplace_id:
                        continue
                        
                    x, y = building['position']
                    building_size = self.tile_size * 3 if building['size'] == 'large' else (
                                self.tile_size * 2 if building['size'] == 'medium' else self.tile_size)
                    
                    # Check if building is in visible area (with buffer for larger buildings)
                    if ((visible_left - 3) * self.tile_size <= x <= visible_right * self.tile_size and
                        (visible_top - 3) * self.tile_size <= y <= visible_bottom * self.tile_size):
                        
                        # Render the building texture
                        self._find_and_render_building_texture(building, x, y, camera_x, camera_y)
                        
                        # Draw building type indicator safely
                        try:
                            # Create a local proxy function with explicit safety checks
                            def safe_draw_indicator(building, x, y, camera_x, camera_y, tile_size):
                                try:
                                    # Enhanced safety check
                                    if not pygame.display.get_init() or self.screen is None:
                                        return
                                        
                                    ui_manager.draw_building_type_indicator(
                                        building, x, y, camera_x, camera_y, tile_size)
                                except Exception as e:
                                    print(f"Indicator draw error: {e}")
                                    
                            safe_draw_indicator(building, x, y, camera_x, camera_y, self.tile_size)
                        except Exception as e:
                            print(f"Error with building indicator for building {building_index}: {e}")
                except Exception as e:
                    print(f"Error rendering building {building_index}: {e}")
            
            # Second pass: draw highlighted buildings if a villager is selected
            if selected_villager:
                try:
                    # Draw highlighted buildings
                    for highlight_id in [home_id, workplace_id]:
                        if highlight_id is not None and 0 <= highlight_id < len(village_data['buildings']):
                            building = village_data['buildings'][highlight_id]
                            x, y = building['position']
                            building_size = self.tile_size * 3 if building['size'] == 'large' else (
                                        self.tile_size * 2 if building['size'] == 'medium' else self.tile_size)
                            
                            # Check if building is in visible area
                            if ((visible_left - 3) * self.tile_size <= x <= visible_right * self.tile_size and
                                (visible_top - 3) * self.tile_size <= y <= visible_bottom * self.tile_size):
                                
                                # Create highlight effect
                                highlight_color = (0, 255, 0, 100) if highlight_id == home_id else (255, 0, 0, 100)
                                highlight_surface = pygame.Surface((building_size, building_size), pygame.SRCALPHA)
                                highlight_surface.fill(highlight_color)
                                
                                # Render the building texture safely
                                try:
                                    self._find_and_render_building_texture(building, x, y, camera_x, camera_y)
                                except Exception as e:
                                    print(f"Error rendering highlight building texture: {e}")
                                
                                # Draw highlight over building safely
                                try:
                                    if self.screen:
                                        self.screen.blit(highlight_surface, (x - camera_x, y - camera_y))
                                except Exception as e:
                                    print(f"Error drawing highlight: {e}")
                                
                                # Draw glow effect around building safely
                                try:
                                    if self.screen:
                                        glow_size = 4
                                        glow_color = (0, 255, 0) if highlight_id == home_id else (255, 100, 0)
                                        pygame.draw.rect(self.screen, glow_color, 
                                                    (x - camera_x - glow_size, y - camera_y - glow_size, 
                                                        building_size + glow_size * 2, building_size + glow_size * 2), 
                                                    glow_size)
                                except Exception as e:
                                    print(f"Error drawing glow: {e}")
                                
                                # Draw building type indicator safely
                                try:
                                    ui_manager.draw_building_type_indicator(
                                        building, x, y, camera_x, camera_y, self.tile_size)
                                except Exception as e:
                                    print(f"Error drawing indicator for highlight: {e}")
                                
                                # Add "Home" or "Workplace" label safely
                                try:
                                    label = "Home" if highlight_id == home_id else "Workplace"
                                    label_color = (0, 255, 0) if highlight_id == home_id else (255, 100, 0)
                                    font = pygame.font.SysFont(None, 24)
                                    label_text = font.render(label, True, label_color)
                                    
                                    # Position label above building
                                    label_x = x - camera_x + building_size // 2 - label_text.get_width() // 2
                                    label_y = y - camera_y - 25
                                    
                                    # Draw background for label
                                    bg_rect = pygame.Rect(
                                        label_x - 5, label_y - 2, 
                                        label_text.get_width() + 10, label_text.get_height() + 4)
                                    bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                                    bg_surface.fill((0, 0, 0, 150))
                                    
                                    if self.screen:
                                        self.screen.blit(bg_surface, bg_rect)
                                        self.screen.blit(label_text, (label_x, label_y))
                                except Exception as e:
                                    print(f"Error drawing label: {e}")
                except Exception as e:
                    print(f"Error in highlight rendering: {e}")
        except Exception as e:
            print(f"Error in _render_buildings: {e}")
            import traceback
            traceback.print_exc()

    def _find_and_render_building_texture(self, building, x, y, camera_x, camera_y):
        """Helper method to find and render the appropriate building texture.
        
        Args:
            building: The building to render
            x, y: Building position
            camera_x, camera_y: Camera position
            
        Returns:
            Boolean indicating if a texture was found and rendered
        """
        # Get building properties
        building_type = building.get('type', '')
        building_size_str = building.get('size', 'small')
        building_type_str = building.get('building_type', '').lower() if 'building_type' in building else ''
        
        # Try multiple possible key formats for backward compatibility
        found = False
        possible_keys = [
            building_type,  # Original format from 'type' field
            f"{building_size_str}_{building_type_str}_1",  # New format with building_type
            f"{building_size_str}_1"  # Simple format with just size
        ]
        
        for key in possible_keys:
            if key in self.assets['buildings']:
                try:
                    self.screen.blit(self.assets['buildings'][key], (x - camera_x, y - camera_y))
                    found = True
                    break
                except Exception as e:
                    print(f"Error rendering building with key {key}: {e}")
        
        # Use fallback if no matching building texture found
        if not found:
            # Get building size in pixels
            building_size = self.tile_size * 3 if building_size_str == 'large' else (
                        self.tile_size * 2 if building_size_str == 'medium' else self.tile_size)
            
            pygame.draw.rect(self.screen, (200, 200, 200), 
                        (x - camera_x, y - camera_y, 
                            building_size, building_size))
        
        return found


    def _render_bridges(self, village_data, visible_left, visible_right, visible_top, visible_bottom, camera_x, camera_y):
        """Render bridges that go over water."""
        if 'bridges' not in village_data:
            return
            
        for bridge in village_data['bridges']:
            x, y = bridge['position']
            if (visible_left * self.tile_size <= x <= visible_right * self.tile_size and
                visible_top * self.tile_size <= y <= visible_bottom * self.tile_size):
                try:
                    bridge_type = bridge['type']
                    bridge_img = self.assets['environment'][bridge_type]
                    self.screen.blit(bridge_img, (x - camera_x, y - camera_y))
                except (KeyError, AttributeError):
                    # Fallback if bridge texture is missing
                    pygame.draw.rect(self.screen, (150, 100, 50), 
                                (x - camera_x, y - camera_y, 
                                    self.tile_size, self.tile_size))

    def _render_trees(self, village_data, visible_left, visible_right, visible_top, visible_bottom, camera_x, camera_y):
        """Render trees."""
        for tree in village_data['trees']:
            x, y = tree['position']
            if (visible_left * self.tile_size <= x <= visible_right * self.tile_size and
                visible_top * self.tile_size <= y <= visible_bottom * self.tile_size):
                try:
                    tree_img = self.assets['environment'][f"tree_{tree['variant']}"]
                    self.screen.blit(tree_img, (x - camera_x, y - camera_y))
                except KeyError:
                    # Fallback if tree texture is missing
                    pygame.draw.circle(self.screen, (0, 100, 0), 
                                      (x - camera_x + self.tile_size//2, 
                                       y - camera_y + self.tile_size//2), 
                                      self.tile_size//2)
    
    def _render_villagers(self, villagers, camera_x, camera_y):
        """Render villagers and their selection indicators."""
        for villager in villagers:
            # Draw if in visible area
            if (camera_x - self.tile_size <= villager.rect.x <= camera_x + self.screen_width and
                camera_y - self.tile_size <= villager.rect.y <= camera_y + self.screen_height):
                self.screen.blit(villager.image, 
                               (villager.rect.x - camera_x, 
                                villager.rect.y - camera_y))
                
                # Draw selection indicator if selected
                if villager.is_selected:
                    villager.draw_selection_indicator(self.screen, camera_x, camera_y)
                if hasattr(villager, 'is_sleeping') and villager.is_sleeping and hasattr(villager, 'draw_sleep_indicator'):
                    villager.draw_sleep_indicator(self.screen, camera_x, camera_y)
