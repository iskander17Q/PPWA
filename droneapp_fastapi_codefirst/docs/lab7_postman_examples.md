# Lab7 — Postman Examples (DroneAPP API)

Примеры запросов для тестирования API сущности ProcessingRun.

Base URL: http://127.0.0.1:8002

1) GET всех обработок

GET http://127.0.0.1:8002/api/runs


2) GET одной обработки по id

GET http://127.0.0.1:8002/api/runs/1


3) POST — создать новую обработку

POST http://127.0.0.1:8002/api/runs
Headers:
- Content-Type: application/json

Body (raw JSON):
{
  "user_id": 1,
  "index_type": "NDVI",
  "status": "QUEUED"
}

Ожидаемый ответ: 201 Created + тело RunReadDTO


4) PUT — обновить обработку

PUT http://127.0.0.1:8002/api/runs/1
Headers:
- Content-Type: application/json

Body (raw JSON):
{
  "status": "SUCCESS"
}

Ожидаемый ответ: 200 OK + тело RunReadDTO


Ошибки:
- 400 Bad Request — при попытке создать run, если у пользователя нет input images или user не найден
- 404 Not Found — при обращении к несуществующему run
