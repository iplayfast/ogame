"""
Interaction System - Handles interactions between villagers
"""
import pygame
import math
import random
from ui import Interface

class InteractionSystem:
    """Manages interactions between villagers and with the environment."""
    
    def __init__(self, game_state):
        """Initialize the interaction system.
        
        Args:
            game_state: Reference to the main game state
        """
        self.game_state = game_state
        
        # Interaction settings
        self.INTERACTION_RADIUS = 50
        self.CONVERSATION_CHANCE = 0.01  # 1% chance per update
        
        # Tracking for current interactions
        self.active_conversations = {}  # {(villager1, villager2): start_time}
        self.interaction_cooldowns = {}  # {villager: cooldown_time}
    
    def update(self, current_time):
        """Update villager interactions.
        
        Args:
            current_time: Current time in milliseconds
        """
        # Update active conversations
        self._update_active_conversations(current_time)
        
        # Check for new potential interactions
        self._check_for_new_interactions(current_time)
        
        # Clean up expired cooldowns
        self._clean_cooldowns(current_time)
    
    def _update_active_conversations(self, current_time):
        """Update active conversations and end those that have lasted long enough.
        
        Args:
            current_time: Current time in milliseconds
        """
        # Conversation duration (5-15 seconds)
        MIN_DURATION = 5000
        MAX_DURATION = 15000
        
        # Check all active conversations
        ended_conversations = []
        for (v1, v2), start_time in self.active_conversations.items():
            # Calculate conversation duration
            duration = current_time - start_time
            
            # Generate a random duration if not set
            if not hasattr(v1, 'conversation_duration') or not v1.conversation_duration:
                v1.conversation_duration = random.randint(MIN_DURATION, MAX_DURATION)
            
            # End conversation if it has lasted long enough
            if duration > v1.conversation_duration:
                ended_conversations.append((v1, v2))
                
                # Set cooldown for both villagers
                cooldown = random.randint(10000, 30000)  # 10-30 seconds
                self.interaction_cooldowns[v1] = current_time + cooldown
                self.interaction_cooldowns[v2] = current_time + cooldown
                
                # Reset conversation state
                v1.is_talking = False
                v2.is_talking = False
                v1.conversation_duration = None
                
                # Notify that conversation ended
                Interface.on_villager_interaction(v1, v2, "conversation_end")
        
        # Remove ended conversations
        for v1, v2 in ended_conversations:
            if (v1, v2) in self.active_conversations:
                del self.active_conversations[(v1, v2)]
    
    def _check_for_new_interactions(self, current_time):
        """Check for potential new interactions between villagers.
        
        Args:
            current_time: Current time in milliseconds
        """
        # Find villagers that could interact
        for v1 in self.game_state.villagers:
            # Skip villagers on cooldown
            if v1 in self.interaction_cooldowns:
                continue
                
            # Skip villagers that are sleeping
            if hasattr(v1, 'is_sleeping') and v1.is_sleeping:
                continue
                
            for v2 in self.game_state.villagers:
                # Skip self-interaction
                if v1 == v2:
                    continue
                    
                # Skip if either villager is already in a conversation
                in_conversation = False
                for (a, b) in self.active_conversations.keys():
                    if v1 in (a, b) or v2 in (a, b):
                        in_conversation = True
                        break
                        
                if in_conversation:
                    continue
                
                # Skip villagers on cooldown
                if v2 in self.interaction_cooldowns:
                    continue
                    
                # Skip villagers that are sleeping
                if hasattr(v2, 'is_sleeping') and v2.is_sleeping:
                    continue
                
                # Check if villagers are close enough to interact
                distance = math.sqrt((v1.position.x - v2.position.x)**2 + 
                                    (v1.position.y - v2.position.y)**2)
                
                if distance < self.INTERACTION_RADIUS:
                    # There's a small chance they'll start a conversation
                    if random.random() < self.CONVERSATION_CHANCE:
                        self._start_conversation(v1, v2, current_time)
    
    def _start_conversation(self, v1, v2, current_time):
        """Start a conversation between two villagers.
        
        Args:
            v1: First villager
            v2: Second villager
            current_time: Current time in milliseconds
        """
        # Set both villagers to talking state
        v1.is_talking = True
        v2.is_talking = True
        
        # Record conversation start time
        self.active_conversations[(v1, v2)] = current_time
        
        # Choose a random conversation sound
        if hasattr(v1, 'conversation_sound'):
            try:
                v1.conversation_sound.play()
            except Exception as e:
                print(f"Error playing conversation sound: {e}")
        
        # Notify Interface
        Interface.on_villager_interaction(v1, v2, "conversation_start")
        
        # Create a list of villagers for discussion event
        Interface.on_villager_discussion([v1, v2], ((v1.position.x + v2.position.x) / 2, 
                                                   (v1.position.y + v2.position.y) / 2), 
                                        "casual")
    
    def _clean_cooldowns(self, current_time):
        """Clean up expired cooldowns.
        
        Args:
            current_time: Current time in milliseconds
        """
        # Find expired cooldowns
        expired = []
        for villager, cooldown_time in self.interaction_cooldowns.items():
            if current_time >= cooldown_time:
                expired.append(villager)
        
        # Remove expired cooldowns
        for villager in expired:
            del self.interaction_cooldowns[villager]
    
    def check_building_proximity(self):
        """Check for villagers entering or exiting buildings."""
        for villager in self.game_state.villagers:
            # Skip if villager position is not accessible
            if not hasattr(villager, 'position'):
                continue
                
            v_pos = (villager.position.x, villager.position.y)
            
            # Check all buildings
            for building_id, building in enumerate(self.game_state.village_data['buildings']):
                b_pos = building['position']
                
                # Determine building size
                size_name = building.get('size', 'small')
                size_multiplier = 3 if size_name == 'large' else (2 if size_name == 'medium' else 1)
                building_size = self.game_state.TILE_SIZE * size_multiplier
                
                # Check if villager is inside building
                is_inside = (b_pos[0] <= v_pos[0] < b_pos[0] + building_size and
                            b_pos[1] <= v_pos[1] < b_pos[1] + building_size)
                
                # Check previous state
                was_inside = hasattr(villager, 'inside_building_id') and villager.inside_building_id == building_id
                
                # Handle state change
                if is_inside and not was_inside:
                    # Villager entered building
                    villager.inside_building_id = building_id
                    Interface.on_building_entered(villager, building)
                    
                elif was_inside and not is_inside:
                    # Villager exited building
                    villager.inside_building_id = None
                    Interface.on_building_exited(villager, building)