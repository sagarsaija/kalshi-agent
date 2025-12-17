const API_BASE = "/api";

export type Period = "1h" | "1d" | "7d" | "30d" | "all";

export interface Balance {
  balance: number;
  portfolio_value: number;
  available_balance: number;
  bonus_balance: number;
}

export interface Position {
  ticker: string;
  market_title: string;
  position: number;
  market_exposure: number;
  resting_orders_count: number;
  total_traded: number;
  realized_pnl: number;
  fees_paid: number;
}

export interface Fill {
  id: string;
  ticker: string;
  side: "yes" | "no";
  action: "buy" | "sell";
  count: number;
  yes_price: number;
  no_price: number;
  created_at: string;
  is_taker: boolean;
  order_id: string;
}

export interface Settlement {
  id: string;
  ticker: string;
  market_result: "yes" | "no";
  yes_count: number;
  no_count: number;
  revenue: number;
  settled_at: string;
  is_win: boolean;
}

export interface PortfolioHistory {
  timestamp: string;
  ts: number;
  balance: number;
  portfolio_value: number;
  total_value: number;
  pnl: number;
}

export interface DailyPnL {
  date: string;
  realized_pnl: number;
  settlement_count: number;
  wins: number;
  losses: number;
  trade_count: number;
  volume: number;
}

export interface CumulativePnL {
  date: string;
  daily_pnl: number;
  cumulative_pnl: number;
  trade_count: number;
}

export interface Summary {
  balance: number;
  portfolio_value: number;
  total_value: number;
  available_balance: number;
  open_positions_count: number;
  total_exposure: number;
  unrealized_pnl: number;
  realized_pnl: number;
  trade_count: number;
  volume: number;
  period: string;
}

export interface WinRate {
  wins: number;
  losses: number;
  total: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  net_pnl: number;
  period: string;
}

export interface MarketBreakdown {
  ticker: string;
  pnl: number;
  wins: number;
  losses: number;
  count: number;
  win_rate: number;
}

async function fetchApi<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API_BASE}${endpoint}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.append(key, value);
    });
  }
  
  const response = await fetch(url.toString());
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json();
}

export const api = {
  // Portfolio
  getBalance: () => fetchApi<Balance>("/portfolio/balance"),
  getPositions: () => fetchApi<{ positions: Position[]; count: number }>("/portfolio/positions"),
  getPortfolioHistory: (period: Period) =>
    fetchApi<{ history: PortfolioHistory[]; period: string }>("/portfolio/history", { period }),
  getSummary: (period: Period) => fetchApi<Summary>("/portfolio/summary", { period }),

  // Trades
  getFills: (period: Period, limit = 100) =>
    fetchApi<{ fills: Fill[]; cursor: string | null; period: string }>("/trades/fills", {
      period,
      limit: limit.toString(),
    }),
  getSettlements: (period: Period, limit = 100) =>
    fetchApi<{ settlements: Settlement[]; cursor: string | null; period: string }>(
      "/trades/settlements",
      { period, limit: limit.toString() }
    ),
  getRecentTrades: (limit = 20) =>
    fetchApi<{ trades: Fill[] }>("/trades/recent", { limit: limit.toString() }),

  // Analytics
  getDailyPnL: (period: Period) =>
    fetchApi<{ daily_pnl: DailyPnL[]; period: string }>("/analytics/daily-pnl", { period }),
  getCumulativePnL: (period: Period) =>
    fetchApi<{ cumulative_pnl: CumulativePnL[]; period: string }>("/analytics/cumulative-pnl", {
      period,
    }),
  getWinRate: (period: Period) => fetchApi<WinRate>("/analytics/win-rate", { period }),
  getMarketBreakdown: (period: Period) =>
    fetchApi<{ breakdown: MarketBreakdown[]; period: string }>("/analytics/market-breakdown", {
      period,
    }),
};
