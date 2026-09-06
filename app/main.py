from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path

from app.database import Base, engine
from app.config import SESSION_SECRET_KEY, UPLOAD_DIR
from app.routers import auth, dashboard, patients, consultations

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ambient AI Clinical Scribe")

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY, same_site="lax")
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Serve uploaded recordings
uploads_dir = Path(UPLOAD_DIR)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


@app.get("/__static_check")
def static_check():
    css_file = static_dir / "css" / "app.css"
    return JSONResponse({
        "static_dir": str(static_dir),
        "css_path": str(css_file),
        "css_exists": css_file.exists(),
        "css_size": css_file.stat().st_size if css_file.exists() else None,
    })


@app.exception_handler(HTTPException)
async def auth_redirect_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        if request.headers.get("HX-Request") == "true":
            response = Response(status_code=200)
            response.headers["HX-Redirect"] = "/login"
            return response
        return RedirectResponse("/login", status_code=303)
    return Response(content=str(exc.detail), status_code=exc.status_code)


app.include_router(dashboard.router)
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(consultations.router)
