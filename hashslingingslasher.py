import random

def create_seed():
	characters=["a","b","c","d","e","f","0","1","2","3","4","5","6","7","8","9"]
	seed=""

	for i in range(32):
		seed+=random.choice(characters)

	return str(seed)


def hash(seed):
	hashed=str(int(hash(seed))*2)
	return hashed