"""
Comprehensive Asset Loader for Village Simulation

This module provides a centralized, robust asset loading system 
that handles all game assets, including characters, tilesets, 
and other game resources.
"""

import os
import pygame
import math

class AssetManager:
    """
    Centralized asset management class to handle loading and caching of all game assets.
    """
    _instance = None  # Singleton instance
    
    def __new__(cls):
        """Implement singleton pattern to ensure only one asset manager exists."""
        if not cls._instance:
            cls._instance = super(AssetManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize asset manager if not already initialized."""
        if self._initialized:
            return
        
        # Initialize pygame
        pygame.init()
        
        # Asset storage dictionaries
        self.characters = {}
        self.character_tilesets = {}
        self.buildings = {}
        self.environment = {}
        self.ui = {}
        self.sounds = {}
        
        # Root directory for assets
        self.root_dir = self._find_assets_root()
        
        # Initialization flag
        self._initialized = True
    
    def _find_assets_root(self):
        """
        Find the root directory for assets by traversing up from the current file.
        
        Returns:
            str: Path to the assets directory
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Traverse up to find the assets directory
        for _ in range(3):  # Limit to prevent infinite loop
            assets_dir = os.path.join(current_dir, 'assets')
            if os.path.exists(assets_dir):
                return assets_dir
            current_dir = os.path.dirname(current_dir)
        
        # Fallback
        print("Warning: Could not find assets directory. Using current directory.")
        return os.path.dirname(os.path.abspath(__file__))
    
    def load_character_assets(self, character_types=None):
        """
        Load character sprites and animations.
        
        Args:
            character_types (list, optional): List of specific character types to load
        """
        # Default character types if not specified
        if character_types is None:
            character_types = [
                "Old_man", "Old_woman", "Man", "Woman", "Boy", "Girl"
            ]
        
        # Character folders mapping
        character_folders = {
            "Old_man": "1 Old_man",
            "Old_woman": "2 Old_woman",
            "Man": "3 Man",
            "Woman": "4 Woman",
            "Boy": "5 Boy",
            "Girl": "6 Girl"
        }
        
        # Path to characters directory
        characters_dir = os.path.join(self.root_dir, 'characters')
        
        for char_type in character_types:
            # Determine folder name
            folder_name = character_folders.get(char_type, char_type)
            folder_path = os.path.join(characters_dir, folder_name)
            
            if not os.path.exists(folder_path):
                print(f"Warning: Character folder not found for {char_type}: {folder_path}")
                continue
            
            # Load character animations
            animations = {}
            animation_types = ['idle', 'walk', 'attack', 'hurt', 'death']
            
            for anim_type in animation_types:
                file_path = os.path.join(folder_path, f"{char_type}_{anim_type}.png")
                if os.path.exists(file_path):
                    try:
                        # Load animation using AnimatedTileset from sprite.py
                        from utils.sprite import AnimatedTileset
                        animations[anim_type] = AnimatedTileset(file_path, 48, 48, 1)
                        print(f"Loaded {char_type} {anim_type} animation")
                    except Exception as e:
                        print(f"Error loading {char_type} {anim_type} animation: {e}")
            
            # Store character tilesets
            self.character_tilesets[char_type] = animations
    
    def load_building_assets(self):
        """Load building sprites and textures."""
        buildings_dir = os.path.join(self.root_dir, 'buildings')
        building_types = ["house", "tavern", "shop", "blacksmith", "bakery"]
        
        for size in ['small', 'medium', 'large']:
            for building_type in building_types:
                for i in range(1, 5):  # 4 variations per type
                    # Try new naming convention
                    building_path = os.path.join(buildings_dir, f"building_{size}_{building_type}_{i}.png")
                    
                    # If new convention doesn't exist, try old convention
                    if not os.path.exists(building_path):
                        building_path = os.path.join(buildings_dir, f"building_{size}_{i}.png")
                    
                    if os.path.exists(building_path):
                        try:
                            # Use convert_alpha() for proper transparency
                            building_img = pygame.image.load(building_path).convert_alpha()
                            key = f"{size}_{building_type}_{i}"
                            self.buildings[key] = building_img
                            print(f"Loaded building: {key}")
                        except Exception as e:
                            print(f"Error loading building {building_path}: {e}")
    
    def load_environment_assets(self):
        """Load environment sprites like trees, grass, paths."""
        env_dir = os.path.join(self.root_dir, 'environment')
        
        # Load trees
        for i in range(1, 6):  # 5 tree variations
            tree_path = os.path.join(env_dir, f"tree_{i}.png")
            if os.path.exists(tree_path):
                try:
                    tree_img = pygame.image.load(tree_path).convert_alpha()
                    self.environment[f"tree_{i}"] = tree_img
                except Exception as e:
                    print(f"Error loading tree {i}: {e}")
        
        # Load grass
        for i in range(1, 4):  # 3 grass variations
            grass_path = os.path.join(env_dir, f"grass_{i}.png")
            if os.path.exists(grass_path):
                try:
                    grass_img = pygame.image.load(grass_path).convert_alpha()
                    self.environment[f"grass_{i}"] = grass_img
                except Exception as e:
                    print(f"Error loading grass {i}: {e}")
        
        # Load paths
        for i in range(1, 3):  # 2 path variations
            path_path = os.path.join(env_dir, f"path_{i}.png")
            if os.path.exists(path_path):
                try:
                    path_img = pygame.image.load(path_path).convert_alpha()
                    self.environment[f"path_{i}"] = path_img
                except Exception as e:
                    print(f"Error loading path {i}: {e}")
        
        # Load water animation frames
        self.environment['water'] = []
        for i in range(1, 5):  # 4 animation frames
            water_path = os.path.join(env_dir, f"water_frame_{i}.png")
            if os.path.exists(water_path):
                try:
                    water_img = pygame.image.load(water_path).convert_alpha()
                    self.environment['water'].append(water_img)
                except Exception as e:
                    print(f"Error loading water frame {i}: {e}")
    
    def load_ui_assets(self):
        """Load UI icons and elements."""
        ui_dir = os.path.join(self.root_dir, 'ui')
        
        # Load icons
        for icon_name in ['health', 'energy', 'mood', 'money']:
            icon_path = os.path.join(ui_dir, f"icon_{icon_name}.png")
            if os.path.exists(icon_path):
                try:
                    icon_img = pygame.image.load(icon_path).convert_alpha()
                    self.ui[f'icon_{icon_name}'] = icon_img
                except Exception as e:
                    print(f"Error loading {icon_name} icon: {e}")
        
        # Load dialog template
        dialog_path = os.path.join(ui_dir, "dialog_template.png")
        if os.path.exists(dialog_path):
            try:
                dialog_img = pygame.image.load(dialog_path).convert_alpha()
                self.ui['dialog'] = dialog_img
            except Exception as e:
                print(f"Error loading dialog template: {e}")
    
    def load_sounds(self):
        """Load conversation sounds."""
        sounds_dir = os.path.join(self.root_dir, 'sounds')
        
        # Create conversation sounds
        self.sounds['conversations'] = []
        
        # Try to load actual sound files first
        for i in range(1, 6):  # 5 conversation sounds
            sound_path = os.path.join(sounds_dir, f"conversation_{i}.wav")
            if os.path.exists(sound_path):
                try:
                    sound = pygame.mixer.Sound(sound_path)
                    sound.set_volume(0.3)
                    self.sounds['conversations'].append(sound)
                    print(f"Loaded conversation sound {i}")
                except Exception as e:
                    print(f"Error loading conversation sound {i}: {e}")
        
        # If no sounds found, generate procedural sounds
        if not self.sounds['conversations']:
            for i in range(5):
                sound = self._generate_tone_sound(
                    frequency=440 + i * 100,  # Slightly different frequencies
                    duration=1.0,
                    sample_rate=44100
                )
                sound.set_volume(0.3)
                self.sounds['conversations'].append(sound)
    
    def _generate_tone_sound(self, frequency, duration, sample_rate=44100):
        """
        Generate a simple sine wave sound for testing.
        
        Args:
            frequency: Frequency of the sound in Hz
            duration: Duration of the sound in seconds
            sample_rate: Sample rate in samples per second
            
        Returns:
            pygame.mixer.Sound with the generated tone
        """
        num_samples = int(duration * sample_rate)
        buf = bytearray(num_samples)
        
        for i in range(num_samples):
            t = i / sample_rate
            buf[i] = int(127 + 127 * math.sin(frequency * t * 2 * math.pi))
        
        return pygame.mixer.Sound(buffer=buf)
    
    def load_all_assets(self, character_types=None):
        """
        Load all game assets in a comprehensive manner.
        
        Args:
            character_types (list, optional): Specific character types to load
        """
        print("Starting comprehensive asset loading...")
        
        # Load different asset categories
        self.load_character_assets(character_types)
        self.load_building_assets()
        self.load_environment_assets()
        self.load_ui_assets()
        self.load_sounds()
        
        print("Asset loading complete!")
        return {
            'characters': self.character_tilesets,
            'buildings': self.buildings,
            'environment': self.environment,
            'ui': self.ui,
            'sounds': self.sounds
        }

def load_assets(character_types=None):
    """
    Convenience function to load all assets.
    
    Args:
        character_types (list, optional): Specific character types to load
        
    Returns:
        dict: Loaded game assets
    """
    asset_manager = AssetManager()
    return asset_manager.load_all_assets(character_types)