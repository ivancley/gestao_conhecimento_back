from api.utils.redis_db import RedisDB

def add_message_to_buffer(telefone: str, message: str):
    print(f"🔄 Adicionando mensagem para {telefone}: {message}")
    db = RedisDB()
    result = db.add_message(telefone, message)
    print(f"🔄 Resultado da adição: {result}")
    db.close_connections()
    return result

def get_message_from_buffer(telefone):
    print(f"🔍 Buscando mensagens para {telefone}")
    db = RedisDB()
    response = db.get_messages(telefone)
    print(f"🔍 Mensagens encontradas: {response}")
    db.close_connections()
    return response

def remove_message_from_buffer(telefone):
    print(f"🗑️ Removendo mensagens para {telefone}")
    db = RedisDB()
    result = db.delete_messages(telefone)
    print(f"🗑️ Resultado da remoção: {result}")
    db.close_connections()
    return result

