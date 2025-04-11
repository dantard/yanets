# File with different utility functions used through the code

# Random number generator
random_gen = None

def get_random_int(i1, i2):
    # Return a random integer between i1 and i2-1
    return random_gen.integers(i1, i2+1)

##