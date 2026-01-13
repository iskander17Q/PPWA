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
from app.models.models import InputImage, ProcessingRun


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

    # Create InputImage record
    input_image = InputImage(
        user_id=current_user.id,
        filename=filename,
        storage_path=upload_path,
    )
    db.add(input_image)
    db.flush()  # Get the ID without committing

    try:
        metrics, assets = analyze_image(upload_path, TEMP_DIR)
    except Exception as e:
        db.rollback()
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
        db.rollback()
        raise HTTPException(status_code=500, detail=f'Error generating PDF: {e}')

    # Create ProcessingRun record
    processing_run = ProcessingRun(
        user_id=current_user.id,
        input_image_id=input_image.id,
        index_type='NDVI',  # Default index type for analyze API
        status='SUCCESS',
    )
    db.add(processing_run)

    # increment user's used attempts
    db.add(current_user)
    current_user.free_attempts_used = (current_user.free_attempts_used or 0) + 1
    
    try:
        db.commit()
        print(f"INFO: Created ProcessingRun ID={processing_run.id} and InputImage ID={input_image.id} for user_id={current_user.id}")
    except Exception as e:
        db.rollback()
        print(f"ERROR: Failed to save ProcessingRun and InputImage: {e}")
        # Continue anyway - the report was generated

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
