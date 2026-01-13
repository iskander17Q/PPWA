from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import uuid
from typing import Dict
from app.services.rgb_analyzer import analyze_image
from app.services.pdf_report import generate_pdf

router = APIRouter()

REPORTS_DIR = os.path.abspath(os.path.join(os.getcwd(), 'reports'))
UPLOADS_DIR = os.path.abspath(os.path.join(os.getcwd(), 'uploads'))
TEMP_DIR = os.path.abspath(os.path.join(os.getcwd(), 'reports', 'tmp'))

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Simple in-memory mapping of report_id -> meta
REPORTS_META: Dict[str, Dict] = {}


from fastapi import Depends
from app.deps.auth import get_current_user_api
from app.db import get_db
from sqlalchemy.orm import Session


@router.post('/api/analyze')
async def analyze(
    file: UploadFile = File(...),
    plot_name: str = Form(None),
    current_user = Depends(get_current_user_api),
    db: Session = Depends(get_db),
):
    # Basic validation
    if file.content_type.split('/')[0] != 'image':
        raise HTTPException(status_code=400, detail='Uploaded file is not an image')

    # Quota check
    plan_limit = getattr(current_user.plan, 'free_attempts_limit', None)
    if plan_limit is None:
        # fallback by name
        if getattr(current_user.plan, 'name', '').lower() == 'free':
            plan_limit = 2
        else:
            plan_limit = 999

    remaining = plan_limit - (current_user.free_attempts_used or 0)
    if remaining <= 0:
        # Offer upgrade to PRO — client/UI will show purchase prompt and redirect to /app/upgrade
        return JSONResponse({'offer_upgrade': True, 'upgrade_url': '/app/upgrade', 'message': 'Лимит попыток исчерпан. Перейдите на PRO.'}, status_code=402)

    uid = uuid.uuid4().hex
    filename = f'{uid}_{file.filename}'
    upload_path = os.path.join(UPLOADS_DIR, filename)
    with open(upload_path, 'wb') as fh:
        fh.write(await file.read())

    try:
        metrics, assets = analyze_image(upload_path, TEMP_DIR)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error analysing image: {e}')

    report_id = uuid.uuid4().hex
    report_filename = f'report_{report_id}.pdf'
    report_path = os.path.join(REPORTS_DIR, report_filename)

    meta = {
        'report_id': report_id,
        'original_filename': filename,
        'plot_name': plot_name,
        'metrics': metrics,
        'user_id': current_user.id,
    }

    try:
        generate_pdf(report_path, meta, assets, upload_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error generating PDF: {e}')

    # increment user's used attempts
    db.add(current_user)
    current_user.free_attempts_used = (current_user.free_attempts_used or 0) + 1
    db.commit()

    pdf_url = f'/reports/{report_filename}'
    REPORTS_META[report_id] = meta

    return JSONResponse({'report_id': report_id, 'pdf_url': pdf_url, 'metrics': metrics, 'remaining': plan_limit - current_user.free_attempts_used})


@router.get('/reports/{filename}')
def get_report(filename: str):
    from fastapi.responses import FileResponse
    report_path = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail='Report not found')
    return FileResponse(report_path, media_type='application/pdf', filename=filename)
