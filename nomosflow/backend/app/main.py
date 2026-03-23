from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes import partners, customers, payments, dunning, churn, ai
from app.middleware.auth import verify_api_key
from app.services.gemini_quota import GeminiQuotaExceededError

app = FastAPI(title="NomosFlow API", version="1.0.0")


@app.exception_handler(GeminiQuotaExceededError)
async def gemini_quota_handler(request: Request, exc: GeminiQuotaExceededError):
    return JSONResponse(
        status_code=429,
        content={
            "error": "gemini_quota_exceeded",
            "message": str(exc),
            "quota": {
                "used": exc.used,
                "limit": exc.limit,
                "resets_at": exc.resets_at.isoformat() + "Z",
            },
        },
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://nomosflow.vercel.app", "https://ornate-truffle-98f047.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_auth = [Depends(verify_api_key)]

app.include_router(partners.router,  prefix="/api/partners",  tags=["Partners"],  dependencies=_auth)
app.include_router(customers.router, prefix="/api/customers", tags=["Customers"], dependencies=_auth)
app.include_router(payments.router,  prefix="/api/payments",  tags=["Payments"],  dependencies=_auth)
app.include_router(dunning.router,   prefix="/api/dunning",   tags=["Dunning"],   dependencies=_auth)
app.include_router(churn.router,     prefix="/api/churn",     tags=["Churn"],     dependencies=_auth)
app.include_router(ai.router,        prefix="/api/ai",        tags=["AI"],        dependencies=_auth)


@app.get("/health")
def health():
    return {"status": "ok", "service": "NomosFlow API"}
