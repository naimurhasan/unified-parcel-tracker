# 📦 Unified Parcel Tracker

**Unified Parcel Tracker** is a containerized web application designed to **track parcels from multiple courier services** through a single unified dashboard.
It integrates background task processing, a PostgreSQL database, and Redis-based Celery workers for asynchronous operations — all orchestrated using Docker Compose.

🎥 **[Project Demo Video](0d1aa64d-e5a7-43c0-82a9-6f5195990e01.mp4)**

<video width="640" controls>
  <source src="0d1aa64d-e5a7-43c0-82a9-6f5195990e01.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

---

## 🚀 Features

* **Unified Tracking:** Track parcels across different courier APIs (e.g., FedEx, DHL, UPS, etc.) in one interface.
* **Background Tasks:** Celery + Redis handle background updates and sync jobs.
* **Admin Dashboard:** Monitor database and tasks via Adminer and Flower dashboards.
* **API-Driven:** Built using a modern Python web stack (FastAPI / Flask style).
* **Modular Design:** Clean structure with separate modules for models, schemas, tasks, and templates.
* **Dockerized:** Fully containerized with isolated services for development and production.

---

## ⚙️ Tech Stack

| Component            | Technology Used                        |
| -------------------- | -------------------------------------- |
| **Backend**          | Python (FastAPI / Flask)               |
| **Database**         | PostgreSQL                             |
| **Task Queue**       | Celery                                 |
| **Broker**           | Redis                                  |
| **Admin Tool**       | Adminer (DB) + Flower (Celery Monitor) |
| **Containerization** | Docker Compose                         |

---

## 🐳 Docker Setup

### 1️⃣ Build and Run

```bash
docker-compose up --build
```

This command builds all services (web, db, redis, worker, beat, flower, adminer) and starts the application stack.

### 2️⃣ Access Services

| Service      | URL                                            | Description                                          |
| ------------ | ---------------------------------------------- | ---------------------------------------------------- |
| **Web App**  | [http://localhost:8000](http://localhost:8000) | Main application interface                           |
| **Adminer**  | [http://localhost:8080](http://localhost:8080) | PostgreSQL management dashboard                      |
| **Flower**   | [http://localhost:5555](http://localhost:5555) | Celery monitoring dashboard                          |
| **Database** | localhost:5432                                 | PostgreSQL (username: postgres / password: password) |

---

## ⚡ Environment Variables

Set in `docker-compose.yml`:

```bash
DATABASE_URL=postgresql://postgres:password@db:5432/unified_parcel_tracker
REDIS_URL=redis://redis:6379/0
```

---

## 🧩 Celery Services

The project includes three Celery-related containers:

* **worker** → Executes background jobs.
* **beat** → Schedules periodic tasks (e.g., parcel updates).
* **flower** → Web UI to monitor tasks.

---

## 🧪 Local Development (Optional)

If you prefer running outside Docker:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload
```

---

## 🧰 Useful Commands

```bash
# Run Celery worker
celery -A app.celery_app worker --loglevel=info

# Run Celery beat scheduler
celery -A app.celery_app beat --loglevel=info

# Start Flower monitoring tool
celery -A app.celery_app flower --port=5555
```

---

## 🧠 Notes

* The project is a smaller prototype version of the project delivered to actual client
* To integrate new courier APIs, add a new module under `app/vendors/` and register it with the main tracking system.

---

## 🤝 Contributing

Contributions are welcome!
Fork the repo, create a new branch, and submit a pull request.

---

## 📄 License

This project is licensed under the **MIT License**.

