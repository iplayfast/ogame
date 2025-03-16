import pygame
import math
import Interface

class HousingUI:
    """Handles UI elements related to villager housing and jobs."""
    
    def __init__(self, screen, assets, screen_width, screen_height):
        """Initialize the housing UI manager.
        
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
        self.font = pygame.font.SysFont(None, 22)
        self.small_font = pygame.font.SysFont(None, 18)
        self.title_font = pygame.font.SysFont(None, 24)
        
        # Define colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.PANEL_BG = (40, 40, 40, 200)
        self.PANEL_BORDER = (150, 150, 150)
        self.TEXT_COLOR = (230, 230, 230)
        self.TITLE_COLOR = (255, 255, 180)
        
        # UI state
        self.show_housing_panel = False
        self.selected_building = None
    
    def toggle_housing_panel(self):
        """Toggle visibility of the housing panel."""
        self.show_housing_panel = not self.show_housing_panel
        
    def set_selected_building(self, building):
        """Set the currently selected building."""
        self.selected_building = building
    
    def draw_building_name(self, building, camera_x, camera_y):
        """Draw the name of a building over it.
        
        Args:
            building: Building data dictionary
            camera_x: Camera X position
            camera_y: Camera Y position
        """
        if 'name' not in building:
            return
            
        x, y = building['position']
        # Get building size
        size = 32 * 3 if building['size'] == 'large' else (
               32 * 2 if building['size'] == 'medium' else 32)
        
        # Calculate screen position
        screen_x = x - camera_x + size // 2
        screen_y = y - camera_y - 20  # Position name above building
        
        # Render name text
        name_text = self.small_font.render(building['name'], True, self.WHITE)
        
        # Create a semi-transparent background
        bg_width = name_text.get_width() + 10
        bg_height = name_text.get_height() + 6
        bg_rect = pygame.Rect(
            screen_x - bg_width // 2,
            screen_y - bg_height // 2,
            bg_width,
            bg_height
        )
        
        # Create background surface with alpha
        bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 150))
        
        # Draw background and text
        self.screen.blit(bg_surface, bg_rect)
        self.screen.blit(name_text, (screen_x - name_text.get_width() // 2, screen_y - name_text.get_height() // 2))
    
    def draw_enhanced_building_info(self, building, villagers, camera_x, camera_y):
        """Draw detailed information about a building when clicked.
        
        Args:
            building: Building data dictionary
            villagers: List of villager objects
            camera_x: Camera X position
            camera_y: Camera Y position
        """
        if not building:
            return
            
        # Find residents of this building
        residents = []
        workers = []
        
        for villager in villagers:
            # Check if this is villager's home
            if hasattr(villager, 'home') and villager.home:
                if 'id' in villager.home and building.get('id') == villager.home['id']:
                    residents.append(villager)
            
            # Check if this is villager's workplace
            if hasattr(villager, 'workplace') and villager.workplace:
                if 'id' in villager.workplace and building.get('id') == villager.workplace['id']:
                    workers.append(villager)
        
        # Get building information
        building_type = building.get('building_type', 'Building')
        building_name = building.get('name', building_type)
        
        # Create panel dimensions
        panel_width = 300
        panel_height = 200 + (len(residents) + len(workers)) * 20
        
        # Position panel near mouse but keep on screen
        mouse_pos = pygame.mouse.get_pos()
        panel_x = min(mouse_pos[0] + 20, self.screen_width - panel_width - 10)
        panel_y = min(mouse_pos[1] - panel_height // 2, self.screen_height - panel_height - 10)
        panel_y = max(panel_y, 10)  # Keep panel from going off top of screen
        
        # Create semi-transparent surface for panel
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill(self.PANEL_BG)
        
        # Draw panel and border
        self.screen.blit(panel_surface, (panel_x, panel_y))
        pygame.draw.rect(self.screen, self.PANEL_BORDER, 
                      (panel_x, panel_y, panel_width, panel_height), 2)
        
        # Draw building title
        title_text = self.title_font.render(building_name, True, self.TITLE_COLOR)
        self.screen.blit(title_text, (panel_x + 10, panel_y + 10))
        
        # Draw building type
        type_text = self.font.render(f"Type: {building_type}", True, self.TEXT_COLOR)
        self.screen.blit(type_text, (panel_x + 10, panel_y + 40))
        
        # Draw position
        pos_text = self.font.render(f"Position: {building['position']}", True, self.TEXT_COLOR)
        self.screen.blit(pos_text, (panel_x + 10, panel_y + 65))
        
        # Draw residents section if applicable
        y_offset = panel_y + 95
        if residents:
            residents_title = self.font.render("Residents:", True, self.TITLE_COLOR)
            self.screen.blit(residents_title, (panel_x + 10, y_offset))
            y_offset += 25
            
            for villager in residents:
                resident_text = self.small_font.render(
                    f"• {villager.name} ({villager.job})", True, self.TEXT_COLOR)
                self.screen.blit(resident_text, (panel_x + 20, y_offset))
                y_offset += 20
            
            y_offset += 10
        
        # Draw workers section if applicable
        if workers and building_type != 'House' and building_type != 'Cottage' and building_type != 'Manor':
            workers_title = self.font.render("Workers:", True, self.TITLE_COLOR)
            self.screen.blit(workers_title, (panel_x + 10, y_offset))
            y_offset += 25
            
            for villager in workers:
                worker_text = self.small_font.render(
                    f"• {villager.name} ({villager.job})", True, self.TEXT_COLOR)
                self.screen.blit(worker_text, (panel_x + 20, y_offset))
                y_offset += 20
    
    def draw_villager_housing_info(self, villager, camera_x, camera_y):
        """Add housing and workplace info to the villager panel.
        
        Args:
            villager: Selected villager object
            camera_x: Camera X position
            camera_y: Camera Y position
        """
        if not villager or not hasattr(villager, 'home'):
            return
        
        # Get info panel position (on right side)
        panel_width = 300
        panel_x = self.screen_width - panel_width - 10
        panel_y = 200  # Start below basic info panel
        
        # Calculate home and workplace positions relative to camera
        home_pos = None
        if hasattr(villager, 'home') and villager.home and 'position' in villager.home:
            home_pos = (
                villager.home['position'][0] - camera_x,
                villager.home['position'][1] - camera_y
            )
        
        workplace_pos = None
        if hasattr(villager, 'workplace') and villager.workplace and 'position' in villager.workplace:
            workplace_pos = (
                villager.workplace['position'][0] - camera_x,
                villager.workplace['position'][1] - camera_y
            )
        
        # Draw info panel background
        pygame.draw.rect(self.screen, (50, 50, 50), 
                       (panel_x, panel_y, panel_width, 150))
        pygame.draw.rect(self.screen, (200, 200, 200), 
                       (panel_x, panel_y, panel_width, 150), 2)
        
        # Draw title
        title_text = self.title_font.render("Housing & Work Info", True, self.WHITE)
        self.screen.blit(title_text, (panel_x + 10, panel_y + 10))
        
        # Draw home info
        y_offset = panel_y + 40
        if hasattr(villager, 'home') and villager.home:
            home_name = villager.home.get('name', 'Unknown house')
            home_text = self.font.render(f"Home: {home_name}", True, self.WHITE)
            self.screen.blit(home_text, (panel_x + 10, y_offset))
            
            # Draw roommates if any
            roommates = villager.home.get('roommates', [])
            if len(roommates) > 1:  # More than just this villager
                y_offset += 25
                roommate_text = self.small_font.render(
                    f"Roommates: {', '.join(name for name in roommates if name != villager.name)}", 
                    True, self.WHITE)
                self.screen.blit(roommate_text, (panel_x + 10, y_offset))
        else:
            home_text = self.font.render("Home: Homeless", True, self.WHITE)
            self.screen.blit(home_text, (panel_x + 10, y_offset))
        
        # Draw workplace info
        y_offset += 25
        if hasattr(villager, 'workplace') and villager.workplace:
            workplace_type = villager.workplace.get('type', 'Unknown')
            workplace_text = self.font.render(f"Workplace: {workplace_type}", True, self.WHITE)
            self.screen.blit(workplace_text, (panel_x + 10, y_offset))
        else:
            # Different text based on job
            if villager.job in ["Hunter", "Miner"]:
                workplace_text = self.font.render(f"Workplace: Outside village", True, self.WHITE)
            else:
                workplace_text = self.font.render(f"Workplace: Not assigned", True, self.WHITE)
            self.screen.blit(workplace_text, (panel_x + 10, y_offset))
        
        # Draw mini-map showing home and workplace
        if home_pos or workplace_pos:
            y_offset += 35
            map_size = 100
            map_x = panel_x + panel_width - map_size - 10
            map_y = y_offset
            
            # Draw mini-map background
            pygame.draw.rect(self.screen, (20, 20, 20), 
                           (map_x, map_y, map_size, map_size))
            pygame.draw.rect(self.screen, (100, 100, 100), 
                           (map_x, map_y, map_size, map_size), 1)
            
            # Draw markers for home and workplace
            if home_pos:
                # Check if home is within view
                if (0 <= home_pos[0] <= self.screen_width and 
                    0 <= home_pos[1] <= self.screen_height):
                    # Draw home position (scaled to mini-map)
                    home_map_x = map_x + int(home_pos[0] * map_size / self.screen_width)
                    home_map_y = map_y + int(home_pos[1] * map_size / self.screen_height)
                    pygame.draw.circle(self.screen, (0, 200, 0), 
                                     (home_map_x, home_map_y), 5)
                    pygame.draw.circle(self.screen, (255, 255, 255), 
                                     (home_map_x, home_map_y), 5, 1)
            
            if workplace_pos:
                # Check if workplace is within view
                if (0 <= workplace_pos[0] <= self.screen_width and 
                    0 <= workplace_pos[1] <= self.screen_height):
                    # Draw workplace position (scaled to mini-map)
                    work_map_x = map_x + int(workplace_pos[0] * map_size / self.screen_width)
                    work_map_y = map_y + int(workplace_pos[1] * map_size / self.screen_height)
                    pygame.draw.circle(self.screen, (200, 0, 0), 
                                     (work_map_x, work_map_y), 5)
                    pygame.draw.circle(self.screen, (255, 255, 255), 
                                     (work_map_x, work_map_y), 5, 1)
            
            # Draw villager position
            villager_x = villager.rect.centerx - camera_x
            villager_y = villager.rect.centery - camera_y
            if (0 <= villager_x <= self.screen_width and 
                0 <= villager_y <= self.screen_height):
                v_map_x = map_x + int(villager_x * map_size / self.screen_width)
                v_map_y = map_y + int(villager_y * map_size / self.screen_height)
                pygame.draw.circle(self.screen, (0, 200, 200), 
                                 (v_map_x, v_map_y), 3)
    
    def draw_daily_activities(self, villager):
        """Draw the daily activities for a villager.
        
        Args:
            villager: Selected villager object
        """
        if not villager or not hasattr(villager, 'daily_activities'):
            return
        
        # Get panel position (on right side)
        panel_width = 300
        panel_x = self.screen_width - panel_width - 10
        panel_y = 360  # Start below housing info panel
        
        # Calculate panel height based on number of activities
        activities = villager.daily_activities
        panel_height = 45 + len(activities) * 20
        
        # Draw info panel background
        pygame.draw.rect(self.screen, (50, 50, 50), 
                       (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(self.screen, (200, 200, 200), 
                       (panel_x, panel_y, panel_width, panel_height), 2)
        
        # Draw title
        title_text = self.title_font.render("Daily Activities", True, self.WHITE)
        self.screen.blit(title_text, (panel_x + 10, panel_y + 10))
        
        # Draw list of activities
        y_offset = panel_y + 40
        for i, activity in enumerate(activities):
            activity_text = self.small_font.render(f"{i+1}. {activity}", True, self.WHITE)
            self.screen.blit(activity_text, (panel_x + 20, y_offset))
            y_offset += 20
    # This code should be added to housing_ui.py

    def set_selected_building(self, building):
        """Set the currently selected building with Interface notification."""
        # Store previous selection
        old_selection = self.selected_building
        
        # Normal update
        self.selected_building = building
        
        # Notify if selection changed
        if building is not None and building != old_selection:
            Interface.on_building_selected(building)
            print(f"Building selected: {building.get('building_type', 'unknown')}")

    # This code goes in assign_housing_and_jobs function within villager_housing.py to notify of assignments

    def notify_housing_assignments(villagers, assignments):
        """Notify Interface of housing and workplace assignments."""
        if not assignments or 'villagers' not in assignments:
            return
            
        for villager in villagers:
            for v_data in assignments['villagers']:
                if villager.name == v_data['name']:
                    # Find the home building
                    if 'home' in v_data and 'id' in v_data['home'] and v_data['home']['id'] >= 0:
                        home_id = v_data['home']['id']
                        # Notify Interface
                        Interface.on_building_housing_assigned(villager, {'id': home_id}, 'home')
                    
                    # Find the workplace building
                    if 'workplace' in v_data and 'id' in v_data['workplace']:
                        workplace_id = v_data['workplace']['id']
                        # Notify Interface
                        Interface.on_building_housing_assigned(villager, {'id': workplace_id}, 'workplace')
                        
        print("Interface notified of all housing and workplace assignments")

    # Call this at the end of assign_housing_and_jobs