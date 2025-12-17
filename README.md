# Kalshi Trading Dashboard

A real-time dashboard to track your Kalshi trades, P/L, and portfolio performance.

![Dashboard Preview](https://via.placeholder.com/800x400?text=Kalshi+Dashboard)

## Features

- 📊 **Portfolio Overview** - Track total balance, cash, and portfolio value
- 📈 **P/L Charts** - Visualize daily and cumulative profit/loss
- 📉 **Portfolio History** - Line chart of portfolio value over time
- 🎯 **Win Rate Stats** - Track your trading performance
- 📋 **Trade History** - View all executed trades (fills)
- ✅ **Settlements** - Track resolved positions
- 🏷️ **Market Breakdown** - P/L analysis by market/ticker
- ⏱️ **Time Filters** - 1H, 1D, 7D, 30D, All Time views
- 🔄 **Auto-refresh** - Data updates every 60 seconds

## Tech Stack

**Backend:**

- FastAPI (Python)
- SQLite for local data storage
- Kalshi API with RSA authentication

**Frontend:**

- Next.js 14 (App Router)
- TailwindCSS
- Recharts for charts
- TanStack Query for data fetching

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Kalshi API credentials from [kalshi.com/account/profile](https://kalshi.com/account/profile)

### 1. Clone and Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your credentials
cp .env.example .env
# Edit .env with your API_KEY_ID and PRIVATE_KEY
```

### 2. Configure Environment Variables

Create `backend/.env` with:

```env
API_KEY_ID=your_api_key_id_here
PRIVATE_KEY=-----BEGIN EC PRIVATE KEY-----
your_private_key_content_here
-----END EC PRIVATE KEY-----
```

**Note:** The private key should include the full PEM headers. If your key is a single line, wrap it with:

```
-----BEGIN EC PRIVATE KEY-----
<your key here>
-----END EC PRIVATE KEY-----
```

### 3. Start Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`

### 4. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

## API Endpoints

| Endpoint                                         | Description                         |
| ------------------------------------------------ | ----------------------------------- |
| `GET /api/portfolio/balance`                     | Current balance and portfolio value |
| `GET /api/portfolio/positions`                   | Open positions                      |
| `GET /api/portfolio/history?period=7d`           | Historical portfolio values         |
| `GET /api/portfolio/summary?period=all`          | Summary statistics                  |
| `GET /api/trades/fills?period=7d`                | Trade fills (executed orders)       |
| `GET /api/trades/settlements?period=all`         | Settled positions                   |
| `GET /api/analytics/daily-pnl?period=30d`        | Daily P/L breakdown                 |
| `GET /api/analytics/cumulative-pnl?period=30d`   | Cumulative P/L                      |
| `GET /api/analytics/win-rate?period=all`         | Win/loss statistics                 |
| `GET /api/analytics/market-breakdown?period=all` | P/L by market                       |

**Period options:** `1h`, `1d`, `7d`, `30d`, `all`

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings
│   │   ├── database.py          # SQLite setup
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── kalshi_client.py     # Kalshi API client
│   │   └── routers/
│   │       ├── portfolio.py     # Balance, positions
│   │       ├── trades.py        # Fills, settlements
│   │       └── analytics.py     # P/L calculations
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx             # Dashboard
│   │   ├── providers.tsx        # React Query
│   │   └── globals.css
│   ├── components/
│   │   ├── stats-cards.tsx
│   │   ├── portfolio-chart.tsx
│   │   ├── pnl-chart.tsx
│   │   ├── positions-table.tsx
│   │   ├── trades-table.tsx
│   │   ├── settlements-table.tsx
│   │   └── market-breakdown.tsx
│   ├── lib/
│   │   ├── api.ts               # API client
│   │   ├── hooks.ts             # React Query hooks
│   │   └── utils.ts             # Formatting utilities
│   └── package.json
│
└── README.md
```

## Troubleshooting

### "Could not load private key"

Make sure your private key in `.env` includes the PEM headers and is properly formatted. Kalshi uses EC (Elliptic Curve) keys.

### CORS errors

The backend is configured to allow requests from `localhost:3000`. If you're running the frontend on a different port, update the CORS settings in `backend/app/main.py`.

### Rate limiting

Kalshi has API rate limits (~10 req/s). The dashboard caches data and refreshes every 60 seconds to stay within limits.

## License

MIT
