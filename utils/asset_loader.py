import pygame
import os
import math

def load_assets():
    """Load all game assets.
    
    Returns:
        Dictionary containing all game assets
    """
    assets = {
        'characters': {},
        'buildings': {'roofs': {}},
        'environment': {},
        'ui': {}
    }
    
    print("Loading assets...")
    
    # Load character sprites
    for i in range(1, 6):  # 5 variations
        try:
            path = f'assets/characters/villager_{i}.png'
            if os.path.exists(path):
                assets['characters'][f'villager_{i}'] = pygame.image.load(path).convert_alpha()
                print(f"Loaded {path}")
        except pygame.error as e:
            print(f"Warning: Could not load villager_{i}.png - {e}")
    
    # Load buildings and roofs - MODIFIED to match the naming convention in topdown-asset-generator.py
    building_types = ["house", "tavern", "shop", "blacksmith", "bakery"]
    
    for size in ['small', 'medium', 'large']:
        for building_type in building_types:
            for i in range(1, 5):  # 4 variations per type
                building_path = f'assets/buildings/building_{size}_{building_type}_{i}.png'
                if os.path.exists(building_path):
                    # Use a consistent key format that works with both old and new conventions
                    # We'll use a format that matches how buildings are stored in village_data
                    key = f"{size}_{building_type}_{i}"
                    assets['buildings'][key] = pygame.image.load(building_path).convert_alpha()
                    print(f"Loaded {building_path} as {key}")
                
                # Also check for the old naming convention for backward compatibility
                old_building_path = f'assets/buildings/building_{size}_{i}.png'
                if os.path.exists(old_building_path):
                    key = f"{size}_{i}"
                    assets['buildings'][key] = pygame.image.load(old_building_path).convert_alpha()
                    print(f"Loaded {old_building_path} as {key}")
                
                # Check for roof assets
                roof_path = f'assets/buildings/roofs/roof_{size}_{i}.png'
                if os.path.exists(roof_path):
                    assets['buildings']['roofs'][f'{size}_{i}'] = pygame.image.load(roof_path).convert_alpha()
                    print(f"Loaded {roof_path}")
    
    # Debug: Print all building keys that were loaded
    print(f"Loaded {len(assets['buildings'])} building assets (excluding roofs):")
    for key in assets['buildings'].keys():
        if key != 'roofs':
            print(f"  - {key}")
    
    # Load environment assets
    for i in range(1, 6):  # 5 tree variations
        try:
            tree_path = f'assets/environment/tree_{i}.png'
            if os.path.exists(tree_path):
                assets['environment'][f'tree_{i}'] = pygame.image.load(tree_path).convert_alpha()
                print(f"Loaded {tree_path}")
        except pygame.error as e:
            print(f"Warning: Could not load tree_{i}.png - {e}")
    
    for i in range(1, 4):  # 3 grass variations
        try:
            grass_path = f'assets/environment/grass_{i}.png'
            if os.path.exists(grass_path):
                assets['environment'][f'grass_{i}'] = pygame.image.load(grass_path).convert_alpha()
                print(f"Loaded {grass_path}")
        except pygame.error as e:
            print(f"Warning: Could not load grass_{i}.png - {e}")
    
    for i in range(1, 3):  # 2 path variations
        try:
            path_path = f'assets/environment/path_{i}.png'
            if os.path.exists(path_path):
                assets['environment'][f'path_{i}'] = pygame.image.load(path_path).convert_alpha()
                print(f"Loaded {path_path}")
        except pygame.error as e:
            print(f"Warning: Could not load path_{i}.png - {e}")
       # Load bridge sprites
    try:
        bridge_path = 'assets/environment/LeftRightBridge.png'
        if os.path.exists(bridge_path):
            assets['environment']['LeftRightBridge'] = pygame.image.load(bridge_path).convert_alpha()
            print(f"Loaded {bridge_path}")
    except pygame.error as e:
        print(f"Warning: Could not load LeftRightBridge.png - {e}")
        
    try:
        bridge_path = 'assets/environment/UpDownBridge.png'
        if os.path.exists(bridge_path):
            assets['environment']['UpDownBridge'] = pygame.image.load(bridge_path).convert_alpha()
            print(f"Loaded {bridge_path}")
    except pygame.error as e:
        print(f"Warning: Could not load UpDownBridge.png - {e}")
    # Load water animation frames
    assets['environment']['water'] = []
    for i in range(1, 5):  # 4 animation frames
        try:
            water_path = f'assets/environment/water_frame_{i}.png'
            if os.path.exists(water_path):
                assets['environment']['water'].append(pygame.image.load(water_path).convert_alpha())
                print(f"Loaded {water_path}")
        except pygame.error as e:
            print(f"Warning: Could not load water_frame_{i}.png - {e}")
    
    # Load UI elements
    for icon in ['health', 'energy', 'mood', 'money']:
        try:
            icon_path = f'assets/ui/icon_{icon}.png'
            if os.path.exists(icon_path):
                assets['ui'][f'icon_{icon}'] = pygame.image.load(icon_path).convert_alpha()
                print(f"Loaded {icon_path}")
        except pygame.error as e:
            print(f"Warning: Could not load icon_{icon}.png - {e}")
    
    try:
        dialog_path = 'assets/ui/dialog_template.png'
        if os.path.exists(dialog_path):
            assets['ui']['dialog'] = pygame.image.load(dialog_path).convert_alpha()
            print(f"Loaded {dialog_path}")
    except pygame.error as e:
        print(f"Warning: Could not load dialog_template.png - {e}")
    
    # Create simulated conversation sounds
    assets['sounds'] = {}
    assets['sounds']['conversations'] = []
    
    # Create simple beep sounds with different pitches for conversations
    for i in range(5):
        try:
            # Try to load a sound file if it exists
            sound_path = f'assets/sounds/conversation_{i+1}.wav'
            if os.path.exists(sound_path):
                sound = pygame.mixer.Sound(sound_path)
                print(f"Loaded {sound_path}")
            else:
                # Otherwise create a simple beep sound programmatically
                duration = 1.0  # seconds
                frequency = 440 + i * 100  # Hz (A4 + offset)
                sample_rate = 44100  # samples per second
                buffer = generate_sine_wave(frequency, duration, sample_rate)
                sound = pygame.mixer.Sound(buffer=buffer)
                sound.set_volume(0.3)  # Lower volume
                print(f"Generated sound for conversation {i+1}")
            
            assets['sounds']['conversations'].append(sound)
        except Exception as e:
            print(f"Warning: Could not create sound for conversation {i+1} - {e}")
            # Add a dummy sound to prevent index errors
            dummy_buffer = bytearray(1000)
            assets['sounds']['conversations'].append(pygame.mixer.Sound(buffer=dummy_buffer))
    
    print("Asset loading complete!")
    return assets

def generate_sine_wave(frequency, duration, sample_rate=44100):
    """Generate a simple sine wave sound for testing.
    
    Args:
        frequency: Frequency of the sound in Hz
        duration: Duration of the sound in seconds
        sample_rate: Sample rate in samples per second
        
    Returns:
        bytearray containing the sound data
    """
    num_samples = int(duration * sample_rate)
    buf = bytearray(num_samples)
    
    for i in range(num_samples):
        t = i / sample_rate
        buf[i] = int(127 + 127 * math.sin(frequency * t * 2 * math.pi))
    
    return buf
