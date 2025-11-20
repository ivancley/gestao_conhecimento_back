from fastapi import APIRouter


from api.v1.conta.controller import router as conta_router
from api.v1.web_link.controller import router as web_link_router
from api.v1.usuario.controller import router as usuario_router

routes = APIRouter(prefix="/api/v1")


routes.include_router(conta_router)
routes.include_router(usuario_router)
routes.include_router(web_link_router)