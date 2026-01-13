# Lab8 — Postman / Test Examples

Base URL: http://127.0.0.1:8002

1) GET analyze page (UI)
GET http://127.0.0.1:8002/app/analyze

2) POST analyze (API)
POST http://127.0.0.1:8002/api/analyze
Content-Type: multipart/form-data
Body: file (binary), plot_name (text)

Example using curl:

curl -X POST "http://127.0.0.1:8002/api/analyze" -F "file=@/path/to/image.jpg" -F "plot_name=FieldA"

Response JSON:
{
  "report_id": "<uuid>",
  "pdf_url": "/reports/report_<uuid>.pdf",
  "metrics": {"vegetation_coverage_percent": 12.34, "exg_mean": 0.45, "vari_mean": 0.12, "health_score": 25.67}
}

3) Download report
GET http://127.0.0.1:8002/reports/report_<uuid>.pdf

4) View report UI
GET http://127.0.0.1:8002/app/reports/<uuid>

Notes:
- PDF and JSON metadata are saved in the `reports/` directory.
- Uploaded images are stored in `uploads/`.
- NDVI is mentioned as future work for multispectral cameras.
