global_random_gen = None

def set_rng(rng1):
    global global_random_gen
    global_random_gen = rng1

def get_random_int(i1, i2):
    if i2 > 0:
        return global_random_gen.integers(i1, i2)
    else:
        return i1
