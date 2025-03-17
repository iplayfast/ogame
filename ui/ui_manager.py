import pygame

class UIManager:
    def __init__(self, screen, assets, screen_width, screen_height):
        """Initialize the UI manager.
        
        Args:
            screen: Pygame screen object
            assets: Dictionary of game assets
            screen_width: Width of the game screen
            screen_height: Height of the game screen
        """
        self.screen = screen
        self.assets = assets
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Set up fonts
        self.font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 18)
        self.name_font = pygame.font.SysFont(None, 28)
        
        # Define colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GREEN = (100, 200, 100)
        self.BLUE = (100, 100, 200)
    
    def draw_selected_villager_info(self, villager, tile_size):
        """Draw information panel for the selected villager.
        
        Args:
            villager: Selected villager object
            tile_size: Size of a tile in pixels
        """
        if not villager:
            return
            
        # Draw info panel background - on right side
        panel_width = 300
        panel_height = 200
        panel_x = self.screen_width - panel_width - 10
        panel_y = 10
        
        pygame.draw.rect(self.screen, (50, 50, 50), 
                       (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(self.screen, (200, 200, 200), 
                       (panel_x, panel_y, panel_width, panel_height), 2)
        
        # Draw villager info
        status = villager.get_status()
        y_offset = panel_y + 10
        
        # Name and job with slightly larger font
        name_text = self.name_font.render(f"{status['Name']}", True, self.WHITE)
        self.screen.blit(name_text, (panel_x + 10, y_offset))
        y_offset += 25
        
        job_text = self.font.render(f"Job: {status['Job']}", True, self.WHITE)
        self.screen.blit(job_text, (panel_x + 10, y_offset))
        y_offset += 25
        
        # Stats with icons
        for stat, icon_name in [
            ("Health", "icon_health"), 
            ("Energy", "icon_energy"),
            ("Mood", "icon_mood"),
            ("Money", "icon_money")
        ]:
            # Try to draw icon
            try:
                icon = self.assets['ui'][icon_name]
                self.screen.blit(icon, (panel_x + 10, y_offset))
                stat_text = self.font.render(f"{stat}: {status[stat]}", True, self.WHITE)
                self.screen.blit(stat_text, (panel_x + 35, y_offset))
            except KeyError:
                # Fallback if icon is missing
                stat_text = self.font.render(f"{stat}: {status[stat]}", True, self.WHITE)
                self.screen.blit(stat_text, (panel_x + 10, y_offset))
            y_offset += 22
        
        # Activity
        activity_text = self.font.render(f"Activity: {status['Activity']}", True, self.WHITE)
        self.screen.blit(activity_text, (panel_x + 10, y_offset))
    
    def draw_minimap(self, village_data, villagers, camera_x, camera_y, tile_size, position='bottom_right'):
        """Draw a minimap of the village.
        
        Args:
            village_data: Village data dictionary
            villagers: List of villager objects
            camera_x: Camera X position
            camera_y: Camera Y position
            tile_size: Size of a tile in pixels
            position: Position of the minimap ('bottom_right', 'upper_right', etc.)
        """
        minimap_size = 150
        
        # Determine position based on parameter
        if position == 'bottom_right':
            minimap_x = self.screen_width - minimap_size - 10
            minimap_y = self.screen_height - minimap_size - 10
        elif position == 'upper_right':
            minimap_x = self.screen_width - minimap_size - 10
            minimap_y = 10
        elif position == 'upper_left':
            minimap_x = 10
            minimap_y = 10
        else:  # Default to bottom right
            minimap_x = self.screen_width - minimap_size - 10
            minimap_y = self.screen_height - minimap_size - 10
        
        # Draw minimap background
        pygame.draw.rect(self.screen, (20, 20, 20), 
                        (minimap_x, minimap_y, minimap_size, minimap_size))
        pygame.draw.rect(self.screen, (100, 100, 100), 
                        (minimap_x, minimap_y, minimap_size, minimap_size), 1)
        
        # Scale factor for minimap
        scale = minimap_size / village_data['size']
        
        # Draw buildings on minimap
        for building in village_data['buildings']:
            x, y = building['position']
            building_size = max(3, int(tile_size * scale))  # Ensure buildings are visible
            building_color = (200, 200, 100)  # Default color
            
            # Different colors based on building type
            building_type = building.get('building_type', '')
            if 'Store' in building_type or 'Market' in building_type:
                building_color = (100, 200, 100)  # Green for shops
            elif 'Inn' in building_type or 'Tavern' in building_type:
                building_color = (200, 100, 100)  # Red for inns
            
            pygame.draw.rect(self.screen, building_color, 
                           (minimap_x + int(x * scale), 
                            minimap_y + int(y * scale), 
                            building_size, building_size))
        
        # Draw paths on minimap
        for path in village_data['paths']:
            x, y = path['position']
            pygame.draw.rect(self.screen, (180, 160, 120), 
                           (minimap_x + int(x * scale), 
                            minimap_y + int(y * scale), 
                            max(1, int(tile_size * scale)), 
                            max(1, int(tile_size * scale))))
        
        # Draw water on minimap
        for water_tile in village_data['water']:
            x, y = water_tile['position']
            pygame.draw.rect(self.screen, (80, 130, 200), 
                           (minimap_x + int(x * scale), 
                            minimap_y + int(y * scale), 
                            max(1, int(tile_size * scale)), 
                            max(1, int(tile_size * scale))))
        
        # Draw villagers on minimap
        for villager in villagers:
            x, y = villager.position.x, villager.position.y
            # Highlight selected villager
            color = (0, 255, 255) if villager.is_selected else (255, 255, 255)
            pygame.draw.circle(self.screen, color, 
                             (minimap_x + int(x * scale), 
                              minimap_y + int(y * scale)), 
                             2)
        
        # Draw camera view rectangle on minimap
        pygame.draw.rect(self.screen, (255, 255, 255), 
                        (minimap_x + int(camera_x * scale), 
                         minimap_y + int(camera_y * scale),
                         int(self.screen_width * scale),
                         int(self.screen_height * scale)), 
                        1)
    
    def draw_debug_info(self, clock, villagers, camera_x, camera_y, village_size):
        """Draw debug information in the top left corner.
        
        Args:
            clock: Pygame clock object for FPS calculation
            villagers: List of villager objects
            camera_x: Camera X position
            camera_y: Camera Y position
            village_size: Size of the village in pixels
        """
        fps = clock.get_fps()
        fps_text = self.small_font.render(f"FPS: {fps:.1f}", True, self.WHITE)
        self.screen.blit(fps_text, (10, 10))
        
        villager_count = len(villagers)
        count_text = self.small_font.render(f"Villagers: {villager_count}", True, self.WHITE)
        self.screen.blit(count_text, (10, 30))
        
        pos_text = self.small_font.render(
            f"Camera: ({camera_x}, {camera_y})", True, self.WHITE)
        self.screen.blit(pos_text, (10, 50))
        
        # Add controls help
        help_text = self.small_font.render(
            "Controls: WASD/Arrows to move camera, P to pause, D for debug info", True, self.WHITE)
        self.screen.blit(help_text, (10, 70))
        
        village_size_text = self.small_font.render(
            f"Village size: {village_size}x{village_size} pixels", True, self.WHITE)
        self.screen.blit(village_size_text, (10, 90))

    def draw_building_type_indicator(self, building, x, y, camera_x, camera_y, tile_size):
        """Draw an indicator of the building type on the building.
        
        Args:
            building: Building object
            x: Building X position
            y: Building Y position
            camera_x: Camera X position
            camera_y: Camera Y position
            tile_size: Size of a tile in pixels
        """
        size = tile_size * 3 if building['size'] == 'large' else (
            tile_size * 2 if building['size'] == 'medium' else tile_size)
        
        building_type = building.get('building_type', '')
        
        # Draw simple icon based on building type
        screen_x = x - camera_x + size // 2
        screen_y = y - camera_y + size // 2
        
        # More specific matching for building types to ensure correct icons
        # Use the first letter of the building type as the icon character by default
        icon_char = building_type[0] if building_type else "?"
        
        # Choose color based on building type
        if building_type in ["House", "Cottage", "Manor"]:
            color = (200, 200, 100)  # Yellow for residential
            icon_char = "H"
        elif building_type == "Store" or building_type == "Market":
            color = (100, 200, 100)  # Green for shops
            icon_char = "S"
        elif building_type == "Bakery":
            color = (230, 180, 80)  # Light brown for bakery
            icon_char = "B"
        elif building_type in ["Inn", "Tavern"]:
            color = (200, 100, 100)  # Red for inns/taverns
            icon_char = "I"
        elif building_type == "Workshop":
            color = (150, 150, 150)  # Gray for workshops
            icon_char = "W"
        elif building_type == "Smithy":
            color = (180, 120, 80)  # Bronze for smithy
            icon_char = "F"  # F for Forge
        elif building_type == "Storage":
            color = (130, 110, 70)  # Brown for storage
            icon_char = "S"  # S for Storage
        elif building_type == "Town Hall":
            color = (100, 100, 200)  # Blue for official buildings
            icon_char = "T"
        elif building_type == "Temple":
            color = (230, 230, 150)  # Light gold for temple
            icon_char = "T"
        else:
            color = (150, 150, 150)  # Gray for other buildings
        
        # Draw circular background
        pygame.draw.circle(self.screen, color, (screen_x, screen_y), tile_size // 3)
        pygame.draw.circle(self.screen, (0, 0, 0), (screen_x, screen_y), tile_size // 3, 1)
        
        # Draw text
        text = self.font.render(icon_char, True, (0, 0, 0))
        text_rect = text.get_rect(center=(screen_x, screen_y))
        self.screen.blit(text, text_rect)

    def draw_multiple_villagers_indicator(self, selected_villager, villagers, camera_x, camera_y):
        """Draw an indicator when multiple villagers are in the same location."""
        if not selected_villager:
            return
            
        # Get selected villager position
        center_x = selected_villager.rect.centerx - camera_x
        center_y = selected_villager.rect.centery - camera_y
        
        # Count villagers at this position
        villagers_at_position = 0
        for villager in villagers:
            if abs(villager.position.x - selected_villager.position.x) < 10 and \
            abs(villager.position.y - selected_villager.position.y) < 10:
                villagers_at_position += 1
        
        # Only draw indicator if multiple villagers exist at this position
        if villagers_at_position > 1:
            # Draw indicator text
            indicator_text = self.small_font.render(
                f"[{villagers_at_position} villagers here - click to cycle]", True, (255, 255, 255))
            
            # Draw background for better visibility
            text_bg_rect = pygame.Rect(
                center_x - indicator_text.get_width() // 2 - 5,
                center_y - 40,
                indicator_text.get_width() + 10,
                indicator_text.get_height() + 6
            )
            
            # Semi-transparent background
            bg_surface = pygame.Surface((text_bg_rect.width, text_bg_rect.height), pygame.SRCALPHA)
            bg_surface.fill((0, 0, 0, 160))
            self.screen.blit(bg_surface, text_bg_rect)
            
            # Draw text
            self.screen.blit(indicator_text, (center_x - indicator_text.get_width() // 2, center_y - 37))


    def draw_building_info(self, building, camera_x, camera_y):
        """Draw information about a building when hovered.
        
        Args:
            building: Building being hovered over
            camera_x: Camera X position
            camera_y: Camera Y position
        """
        if not building:
            return
            
        # Get mouse position for tooltip
        mouse_pos = pygame.mouse.get_pos()
        
        # Get building information
        building_type = building.get('building_type', 'Building')
        
        # Create tooltip text
        tooltip_text = f"{building_type}"
        tooltip_render = self.font.render(tooltip_text, True, self.WHITE)
        
        # Position tooltip near mouse but keep on screen
        tooltip_x = mouse_pos[0] + 15
        tooltip_y = mouse_pos[1] - 25
        
        # Ensure tooltip stays on screen
        if tooltip_x + tooltip_render.get_width() > self.screen_width:
            tooltip_x = self.screen_width - tooltip_render.get_width() - 5
        if tooltip_y < 0:
            tooltip_y = 5
        
        # Draw tooltip background
        background_rect = pygame.Rect(
            tooltip_x - 5, 
            tooltip_y - 5, 
            tooltip_render.get_width() + 10, 
            tooltip_render.get_height() + 10
        )
        pygame.draw.rect(self.screen, (40, 40, 40), background_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), background_rect, 1)
        
        # Draw tooltip text
        self.screen.blit(tooltip_render, (tooltip_x, tooltip_y))
