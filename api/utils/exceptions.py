from fastapi import HTTPException, status

class ExceptionNotFound(HTTPException):
    def __init__(self, detail: str = "Não encontrado"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
class ExceptionBadRequest(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
class ExceptionUnprocessableEntity(HTTPException):
    def __init__(self, detail: str = "Entidade não processável"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)
class ExceptionInternalServerError(HTTPException):
    def __init__(self, detail: str = "Erro interno no servidor"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
    
class ExceptionUnauthorized(HTTPException):
    def __init__(self, detail: str = "Não autorizado"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
    
class ExceptionForbidden(HTTPException):
    def __init__(self, detail: str = "Acesso negado"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
    
class ExceptionInvalidId(HTTPException):
    def __init__(self, detail: str = "ID inválido"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class ExceptionInvalidUserType(HTTPException):
    def __init__(self, detail: str = "Tipo de usuário inválido"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class ExceptionCanceledEnrollment(HTTPException):
    def __init__(self, detail: str = "Matrícula já cancelada"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class ExceptionUnauthorizedStudent(HTTPException):
    def __init__(self, detail: str = "Aluno não autorizado a cancelar matrícula"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
        
class ExceptionInvalidData(HTTPException):
    def __init__(self, detail: str = "Dados inválidos"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
class ExceptionCustomNotFound(HTTPException):
    def __init__(self, entity: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity} não encontrad{entity[-1] == 'a' and 'a' or 'o'}")
        
class ExceptionConflict(HTTPException):
    def __init__(self, detail: str = "Conflito"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class CSVValidationError(HTTPException):
    def __init__(self, detail: list):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

def exception_nao_encontrado(entity: str):
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity} não encontrad{entity[-1] == 'a' and 'a' or 'o'}"
    )
    
def exception_nao_autorizado():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não autorizado"
    )

def exception_acesso_negado():
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado"
    )
    
def exception_invalid_id():
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="ID inválido"
    )

def exception_invalid_query(str: str):
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail=f"Query inválida: {str}"
    )
    
def exception_tipo_usuario_invalido():
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de usuário inválido"
    )
    
def exception_invalid_data():
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Dados inválidos"
    )

def exception_internal_server_error(str: str):
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str
    )
    
