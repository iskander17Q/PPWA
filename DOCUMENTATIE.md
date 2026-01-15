# Documentație Proiect PPAW

## 1. Proiectare

### 1.1 Paradigme utilizate

Aplicația **DroneApp** este construită folosind următoarele paradigme și pattern-uri arhitecturale:

#### Model-View-Controller (MVC)

Aplicația implementează arhitectura MVC pentru separarea responsabilităților:

- **Model**: Reprezentat de clasele SQLAlchemy din `app/models/models.py` care definesc structura bazei de date
- **View**: Template-urile Jinja2 HTML din `app/templates/` pentru interfața utilizatorului
- **Controller**: Rutele FastAPI din `app/controllers/` care gestionează cererile HTTP

```python
# Exemplu: Controller pentru utilizatori
@router.get("/")
def users_index(request: Request, db: Session = Depends(get_db)):
    accessor = _get_accessor(db)
    users = accessor.list_users(active_only=False)
    return templates.TemplateResponse("users/index.html", {
        "request": request,
        "users": users,
    })
```

#### API RESTful

Aplicația expune endpoint-uri REST pentru integrare cu sisteme externe:

```python
@app.get('/api/users', response_model=List[dict])
def get_users(db: Session = Depends(get_db)):
    accessor = UsersAccessor(db)
    users = accessor.list_users()
    return [_serialize_user_basic(u) for u in users]
```

#### ORM Code First

Aplicația folosește abordarea **Code First** cu SQLAlchemy și Alembic pentru migrații:

- Modelele sunt definite în Python ca clase SQLAlchemy
- Schema bazei de date este generată automat din modele
- Migrațiile sunt gestionate prin Alembic

```python
class User(Base):
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(120))
    role = Column(String(10), nullable=False, server_default="USER")
    plan_id = Column(BigInteger, ForeignKey('subscription_plans.id'), nullable=False)
    
    plan = relationship('SubscriptionPlan', back_populates='users')
    processing_runs = relationship('ProcessingRun', back_populates='user')
```

#### Layered Architecture (Arhitectură pe straturi)

Aplicația este organizată în straturi clare:

1. **Accessor Layer** (`app/accessors/`): Abstrage accesul la baza de date
2. **Service Layer** (`app/services/`): Conține logica de business
3. **Controller Layer** (`app/controllers/`): Gestionează cererile HTTP
4. **API Layer** (`app/api/`): Endpoint-uri REST pentru integrare

### 1.2 De ce au fost alese aceste paradigme?

#### MVC pentru separarea responsabilităților

- **Mentenabilitate**: Modificările în logica de business nu afectează interfața
- **Testabilitate**: Fiecare componentă poate fi testată independent
- **Scalabilitate**: Ușor de extins cu noi funcționalități

#### Code First ORM pentru flexibilitate

- **Versionare**: Migrațiile Alembic permit versionarea schimbărilor în schema bazei de date
- **Portabilitate**: Aplicația poate rula pe diferite baze de date (SQLite, PostgreSQL)
- **Type Safety**: Modelele Python oferă verificare statică a tipurilor

```python
# Migrație Alembic pentru adăugarea câmpului phone
def upgrade():
    op.add_column('users', sa.Column('phone', sa.String(length=30), nullable=True))
```

#### FastAPI pentru performanță și modernitate

- **Performanță**: FastAPI este unul dintre cele mai rapide framework-uri Python
- **Documentație automată**: Swagger UI generat automat
- **Type Hints**: Suport nativ pentru type hints Python
- **Async/Await**: Suport pentru operațiuni asincrone

#### Layered Architecture pentru organizare

- **Reutilizare**: Serviciile pot fi folosite de multiple controlere
- **Testare**: Fiecare strat poate fi testat izolat
- **Dependency Injection**: FastAPI oferă DI nativă pentru dependențe

### 1.3 Arhitectura aplicației

Aplicația este structurată în module care interacționează pentru a oferi funcționalitatea completă:

#### Module principale

**1. Modul de Autentificare și Autorizare**

- **Middleware**: `AttachUserAndProtectUIMiddleware` verifică autentificarea pentru rutele UI
- **Dependencies**: `get_current_user_api` pentru protecția endpoint-urilor API
- **Session Management**: Folosește `SessionMiddleware` pentru gestionarea sesiunilor

```python
class AttachUserAndProtectUIMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        if path.startswith('/auth') or path.startswith('/static') or path.startswith('/api'):
            return await call_next(request)
        
        user_id = get_user_from_session(request)
        if not user_id:
            return RedirectResponse(url='/auth/login')
        
        # Attach user to request.state for templates
        user = db.query(User).filter(User.id == user_id).first()
        request.state.user = user
        return await call_next(request)
```

**2. Modul de Management Utilizatori**

- **Accessor**: `UsersAccessor` - operații CRUD pe baza de date
- **Service**: `UsersService` - logica de business (validări, cache)
- **Controller**: `users_controller` - rute HTTP pentru UI
- **API**: Endpoint-uri REST pentru integrare

**3. Modul de Analiză Imagini**

- **Service**: `rgb_analyzer.py` - analizează imagini pentru vegetație
- **Service**: `pdf_report.py` - generează rapoarte PDF
- **API**: `/api/analyze` - endpoint pentru upload și analiză

```python
def analyze_image(path: str, workdir: str) -> Tuple[Dict[str, Any], Dict[str, str]]:
    arr = _load_image_rgb(path)
    exg = compute_exg(arr)  # Excess Green Index
    vari = compute_vari(arr)  # Visible Atmospherically Resistant Index
    mask = make_mask_from_exg(exg)
    
    coverage = float(mask.mean() * 100.0)
    health_score = compute_health_score(exg, vari, coverage)
    
    return metrics, assets
```

**4. Modul de Planuri de Abonament**

- **Service**: `PlansService` - gestionarea planurilor cu validări de business
- **Controller**: `plans_controller` - interfață pentru administrare
- **Validări**: Previne ștergerea planurilor folosite de utilizatori

**5. Modul de Procesare Rulări**

- **Accessor**: `RunsAccessor` - gestionarea rulărilor de procesare
- **Controller**: `runs_controller` - interfață pentru vizualizare
- **Tracking**: Urmărește statusul analizelor (QUEUED, SUCCESS, FAILED)

#### Fluxul de date

```
Client Request
    ↓
FastAPI Router
    ↓
Middleware (Auth Check)
    ↓
Controller
    ↓
Service Layer (Business Logic)
    ↓
Accessor Layer (Database Access)
    ↓
SQLAlchemy ORM
    ↓
Database
```

#### Interacțiunea între module

**Exemplu: Procesarea unei analize de imagine**

1. **Client** trimite imaginea la `/api/analyze`
2. **Middleware** verifică autentificarea
3. **Controller** (`analyze_api.py`) primește cererea
4. **Service** (`rgb_analyzer.py`) analizează imaginea
5. **Service** (`pdf_report.py`) generează raportul PDF
6. **Accessor** salvează rezultatele în baza de date
7. **Response** returnează raportul și metricile

```python
@router.post('/api/analyze')
async def analyze(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user_api),
    db: Session = Depends(get_db),
):
    # Quota check
    remaining = plan_limit - current_user.free_attempts_used
    if remaining <= 0:
        return JSONResponse({'offer_upgrade': True}, status_code=402)
    
    # Save uploaded image
    input_image = InputImage(user_id=current_user.id, ...)
    db.add(input_image)
    
    # Analyze image
    metrics, assets = analyze_image(upload_path, TEMP_DIR)
    
    # Generate PDF report
    generate_pdf(report_path, meta, assets, upload_path)
    
    # Create processing run record
    processing_run = ProcessingRun(...)
    db.commit()
    
    return JSONResponse({'report_id': report_id, 'metrics': metrics})
```

## 2. Implementare

### 2.1 Business Layer – explicat

Business Layer-ul este implementat în modulul `app/services/` și conține logica de business a aplicației, separată de accesul la date și de prezentare.

#### UsersService

Serviciul pentru gestionarea utilizatorilor implementează:

- **Caching**: Cache-ul pentru listele de utilizatori și detalii
- **Validări de business**: Verificarea limitelor de încercări
- **Operații de activare/dezactivare**: Soft delete pentru utilizatori

```python
class UsersService:
    def __init__(self, users_accessor: UsersAccessor, cache_service: Optional[MemoryCacheService] = None):
        self.users_accessor = users_accessor
        self.cache_service = cache_service
    
    def get_remaining_attempts(self, user: User) -> int:
        limit = self.get_attempts_limit(user)
        used = user.free_attempts_used or 0
        return max(0, limit - used)
    
    def ensure_can_run_analysis(self, user: User) -> None:
        remaining = self.get_remaining_attempts(user)
        if remaining <= 0:
            raise ValueError("Лимит попыток исчерпан. Перейдите на Pro.")
```

#### PlansService

Serviciul pentru planuri implementează reguli de business:

- **Validare la ștergere**: Previne ștergerea planurilor folosite
- **Caching**: Cache pentru listele de planuri
- **Hard delete**: Ștergere definitivă după validare

```python
def delete_plan_hard(self, plan_id: int) -> None:
    plan = self.db.get(SubscriptionPlan, plan_id)
    if not plan:
        raise ValueError(f"План с ID {plan_id} не найден")
    
    # Business rule: check if plan is used
    users_count = self.db.query(User).filter(User.plan_id == plan_id).count()
    if users_count > 0:
        raise ValueError(f"Нельзя удалить тариф '{plan.name}': есть пользователи на этом тарифе.")
    
    self.db.delete(plan)
    self.db.commit()
```

#### RGB Analyzer Service

Serviciul de analiză implementează algoritmi pentru detectarea vegetației:

- **ExG (Excess Green)**: Index pentru detectarea vegetației
- **VARI (Visible Atmospherically Resistant Index)**: Index rezistent la condiții atmosferice
- **Health Score**: Scor de sănătate calculat din metrici

```python
def compute_exg(arr: np.ndarray) -> np.ndarray:
    R = arr[:, :, 0]
    G = arr[:, :, 1]
    B = arr[:, :, 2]
    exg = 2 * G - R - B
    # Normalize to 0..1
    exg_min = exg.min()
    exg = exg - exg_min
    exg_max = exg.max() + EPS
    exg = exg / exg_max
    return exg

def compute_vari(arr: np.ndarray) -> np.ndarray:
    R = arr[:, :, 0]
    G = arr[:, :, 1]
    B = arr[:, :, 2]
    vari = (G - R) / (G + R - B + EPS)
    return np.nan_to_num(vari, nan=0.0)
```

### 2.2 Librării suplimentare utilizate

#### Framework-uri și biblioteci principale

**FastAPI (0.95.1)**
- Framework web modern pentru Python
- Suport pentru async/await
- Validare automată cu Pydantic
- Documentație automată (Swagger/OpenAPI)

**SQLAlchemy (>=2.0)**
- ORM pentru Python
- Suport pentru multiple baze de date
- Query builder puternic
- Relationship management

**Alembic (1.11.1)**
- Sistem de migrații pentru SQLAlchemy
- Versionare a schimbărilor în schema bazei de date
- Rollback support

**Uvicorn (0.22.0)**
- Server ASGI pentru FastAPI
- Suport pentru hot reload în dezvoltare
- Performanță ridicată

#### Biblioteci pentru procesare imagini

**Pillow**
- Procesare imagini
- Conversie între formate
- Manipulare pixel-level

**NumPy**
- Calcul numeric eficient
- Operații pe matrice
- Utilizat pentru procesarea pixelilor

**Matplotlib**
- Generare grafice și heatmap-uri
- Visualizare metrici de analiză
- Export imagini pentru rapoarte

#### Biblioteci pentru securitate și autentificare

**Passlib[bcrypt]**
- Hash-uire parole
- Suport pentru multiple scheme (bcrypt, pbkdf2_sha256)
- Verificare secură a parolelor

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

#### Biblioteci pentru rapoarte

**ReportLab**
- Generare PDF-uri programatic
- Layout complex pentru rapoarte
- Inserare imagini și grafice

#### Alte biblioteci

**python-dotenv**
- Încărcare variabile de mediu din `.env`
- Configurare flexibilă pentru diferite medii

**python-multipart**
- Procesare form-uri multipart
- Necesar pentru upload fișiere

**psycopg2-binary**
- Driver PostgreSQL pentru SQLAlchemy
- Suport pentru baze de date PostgreSQL în producție

### 2.3 Secțiuni de cod sau abordări deosebite

#### 1. Eager Loading pentru optimizare

Aplicația folosește eager loading pentru a evita problema N+1 queries:

```python
def list_users_with_runs_eager(self) -> List[User]:
    # Use selectinload to eager load processing_runs
    return self.db.query(User).options(selectinload(User.processing_runs)).order_by(User.id).all()

def list_users(self, active_only: bool = True) -> List[User]:
    query = (
        self.db.query(User)
        .options(joinedload(User.plan))  # Eager load plan relationship
    )
    if active_only:
        query = query.filter(User.is_active == True)
    return query.order_by(User.id).all()
```

#### 2. Dependency Injection pentru testabilitate

FastAPI oferă DI nativă, permițând injectarea dependențelor:

```python
from app.deps.services import get_users_service

@router.post("/{user_id}/deactivate")
def user_deactivate(
    user_id: int,
    users_service: UsersService = Depends(get_users_service)
):
    users_service.deactivate_user(user_id)
    return RedirectResponse(url=f"/users/{user_id}")
```

#### 3. Caching în-memory pentru performanță

Serviciile folosesc un serviciu de cache pentru optimizare:

```python
class MemoryCacheService:
    def __init__(self):
        self._cache = {}
        self._ttl = {}
    
    def get(self, key: str):
        if key not in self._cache:
            return None
        if time.time() > self._ttl.get(key, 0):
            del self._cache[key]
            del self._ttl[key]
            return None
        return self._cache[key]
    
    def set(self, key: str, value: Any, ttl_seconds: int = 60):
        self._cache[key] = value
        self._ttl[key] = time.time() + ttl_seconds
```

#### 4. Middleware pentru protecție UI

Middleware personalizat pentru protecția rutei UI:

```python
class AttachUserAndProtectUIMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        # Skip auth/static/api endpoints
        if path.startswith('/auth') or path.startswith('/static') or path.startswith('/api'):
            return await call_next(request)
        
        user_id = get_user_from_session(request)
        if not user_id:
            return RedirectResponse(url='/auth/login')
        
        # Attach user to request.state for templates
        db = SessionLocal()
        try:
            user = db.query(User).options(joinedload(User.plan)).filter(User.id == user_id).first()
            db.expunge(user)  # Detach from session
            request.state.user = user
        finally:
            db.close()
        
        return await call_next(request)
```

#### 5. Validare cu Pydantic

Validarea datelor folosind Pydantic pentru type safety:

```python
from pydantic import BaseModel, EmailStr, validator

class UserViewModel(BaseModel):
    email: EmailStr
    name: Optional[str]
    role: str
    plan_id: int
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['USER', 'ADMIN']:
            raise ValueError('Role must be USER or ADMIN')
        return v
```

#### 6. Error Handling robust

Gestionarea erorilor cu rollback automat:

```python
try:
    accessor.create_user(form_data.dict())
except ValueError as exc:
    error_msg = str(exc)
    errors.append(error_msg)
    return templates.TemplateResponse(
        "users/create.html",
        {"request": request, "errors": errors},
        status_code=status.HTTP_400_BAD_REQUEST,
    )
```

#### 7. Quota Management

Sistem de gestionare a limitelor de utilizare:

```python
# Check quota before processing
plan_limit = current_user.plan.free_attempts_limit
remaining = plan_limit - (current_user.free_attempts_used or 0)
if remaining <= 0:
    return JSONResponse({
        'offer_upgrade': True,
        'upgrade_url': '/app/upgrade',
        'message': 'Лимит попыток исчерпан. Перейдите на PRO.'
    }, status_code=402)

# Increment after successful processing
current_user.free_attempts_used = (current_user.free_attempts_used or 0) + 1
db.commit()
```

## 3. Utilizare

### 3.1 Pașii de instalare

#### 3.1.1 Instalare și configurare pentru programator

**Cerințe preliminare:**
- Python 3.8 sau mai nou
- pip (Python package manager)
- Git (opțional, pentru clonare)

**Pași de instalare:**

1. **Clonează sau descarcă proiectul:**
```bash
cd /Users/iskandereivi/Desktop/PPAW/Project/droneapp_fastapi_codefirst
```

2. **Creează un mediu virtual (recomandat):**
```bash
python3 -m venv venv
source venv/bin/activate  # Pe macOS/Linux
# sau
venv\Scripts\activate  # Pe Windows
```

3. **Instalează dependențele:**
```bash
pip install -r requirements.txt
```

4. **Configurează variabilele de mediu:**
Creează un fișier `.env` în directorul `droneapp_fastapi_codefirst/`:
```env
DATABASE_URL=sqlite:///./droneapp.db
APP_SECRET_KEY=your-secret-key-here-change-in-production
PORT=8000
RELOAD=true
```

Pentru PostgreSQL în producție:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/droneapp
APP_SECRET_KEY=strong-secret-key-for-production
PORT=8000
RELOAD=false
```

5. **Inițializează baza de date:**
```bash
# Rulează migrațiile Alembic
alembic upgrade head
```

6. **Populează baza de date cu date de test:**
```bash
python -m app.seed
```

Aceasta va crea:
- Planuri: "Free" (2 încercări) și "Pro" (999999 încercări)
- Utilizatori: admin@droneapp.local (parolă: admin) și user@droneapp.local (parolă: user)

7. **Pornește serverul de dezvoltare:**
```bash
python run_server.py
```

Sau direct cu uvicorn:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

8. **Accesează aplicația:**
- Interfața web: http://127.0.0.1:8000
- Documentația API: http://127.0.0.1:8000/docs
- Interfața alternativă API: http://127.0.0.1:8000/redoc

**Structura directoarelor importante:**
```
droneapp_fastapi_codefirst/
├── app/
│   ├── main.py              # Punct de intrare FastAPI
│   ├── db.py                # Configurare baza de date
│   ├── models/              # Modele SQLAlchemy
│   ├── accessors/           # Acces la date
│   ├── services/            # Logica de business
│   ├── controllers/         # Controlere MVC
│   ├── api/                 # Endpoint-uri REST
│   ├── templates/           # Template-uri HTML
│   └── static/              # Fișiere statice (CSS, JS)
├── alembic/                 # Migrații baza de date
├── uploads/                 # Imagini încărcate
├── reports/                 # Rapoarte PDF generate
├── logs/                    # Fișiere de log
└── requirements.txt         # Dependențe Python
```

#### 3.1.2 Instalare și configurare la beneficiar

**Pentru deployment în producție:**

1. **Instalează Python și dependențele sistem:**
```bash
# Pe Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv postgresql-client

# Pe macOS (cu Homebrew)
brew install python3 postgresql
```

2. **Configurează baza de date PostgreSQL:**
```bash
# Creează baza de date
sudo -u postgres psql
CREATE DATABASE droneapp;
CREATE USER droneapp_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE droneapp TO droneapp_user;
\q
```

3. **Clonează aplicația pe server:**
```bash
git clone <repository-url>
cd droneapp_fastapi_codefirst
```

4. **Configurează mediu virtual:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

5. **Configurează variabilele de mediu:**
Creează `/etc/droneapp/.env`:
```env
DATABASE_URL=postgresql://droneapp_user:secure_password@localhost:5432/droneapp
APP_SECRET_KEY=<generate-strong-secret-key>
PORT=8000
RELOAD=false
```

6. **Rulează migrațiile:**
```bash
alembic upgrade head
```

7. **Creează utilizatorul inițial:**
```bash
python -m app.seed
```

8. **Configurează serviciul systemd (opțional):**
Creează `/etc/systemd/system/droneapp.service`:
```ini
[Unit]
Description=DroneApp FastAPI Application
After=network.target postgresql.service

[Service]
Type=simple
User=droneapp
WorkingDirectory=/opt/droneapp/droneapp_fastapi_codefirst
Environment="PATH=/opt/droneapp/venv/bin"
ExecStart=/opt/droneapp/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

9. **Pornește serviciul:**
```bash
sudo systemctl enable droneapp
sudo systemctl start droneapp
```

10. **Configurează reverse proxy (Nginx):**
```nginx
server {
    listen 80;
    server_name droneapp.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /opt/droneapp/droneapp_fastapi_codefirst/app/static;
    }
}
```

### 3.2 Mod de utilizare

#### 3.2.1 Autentificare

1. Accesează aplicația la adresa configurată (ex: http://127.0.0.1:8000)
2. Aplicația te va redirecționa automat la pagina de login (`/auth/login`)
3. Introdu credențialele:
   - **Admin**: email: `admin@droneapp.local`, parolă: `admin`
   - **User**: email: `user@droneapp.local`, parolă: `user`

#### 3.2.2 Management utilizatori (Admin)

După autentificare ca admin, poți:

**Vizualizare utilizatori:**
- Accesează `/users` pentru lista completă de utilizatori
- Vezi detalii: email, nume, rol, plan, status activ/inactiv

**Creare utilizator nou:**
1. Click pe "Create User" sau accesează `/users/create`
2. Completează formularul:
   - Email (obligatoriu, unic)
   - Nume (opțional)
   - Telefon (opțional)
   - Rol (USER sau ADMIN)
   - Plan de abonament (selectează din lista de planuri)
   - Status activ (checkbox)
3. Click "Save"

**Editare utilizator:**
1. Accesează `/users/{user_id}` pentru detalii
2. Click "Edit" sau accesează `/users/{user_id}/edit`
3. Modifică câmpurile necesare
4. Click "Save"

**Activare/Dezactivare utilizator:**
- Din pagina de detalii, click "Activate" sau "Deactivate"

#### 3.2.3 Management planuri de abonament (Admin)

**Vizualizare planuri:**
- Accesează `/plans` pentru lista de planuri

**Creare plan nou:**
1. Click "Create Plan" sau accesează `/plans/create`
2. Completează:
   - Nume plan (obligatoriu, unic)
   - Limită încercări gratuite (număr întreg)
3. Click "Save"

**Ștergere plan:**
- Click "Delete" pe planul dorit
- **Notă**: Nu poți șterge un plan dacă există utilizatori care îl folosesc

#### 3.2.4 Analiză imagini (Utilizator)

**Prin interfața web:**
1. Accesează `/app/analyze` (după autentificare)
2. Selectează o imagine (format: JPEG, PNG)
3. Opțional: introdu un nume pentru parcea analizată
4. Click "Upload and Analyze"
5. Așteaptă procesarea (poate dura câteva secunde)
6. Vezi rezultatele:
   - Scor de sănătate (0-100)
   - Acoperire vegetație (%)
   - Metrici ExG și VARI
   - Heatmap-uri vizuale
   - Raport PDF generat automat

**Prin API REST:**

```bash
# Upload și analiză
curl -X POST "http://127.0.0.1:8000/api/analyze" \
  -H "Cookie: session=<session-cookie>" \
  -F "file=@image.jpg" \
  -F "plot_name=Field A"

# Răspuns JSON:
{
  "report_id": "abc123...",
  "pdf_url": "/reports/report_abc123.pdf",
  "metrics": {
    "vegetation_coverage_percent": 75.5,
    "exg_mean": 0.65,
    "vari_mean": 0.58,
    "health_score": 72.3
  },
  "remaining": 1
}
```

**Descărcare raport PDF:**
```bash
curl -O "http://127.0.0.1:8000/reports/report_abc123.pdf"
```

#### 3.2.5 Vizualizare rulări de procesare

**Lista rulărilor:**
- Accesează `/runs` pentru toate rulările
- Filtrare după status (QUEUED, SUCCESS, FAILED)
- Filtrare după tip de index (NDVI, ExG, VARI)

**Detalii rulare:**
- Click pe o rulare pentru detalii complete
- Vezi imaginea originală, metricile, și artefactele generate

#### 3.2.6 Limitări și upgrade

**Plan Free:**
- 2 analize gratuite
- După epuizare, vei primi mesaj pentru upgrade la Pro

**Plan Pro:**
- 999999 analize (practic nelimitat)
- Toate funcționalitățile disponibile

**Upgrade:**
- Contactează administratorul pentru upgrade la plan Pro
- Administratorul poate modifica planul utilizatorului din interfața de management

#### 3.2.7 API Documentation

Aplicația oferă documentație interactivă:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

Aici poți:
- Vezi toate endpoint-urile disponibile
- Testa API-ul direct din browser
- Vezi schemele de request/response
- Vezi exemple de cod pentru fiecare endpoint

#### 3.2.8 Logging și debugging

**Loguri aplicație:**
- Fișierele de log sunt salvate în `logs/app.log`
- Format: `%(asctime)s | %(levelname)s | %(name)s | %(message)s`
- Nivel: INFO (poate fi configurat)

**Verificare loguri:**
```bash
tail -f logs/app.log
```

**Debug mode:**
- Setează `RELOAD=true` în `.env` pentru hot reload
- Modificările în cod vor reîncărca automat serverul

---

## Concluzie

Aplicația **DroneApp** este o soluție completă pentru analiza imaginilor din domeniul agricol, construită cu tehnologii moderne Python. Arhitectura modulară și separarea responsabilităților fac aplicația ușor de întreținut și extins. Sistemul de autentificare, management utilizatori, și analiză imagini oferă o experiență completă atât pentru utilizatori, cât și pentru administratori.

Documentația API automată și interfața web intuitivă fac aplicația accesibilă atât pentru utilizatori tehnici, cât și pentru cei non-tehnici.

