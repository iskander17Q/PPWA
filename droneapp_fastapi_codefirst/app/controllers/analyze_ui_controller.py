from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.getcwd(), 'app', 'templates'))


@router.get('/app/analyze', response_class=HTMLResponse)
def analyze_page(request: Request):
    # request.state.user is set in middleware; template uses it to show remaining attempts
    return templates.TemplateResponse('app/analyze.html', {'request': request})


@router.get('/app/dashboard', response_class=HTMLResponse)
def dashboard(request: Request):
    from app.accessors.users_accessor import UsersAccessor
    from app.accessors.runs_accessor import RunsAccessor
    from app.db import SessionLocal

    db = SessionLocal()
    try:
        users = UsersAccessor(db).list_users()
        runs = RunsAccessor(db).list_runs()
        total_users = len(users)
        total_runs = len(runs)
    finally:
        db.close()

    # count reports
    reports_dir = os.path.join(os.getcwd(), 'reports')
    total_reports = 0
    try:
        total_reports = len([f for f in os.listdir(reports_dir) if f.endswith('.pdf')])
    except Exception:
        total_reports = 0

    return templates.TemplateResponse('app/dashboard.html', {'request': request, 'total_users': total_users, 'total_runs': total_runs, 'total_reports': total_reports})


@router.get('/app/reports', response_class=HTMLResponse)
def reports_list(request: Request):
    reports_dir = os.path.join(os.getcwd(), 'reports')
    entries = []
    if os.path.exists(reports_dir):
        for fname in sorted(os.listdir(reports_dir), reverse=True):
            if not fname.endswith('.pdf'):
                continue
            meta = None
            json_path = os.path.join(reports_dir, os.path.splitext(fname)[0] + '.json')
            if os.path.exists(json_path):
                try:
                    import json

                    with open(json_path, 'r') as fh:
                        meta = json.load(fh)
                except Exception:
                    meta = None
            entries.append({'filename': fname, 'meta': meta})
    # show last 20
    entries = entries[:20]
    return templates.TemplateResponse('app/reports.html', {'request': request, 'reports': entries})


@router.get('/app/upgrade', response_class=HTMLResponse)
def upgrade_page(request: Request):
    return templates.TemplateResponse('app/upgrade.html', {'request': request})


@router.get('/app/reports/{report_id}', response_class=HTMLResponse)
def report_page(request: Request, report_id: str):
    # Try in-memory meta first, else try to read JSON file next to the PDF
    from app.api.analyze_api import REPORTS_META
    meta = REPORTS_META.get(report_id)
    if not meta:
        import os, json
        meta_path = os.path.join(os.getcwd(), 'reports', f'report_{report_id}.json')
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r') as fh:
                    meta = json.load(fh)
            except Exception:
                meta = None
    return templates.TemplateResponse('app/report.html', {'request': request, 'meta': meta, 'report_id': report_id})
