# System-for-IT-Marketing

Информационная система для управления маркетинговой стратегией ИТ-компании (ВКР).

## Статус

| Компонент | Состояние |
|---|---|
| Каркас: FastAPI + PostgreSQL + Docker Compose | готово |
| Миграции Alembic (стратегии, проекты) | готово |
| `analytics/screening`: отсев проектов по порогу AP | готово, покрыто тестами |
| `POST /strategies/{id}/evaluate` | готово (пока только этап отсева) |
| Отслеживание: показатели, план/факт по периодам | готово |
| Импорт плана и факта из CSV и XLSX (`POST /strategies/{id}/import`) | готово |
| Отклонения, выполнение, статусы (`GET /strategies/{id}/tracking`) | готово |
| Импорт из готовой БД (SQLite и др.) | не начато |
| Цели стратегии, бюджет мероприятий, дашборд, отчёты | не начато |
| `analytics/ranking`: ранжирование по синергии Kc | не начато |
| `analytics/configuration`: имитация и конфигурирование | не начато |
| Frontend: экран отслеживания (React + TypeScript + Tailwind) | написан, не запускался |

## Запуск

```bash
cp .env.example .env        # при желании поменяйте пароль
docker compose up --build
```

API: http://localhost:8000, документация: http://localhost:8000/docs

## Пример сценария

```bash
curl -X POST localhost:8000/strategies -H 'Content-Type: application/json' \
  -d '{"name": "Стратегия 2026"}'

curl -X POST localhost:8000/strategies/1/projects -H 'Content-Type: application/json' \
  -d '{"name": "SEO", "ap": 0.8}'
curl -X POST localhost:8000/strategies/1/projects -H 'Content-Type: application/json' \
  -d '{"name": "Вебинары", "ap": 0.3}'

curl -X POST localhost:8000/strategies/1/evaluate -H 'Content-Type: application/json' \
  -d '{"threshold": 0.5}'
```

## Отслеживание эффективности: импорт плана и факта

Загрузите файл через Swagger (`POST /strategies/{id}/import`) или командой:

```bash
curl -X POST localhost:8000/strategies/1/import -F "file=@examples/kpi_plan_fact.csv"
curl localhost:8000/strategies/1/tracking
```

Формат файла (CSV с `;` или `,`, UTF-8 или CP1251; либо XLSX, первый лист):

| Столбец | Обязателен | Пример |
|---|---|---|
| `показатель` (`kpi`) | да | Лиды |
| `период` (`period`) | да | 2026-01 или 2026-Q1 |
| `план` (`plan`) | да | 100 или 2,5 |
| `факт` (`fact`) | нет, пусто для будущих периодов | 105 |
| `единица` (`unit`) | нет | шт |
| `направление` (`direction`) | нет: `больше` (по умолчанию) или `меньше` | меньше |

Повторная загрузка обновляет существующие значения, дублей не создаёт. При ошибке в любой строке не сохраняется ничего, а ответ содержит номера проблемных строк.

Выполнение плана: для «больше — лучше» это факт/план, для «меньше — лучше» план/факт. Статусы по умолчанию: от 95% — в норме, от 80% — риск, ниже — отставание (границы включительные). Пороги условные, их можно менять параметрами `ok_threshold` и `risk_threshold`.

## Frontend

Нужен Node.js 18+. Backend должен работать на порту 8000.

```bash
cd frontend
npm install
npm run dev
```

Откройте адрес из вывода (обычно http://localhost:5173). Запросы `/api/*` проксируются на backend.

## Тесты (без Docker)

```bash
cd backend
pip install -r requirements.txt
pytest
```

## Структура

```
backend/
  app/          FastAPI: api/ (роутеры), services/ (связка БД и расчётов), models, schemas
  app/importers/ разбор файлов CSV и XLSX
  analytics/    расчётное ядро (screening, tracking), не зависит от БД и HTTP
  alembic/      миграции БД
  tests/
frontend/       React + TypeScript + Tailwind (Vite)
docker-compose.yml
examples/       пример файла для импорта
```
