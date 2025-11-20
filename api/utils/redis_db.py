import os
import json
from typing import List, Optional

from dotenv import load_dotenv
import redis

# Carregar variáveis de ambiente
load_dotenv()

CAD_PREFIX = "cadastro:"
AGD_PREFIX = "agendamento:" 

class RedisDB:
    def __init__(self):
        self.redis_client = None
        self.connect()
    
    def connect(self):
        try:
            redis_url = os.getenv('REDIS_URL')
            if not redis_url:
                print("❌ REDIS_URL não encontrada nas variáveis de ambiente")
                return
                
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Testa a conexão
            self.redis_client.ping()
            
        except Exception as e:
            print(f"❌ Erro ao conectar ao Redis: {e}")
            self.redis_client = None
    
    def add_message(self, telefone: str, mensagem: str):
        """Adicionar mensagem ao final da lista de mensagens do telefone"""
        try:
            # Verifica se a conexão está ativa
            if not self.redis_client:
                print("❌ Conexão Redis não está ativa")
                return False
            
            # Testa a conexão
            self.redis_client.ping()
            
            # Adiciona a mensagem ao final da lista
            result = self.redis_client.rpush(telefone, mensagem)

            return True
        except Exception as e:
            print(f"❌ Erro ao adicionar mensagem: {e}")
            return False
    
    def get_messages(self, telefone: str) -> List[str]:
        """Recuperar todas as mensagens de um telefone como lista de strings"""
        try:
            # Verifica se a conexão está ativa
            if not self.redis_client:
                print("❌ Conexão Redis não está ativa")
                return []
            
            # Recupera todas as mensagens da lista (do início ao fim)
            mensagens = self.redis_client.lrange(telefone, 0, -1)
            return mensagens if mensagens else []
        except Exception as e:
            print(f"❌ Erro ao recuperar mensagens: {e}")
            return []
    
    def delete_messages(self, telefone: str) -> bool:
        """Deletar todas as mensagens de um telefone"""
        try:
            deleted = self.redis_client.delete(telefone)
            return deleted > 0
        except Exception as e:
            print(f"Erro ao deletar mensagens: {e}")
            return False
    
    def close_connections(self):
        """Fechar conexões"""
        if self.redis_client:
            self.redis_client.close()
    
    def set_json_with_ttl(self, key: str, value: dict, ttl_seconds: int) -> bool:
        try:
            if not self.redis_client:
                print("❌ Conexão Redis não está ativa")
                return False
            self.redis_client.setex(key, ttl_seconds, json.dumps(value, ensure_ascii=False))
            return True
        except Exception as e:
            print(f"❌ Erro ao setar JSON: {e}")
            return False

    def get_json(self, key: str) -> Optional[dict]:
        try:
            if not self.redis_client:
                print("❌ Conexão Redis não está ativa")
                return None
            raw = self.redis_client.get(key)
            return json.loads(raw) if raw else None
        except Exception as e:
            print(f"❌ Erro ao obter JSON: {e}")
            return None

    def expire_key(self, key: str, ttl_seconds: int) -> bool:
        try:
            if not self.redis_client:
                return False
            return bool(self.redis_client.expire(key, ttl_seconds))
        except Exception as e:
            print(f"❌ Erro ao definir TTL: {e}")
            return False

    # helpers específicos p/ cadastro
    def cad_key(self, telefone: str) -> str:
        return CAD_PREFIX + telefone

    def cad_get(self, telefone: str) -> Optional[dict]:
        return self.get_json(self.cad_key(telefone))

    def cad_set(self, telefone: str, data: dict, ttl_seconds: int) -> bool:
        return self.set_json_with_ttl(self.cad_key(telefone), data, ttl_seconds)

    def cad_delete(self, telefone: str) -> bool:
        return self.delete_messages(self.cad_key(telefone))  # reaproveita delete; OK
    
    # helpers específicos p/ agendamento
    def agd_key(self, telefone: str) -> str:
        return AGD_PREFIX + telefone

    def agd_get(self, telefone: str) -> Optional[dict]:
        return self.get_json(self.agd_key(telefone))

    def agd_set(self, telefone: str, data: dict, ttl_seconds: int) -> bool:
        return self.set_json_with_ttl(self.agd_key(telefone), data, ttl_seconds)

    def agd_delete(self, telefone: str) -> bool:
        return self.delete_messages(self.agd_key(telefone))