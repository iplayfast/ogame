# terrain_tokens.py

# Base terrain types
EMPTY = 0
GRASS_1 = 1
GRASS_2 = 2
GRASS_3 = 3
WATER = 10
PATH_1 = 20
PATH_2 = 21
TREE_1 = 30
TREE_2 = 31
TREE_3 = 32
TREE_4 = 33
TREE_5 = 34
BUILDING = 40  # Base value - building_id gets added to this

# Helper functions for terrain types
def is_grass(token):
    return 1 <= token <= 9
    
def is_water(token):
    return token == WATER
    
def is_path(token):
    return 20 <= token <= 29
    
def is_tree(token):
    return 30 <= token <= 39
    
def is_building(token):
    return token >= BUILDING
    
def get_building_id(token):
    return token - BUILDING if is_building(token) else -1

def is_passable(token):
    return (is_grass(token) or 
            is_path(token) or 
            token == EMPTY)

def get_variant(token):
    if is_grass(token):
        return token
    elif is_path(token):
        return token - PATH_1 + 1
    elif is_tree(token):
        return token - TREE_1 + 1
    return 1
