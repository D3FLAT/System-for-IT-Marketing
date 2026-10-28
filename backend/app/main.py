from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .api import strategies

app = FastAPI(title="Информационная система для управления маркетинговой стратегией ИТ-компании")
app.include_router(strategies.router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # Не возвращаем исходные значения (input, ctx): NaN/inf не сериализуются в JSON.
    errors = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": errors})


@app.get("/health", tags=["service"])
def health():
    return {"status": "ok"}
