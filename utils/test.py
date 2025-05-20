import os

# Путь к текущему файлу
dir_path = os.path.dirname(__file__)

# Путь к файлу firebase-service-account.json
file_path = os.path.join(dir_path, '..\\firebase-service-account.json')

# Проверяем, существует ли файл
if os.path.exists("..\\firebase-service-account.json"):
    print(f"Файл существует: {file_path}")
else:   
    print(f"Файл не существует: {file_path}")
#print(os.path.exists(os.path.join(os.path.dirname(__file__), '../firebase-service-account.json')))