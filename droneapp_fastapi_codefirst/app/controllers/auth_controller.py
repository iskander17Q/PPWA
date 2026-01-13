from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.db import get_db
from app.accessors.users_accessor import UsersAccessor
from app.deps.auth import verify_password, hash_password
from app.db import SessionLocal

templates = Jinja2Templates(directory='app/templates')
router = APIRouter()


@router.get('/auth/login')
def login_page(request: Request):
    return templates.TemplateResponse('auth/login.html', {'request': request, 'error': None})


@router.post('/auth/login')
async def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    from app.models.models import User

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
    finally:
        db.close()

    if not user:
        return templates.TemplateResponse('auth/login.html', {'request': request, 'error': 'Пользователь не найден'}, status_code=401)

    if not user.is_active:
        return templates.TemplateResponse('auth/login.html', {'request': request, 'error': 'Пользователь не активен'}, status_code=401)

    # password verification
    ok = False
    if user.password_hash and user.password_hash not in ("", "fakehash"):
        ok = verify_password(password, user.password_hash)
    else:
        # demo mode: allow 'admin' for ADMIN and 'user' for USER
        if user.role == 'ADMIN' and password == 'admin':
            ok = True
        if user.role == 'USER' and password == 'user':
            ok = True
        if ok:
            # store hashed password for future
            try:
                db = SessionLocal()
                u_db = db.get(type(user), user.id)
                u_db.password_hash = hash_password(password)
                db.add(u_db)
                db.commit()
            finally:
                db.close()

    if not ok:
        return templates.TemplateResponse('auth/login.html', {'request': request, 'error': 'Неверный пароль'}, status_code=401)

    # success - set session
    request.session['user_id'] = user.id
    return RedirectResponse(url='/app/dashboard', status_code=303)


@router.post('/auth/logout')
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url='/auth/login', status_code=303)
