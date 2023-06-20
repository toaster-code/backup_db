import numpy as np

# Parameters
n = 5  # Dimension of the secret vector 's'
m = 4  # Number of rows in the random matrix 'A'
q = 23  # Modulus parameter
P = 7  # Factor to multiply the message

# Key Generation
s = np.random.randint(low=0, high=q, size=n)
A = np.random.randint(low=0, high=q, size=(m, n))
public_key = np.mod(np.dot(A, s), q)

# Encryption
r = np.random.randint(low=0, high=q, size=m)
e = np.random.randint(low=-q // 2, high=q // 2, size=m)

ciphertext = np.mod(np.dot(public_key, r) + P * e, q)

# Padding ciphertext
ciphertext_padded = np.concatenate((ciphertext, np.zeros(n)), axis=0)

# Padding secret vector 's'
s_padded = np.concatenate((s, np.zeros(m)), axis=0)

# Decryption
inner_product = np.dot(ciphertext_padded, s_padded.T)  # Compute the inner product
plaintext = np.mod(inner_product, P)

# Print the generated secret vector, public key, ciphertext, and decrypted plaintext
print("Secret vector 's':", s_padded)
print("Public key 'A * s mod q':", public_key)
print("Ciphertext:", ciphertext)
print("Decrypted plaintext:", plaintext)