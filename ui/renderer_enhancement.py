import pygame

def enhance_renderer_for_interiors(renderer_class):
    """Enhance the renderer class to support building interiors.
    
    This function modifies the given renderer class by adding methods to
    handle building interiors.
    
    Args:
        renderer_class: The Renderer class to enhance
    """
    original_init = renderer_class.__init__
    original_render_buildings = renderer_class._render_buildings
    
    def enhanced_init(self, screen, assets, screen_width, screen_height, tile_size):
        # Call original init
        original_init(self, screen, assets, screen_width, screen_height, tile_size)
        
        # Add interior manager
        from building_interiors import BuildingInteriors
        self.interior_manager = BuildingInteriors(tile_size)
    
    def enhanced_render_buildings(self, village_data, visible_left, visible_right, 
                                 visible_top, visible_bottom, camera_x, camera_y, 
                                 ui_manager, selected_villager=None):
        # Always render interiors first
        if hasattr(self, 'interior_manager'):
            self.interior_manager.render_interiors(
                self.screen, village_data['buildings'], camera_x, camera_y)
            
        # Call original render_buildings method to draw building exteriors on top
        original_render_buildings(self, village_data, visible_left, visible_right,
                                 visible_top, visible_bottom, camera_x, camera_y,
                                 ui_manager, selected_villager)
    
    def initialize_interiors(self, village_data):
        """Initialize building interiors.
        
        Args:
            village_data: Village data dictionary
        """
        if hasattr(self, 'interior_manager'):
            self.interior_manager.generate_interiors(village_data['buildings'])
    
    # Update the Renderer class with the enhanced methods
    renderer_class.__init__ = enhanced_init
    renderer_class._render_buildings = enhanced_render_buildings
    renderer_class.initialize_interiors = initialize_interiors
    
    return renderer_class
