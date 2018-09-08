import random
import hashlib
import hmac

def create_seed():
	characters=["a","b","c","d","e","f","0","1","2","3","4","5","6","7","8","9"]
	seed=""

	for i in range(32):
		seed+=random.choice(characters)

	return str(seed)

def hash(seed):
	hashed=str(hashlib.sha256(str(seed).encode('utf-8')).hexdigest())
	return hashed

def getrandint(server, client, nonce):
	#returns int of random integer 0 to 100
	digits=5
	hasher=hmac.new(bytes(str(server), "ascii"), bytes(str(client)+"-"+str(nonce), "ascii"), hashlib.sha512)
	hexadecimal=str(hasher.hexdigest())
	# hexadecimal=hash(str(server)+str(client)+str(nonce))
	decimal=int(hexadecimal[:digits], 16)
	while True:
		if decimal>999999:
			decimal=int(hexadecimal[digits:digits+5], 16)
			digits=digits+5
		else:
			break
	randint=int(int(str(decimal)[-4:])/100)
	if randint==0:
		randint=100
	return randint