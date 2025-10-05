# Orthonyx Symptom Analysis API

A secure, rate-limited FastAPI backend for submitting and analyzing health symptoms using the OpenAI API. The system is containerized with Docker for a reproducible and scalable environment.

## Table of Contents

1. [Features](#features)
2. [Technology Stack](#technology-stack)
3. [Setup and Installation](#setup-and-installation)
4. [Running the Application](#running-the-application)
5. [Running Tests](#running-tests)
6. [API Documentation](#api-documentation)
7. [Bonus???](#bonus)

---

## Features

* **User Authentication**: Secure user signup and signin endpoints.
* **API Key Management**: Encrypted, expiring API keys are generated and rotated upon signin.
* **Symptom Analysis**: An endpoint to submit health data which is then analyzed by the OpenAI API.
* **Submission History**: An endpoint to retrieve a user's complete symptom submission history.
* **Rate Limiting**: Per-user, per-endpoint rate limiting using a Token Bucket algorithm with Redis to protect resources and prevent abuse.
* **Asynchronous**: Built with `asyncio` for high performance on I/O-bound tasks.
* **Containerized**: Fully containerized with Docker Compose for easy setup and deployment.

---

## Technology Stack

This project leverages a modern, asynchronous Python stack to ensure high performance and maintainability.

* **Backend Framework**: **FastAPI** is used for building the API
* **Database**: **PostgreSQL** provides a robust, relational database.
  * **ORM**: **SQLAlchemy 2.0** is used in its async configuration with the `asyncpg` driver for non-blocking database operations.
  * **Migrations**: **Alembic** handles database schema migrations, allowing for version-controlled and reproducible database changes.
* **In-Memory Store**: **Redis** is used for high-speed in-memory storage, used for the rate limiter's Token Bucket algorithm. It is *not yet* used for caching API responses.
* **Authentication**: **Passlib** used for secure password hashing. API keys are managed using the **Cryptography** library (Fernet) for symmetric encryption.
* **Containerization**: **Docker & Docker Compose** create a reproducible and isolated environment for the application, database, and Redis services, simplifying setup for development and deployment.
* **Testing**: **Pytest** is used as the testing framework, with `pytest-asyncio` for handling async code. End-to-end tests are written using **AIOHTTP** to make live requests against the running application.

---

## Setup and Installation

### Prerequisites

* Docker
* Docker Compose

### 1. Clone the Repository

```shell
git clone https://github.com/RandyTunru/orthonyx-backend.git
cd orthonyx-backend
```

### 2. Create Environment Files

You need to create three environment files in the root of the project: `.env.db`, `.env.app`. You may see the files post-fixed with `.example` to understand the contents.

You will also need to generate a `FERNET_KEY` and paste it in `.env.app`. To generate a `FERNET_KEY`, you can run this short Python script:

```shell
pip install cryptography
```

Then run:

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())
```

### 3. Build and Run the Services

Use Docker Compose to build the images and start the services in the background.

```shell
docker compose -f 'compose.yml' up -d --build
```

The services (app, db, redis) will now be running. This will also immediately create database users to handle migrations (migrator) and crud operations to be used by the app (app_user). on first start, the app container should run the migrations to create the tables.

### 4. Run Database Migrations

To run the database migrations, execute the following command:

```shell
docker exec -it orthonyx_app alembic upgrade head
```

---

## Running the Application

The application is started via the `docker compose up -d` command in the setup instructions.

* The API will be available at `http://localhost:8000`.
* To stream the logs from the application, run: `docker compose logs -f app`.
* To stop all services, run: `docker compose down`.

---

## Running Tests

The project includes an end-to-end test suite that runs against the live, containerized application.

1. **Start the Services**: Make sure your application stack is running.

    ```shell
    docker compose up -d
    ```

2. **Run Tests**: Execute `pytest` from the project's root directory. You may need to install the test dependencies on your host machine first.

    ```shell
    # It's recommended to use a virtual environment

    # Install test dependencies
    pip install pytest pytest-asyncio aiohttp

    # Run the tests, from the project's root directory
    python -m pytest -q app/tests/e2e/
    ```

---

## API Documentation

FastAPI automatically generates interactive API documentation. Once the application is running, you can access it at:

* **Swagger UI**: `http://localhost:8000/docs`
* **ReDoc**: `http://localhost:8000/redoc`

### Main Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/auth/signup` | Register a new user and creates an API key.|
| `POST` | `/auth/signin` | Sign in a user, will rotate API key if expires.|
| `POST` | `/symptom-check/` | Submit health data for AI analysis. Requires authentication. |
| `GET`| `/symptom-history/` | Retrieve a history of all previous symptom submissions. Requires authentication. |

Assumptions Made:

* Used credentials (username, email) can not be used again for a new account sign-up, each email and username must be unique
* Client will handle the API key, users will not need to see and handle their API key
* The POST /symptom-check endpoint accepts a specific payload of the following structure

```json
  {
  "age": 35,
  "sex": "female",
  "symptoms": "headache and fever for 2 days",
  "duration": "2 days",
  "severity": 7,
  "additionalNotes": "also experiencing fatigue"
}
```

## Bonus???

A little extra somethin' somethin' ( ͡° ͜ʖ ͡°)

### Bonus Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/ocr-symptom-history` | Submit health data for AI analysis. Requires authentication. The fields here are more loose and can accept any key-value pair |
| `GET` | `/ocr-symptom-history` | Retrieve a history of all previous ocr symptom submissions. Requires authentication. |

Assumptions Made:

* The POST /ocr-symptom-history endpoint accepts a more flexible payload of key-value pairs, allowing users to submit various health data without strict field requirements.
* The endpoint assumes that the client will provide relevant health information in a structured format, but does not enforce specific fields like age or severity. However, there are some needed fields like `age` and `sex` to help the AI provide better analysis.

```json
{
  "age": 34,
  "sex": "female",
  "identified_data": {
    "chief_complaint": "Persistent cough and fatigue",
    "onset_duration": "Approximately 5 days",
    "blood_pressure": "118/76 mmHg",
    "heart_rate_bpm": 82,
    "temperature_f": "99.1",
    "physician_notes": "Lungs clear on auscultation. Mild pharyngeal erythema. Patient reports no difficulty breathing.",
    "wbc_count": 11500
    # Additional key-value pairs can be added here
  }
}
```
