# HealthMate AI

HealthMate AI is an AI-powered personalized health and meal planning platform that helps people organize wellness routines, explore approved health education, and plan meals around their preferences and selected health topics.

## Overview

HealthMate AI brings personalized meal planning, meal replacement, shopping lists, reminders, progress tracking, general health education, and a safety-focused AI health assistant into one workspace. Its assistant is supported by a vetted health knowledge base and provides source attribution for approved information.

The system is designed for educational and wellness support. It is not a diagnostic system, treatment system, or emergency service.

## Problem Statement

Health and nutrition information is often scattered across sources, difficult to evaluate, and hard to apply to an individual routine. People may also struggle to turn general guidance into practical meal plans, shopping tasks, reminders, and progress habits.

HealthMate AI addresses this organization problem by combining reviewed educational content with user preferences and routine-planning tools. It supports informed wellness decisions without presenting itself as a replacement for doctors or other healthcare professionals.

## Key Features

- **Guest-first public experience:** Explore the public interface and ask general educational questions before creating an account.
- **User authentication:** Sign up, sign in, sign out, and access user-scoped personal data through session-based authentication.
- **Personalized profile:** Save activity level, diet, cuisine, cooking time, allergies, and disliked foods.
- **Health conditions:** Select health topics to tailor approved knowledge retrieval and meal compatibility.
- **AI Health Assistant:** Ask general health questions or questions related to saved health topics.
- **Vetted health knowledge:** Browse reviewed entries with evidence context, limitations, and source links.
- **Personalized meal planner:** Generate a weekly plan based on profile preferences and selected health topics.
- **Meal replacement:** Replace planned meals with compatible alternatives.
- **Shopping list:** Aggregate meal ingredients, add custom items, and track purchased items.
- **Reminders:** Create and manage routine reminders.
- **Progress tracking:** Track planned and completed meals and active reminders.
- **Weekly review:** View a summary of planning consistency and meal completion.

## AI Health Assistant

The assistant uses approved health knowledge as its factual source of truth. Gemini is used for explanation and personalization of retrieved context, rather than as an unrestricted source of medical claims.

It:

- Answers general educational health questions.
- Retrieves approved knowledge relevant to the user's question.
- Supports condition-aware explanations using selected health topics.
- Provides source attribution for retrieved information.
- Uses safe fallback behavior when verified information is insufficient or an output fails safety validation.

It does not:

- Diagnose conditions.
- Prescribe treatment.
- Change medication.
- Recommend medication dosages.
- Claim unsupported cures.

## Vetted Health Knowledge System

The knowledge system is designed around trusted sources and reviewed knowledge entries. Entries store source attribution, evidence context, population scope, applicability, limitations, review status, reviewer information, and review dates.

The approval workflow distinguishes entries that are being drafted or reviewed from entries approved for retrieval. Knowledge can be associated with specific health conditions as well as general health and nutrition topics. Only approved content is eligible for the assistant's factual context.

## Technology Stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite for local development
- PostgreSQL for production-oriented deployments, including the provided Docker Compose setup
- React
- Vite
- CSS
- `lucide-react`
- Gemini API
- pytest

## System Architecture

```text
User
	-> Frontend
	-> FastAPI Backend
	-> Authentication / Profile / Meal / Reminder / Progress Services
	-> Knowledge Retrieval
	-> Gemini
	-> Safety Validation
	-> Response
```

The backend validates requests, applies user authorization, retrieves approved knowledge, passes bounded context to Gemini when configured, validates the generated response, and returns source attribution or a safe fallback.

## Project Structure

```text
backend/
	app/                 FastAPI application, database models, services, safety, and seed data
	tests/               Backend workflow and knowledge tests
	requirements.txt     Python dependencies
frontend/
	src/                 React entry point and application styles
	index.html           Vite HTML entry point
	package.json         Frontend scripts and dependencies

	architecture.md      Architecture notes
	knowledge-base.md    Knowledge system notes
README.md
docker-compose.yml     Local PostgreSQL service definition
```

Generated dependencies, build output, virtual environments, test caches, and local database files are intentionally excluded from this overview.

## Installation

### Backend

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
```

If PowerShell execution policy prevents activation, use the Python executable in `.venv\Scripts\` directly or adjust the policy according to your local development settings.

### Frontend

```powershell
cd frontend
npm install
```

## Environment Variables

Real `.env` files must not be committed. The repository includes `backend/.env.example` and `frontend/.env.example` as templates.

### `backend/.env`

```dotenv
DATABASE_URL=sqlite:///./healthmate.db
GEMINI_API_KEY=your_key_here
```

For production, also configure a strong session secret, secure cookies, and the allowed frontend origins. The backend supports `SESSION_SECRET`, `COOKIE_SECURE`, `CORS_ORIGINS`, and `GEMINI_MODEL` for these deployment settings.

### `frontend/.env`

```dotenv
VITE_API_URL=http://localhost:8000/api
```

Never put an actual API key in this README or in frontend environment variables.

## Running Locally

Start the backend in one PowerShell terminal from the repository root:

```powershell
\.venv\Scripts\Activate.ps1
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Start the frontend in a second terminal:

```powershell
cd frontend
npm run dev
```

The frontend normally runs at `http://localhost:5173`, and the API is available at `http://localhost:8000/api`. FastAPI interactive documentation is available at `http://localhost:8000/docs`.

## Testing

Run the backend tests from the `backend` directory:

```powershell
cd backend
python -m pytest -q
```

## Frontend Build

Run the Vite production build from the `frontend` directory:

```powershell
cd frontend
npm run build
```

## Deployment

For a production deployment, use a hosted FastAPI backend, a persistent PostgreSQL database, and a hosted React/Vite frontend. Configure environment variables through the hosting platform, use HTTPS and secure cookies, restrict CORS origins, and keep credentials out of source control.

## Security

- Store secrets such as API keys and session secrets in environment variables.
- Do not commit `.env` files or local credentials.
- Require authentication for personalized profiles, plans, reminders, shopping lists, progress, and the full assistant workflow.
- Enforce authorization in backend APIs so personal records remain user-scoped.
- Handle health and profile data carefully, with appropriate access controls and deployment practices.

## Limitations

HealthMate AI is intended for educational and wellness purposes. It is not a diagnostic system, a treatment system, or a substitute for professional medical care. AI responses are constrained by the approved knowledge system and may use a safe fallback when verified information is unavailable. Some features require authentication, and production use would require additional operational and clinical review.

## Future Scope

- Broader vetted health knowledge
- Improved semantic retrieval
- Expanded personalization
- Stronger analytics
- Browser notification scheduling
- Production monitoring
- Additional integrations

## Screenshots

Screenshots can be added here as the interface evolves.

## Project Status

HealthMate AI is a capstone/internship project demonstrating a full-stack wellness planning workflow, safety-aware AI assistance, and a reviewed health knowledge architecture. It should not be described as fully production-ready without further security, clinical, operational, and deployment validation.

## License

License information to be added.
