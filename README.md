这是一个聊天室项目，使用Fastapi和React实现。

## 项目结构

```text
┌────────────────┐      HTTP/REST           ┌─────────────────┐      ┌────────────┐
│                │ ◄──── (Login, History) ──►│                 │ ◄───►│            │
│  React Client  │                          │  FastAPI Server │      │ PostgreSQL │
│   (Browser)    │                          │                 │      │ (Messages) │
│                │ ◄════ WebSocket ════════►│   (Python)      │ ◄───►└────────────┘
└────────────────┘    (Real-time Chat)      │                 │      ┌────────────┐
                                            └─────────────────┘      │            │
                                                     │               │   Redis    │
                                                     └──────────────►│  (Cache)   │
                                                                     └────────────┘
```

## 目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── utils.py
│   └── tests/
│       └── test_app.py
├── .env
├── .gitignore
├── README.md
├── requirements.txt
├── setup.py
└── venv/
    └── ...
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   ├── pages/
│   ├── App.js
│   ├── index.js
│   └── ...
```