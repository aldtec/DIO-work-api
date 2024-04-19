from fastapi import FastAPI, status
from workout_api.routers import api_router

# Incluido para permitir paginação
from fastapi_pagination import add_pagination

from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException

class RedirectException(HTTPException):
    pass

app = FastAPI(title='WorkoutApi')
app.include_router(api_router)

# Para lidar com Exceção 303
@app.exception_handler(status.HTTP_303_SEE_OTHER)
async def not_found_handler(request, exc: HTTPException):
    return {"detail": "Recursos movido ou apagado!"}, exc.status_code

# Incluido para permitir paginação
add_pagination(app)
