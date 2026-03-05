import bcrypt

password = b"sex" # Твой пароль (обязательно с префиксом b)
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
print(hashed.decode())