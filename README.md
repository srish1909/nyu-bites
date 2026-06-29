# NYU Bites 🍕

A restaurant and cafe discount discovery platform exclusively for NYU students. Find the best student deals near campus, save your favorites, and ask an AI assistant for personalized recommendations.

## Features

- **Browse & Filter** — Search restaurants by cuisine, price range, discount type, and open-now status
- **Student Discounts** — Verified deals including % off, fixed discounts, free items, and student menus
- **Save Favorites** — Bookmark restaurants to your personal list
- **AI Assistant** — Ask natural language questions like *"cheap sushi open late near Washington Square Park"*
- **NYU-only Access** — Registration requires an `@nyu.edu` email address

## Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — async Python web framework
- [PostgreSQL](https://www.postgresql.org/) + [SQLAlchemy 2.0](https://www.sqlalchemy.org/) — database & ORM
- [Redis](https://redis.io/) — caching and token storage
- [Groq](https://groq.com/) (llama-3.3-70b) — AI agent with tool calling
- JWT authentication with refresh token rotation

**Frontend**
- [React 18](https://react.dev/) — component-based UI
- Axios — API client with auth interceptors

**Infrastructure**
- Docker Compose — local development
- [Render](https://render.com/) — production deployment

## Local Development

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Setup

1. Clone the repo
   ```bash
   git clone https://github.com/srish1909/nyu-bites.git
   cd nyu-bites
   ```

2. Create a `.env` file in the root directory
   ```env
   POSTGRES_USER=nyubites
   POSTGRES_PASSWORD=changeme
   POSTGRES_DB=nyubites
   DATABASE_URL=postgresql+asyncpg://nyubites:changeme@db:5432/nyubites
   REDIS_URL=redis://redis:6379/0
   SECRET_KEY=your-secret-key-here
   ENVIRONMENT=development
   GROQ_API_KEY=your-groq-api-key
   ```

3. Start all services
   ```bash
   docker compose up -d
   ```

4. Seed the database with sample restaurants
   ```bash
   docker exec nyu-bites-api-1 python -m scripts.seed
   ```

5. Open the app at [http://localhost:3000](http://localhost:3000)

The API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

### Running Tests

```bash
docker exec nyu-bites-api-1 python -m pytest tests/ -v
```

## Project Structure

```
nyu-bites/
├── backend/
│   ├── app/
│   │   ├── agent/        # AI agent and tools
│   │   ├── api/v1/       # REST endpoints
│   │   ├── core/         # security, cache, email, rate limiting
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # auth service (Redis token ops)
│   ├── alembic/          # database migrations
│   └── tests/            # pytest test suite
└── frontend/
    └── src/
        ├── api/          # axios client + endpoint functions
        ├── components/   # Nav, RestaurantCard, FilterBar, AgentChat
        └── pages/        # Browse, Saved, Login
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register with @nyu.edu email |
| POST | `/api/v1/auth/login` | Login, receive JWT + refresh token |
| POST | `/api/v1/auth/refresh` | Rotate refresh token |
| POST | `/api/v1/auth/logout` | Revoke tokens |
| GET | `/api/v1/restaurants/` | List restaurants (with filters) |
| POST | `/api/v1/restaurants/` | Submit a new restaurant |
| GET | `/api/v1/users/me/saved` | Get saved restaurants |
| POST | `/api/v1/agent/query` | Ask the AI assistant |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `SECRET_KEY` | JWT signing secret |
| `GROQ_API_KEY` | Groq API key for the AI agent |
| `ENVIRONMENT` | `development` or `production` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins |
