"use client";

import { useState } from "react";
import { Period } from "@/lib/api";
import { PeriodSelector } from "@/components/ui/period-selector";
import { StatsCards } from "@/components/stats-cards";
import { PortfolioChart } from "@/components/portfolio-chart";
import { PnLChart } from "@/components/pnl-chart";
import { PositionsTable } from "@/components/positions-table";
import { TradesTable } from "@/components/trades-table";
import { SettlementsTable } from "@/components/settlements-table";
import { MarketBreakdown } from "@/components/market-breakdown";
import { TransactionsPanel } from "@/components/transactions-panel";
import { RefreshCw } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

export default function Dashboard() {
  const [period, setPeriod] = useState<Period>("7d");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const queryClient = useQueryClient();

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await queryClient.invalidateQueries();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border sticky top-0 bg-background/95 backdrop-blur z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Kalshi Dashboard</h1>
              <p className="text-sm text-muted-foreground">
                Track your trades and P/L
              </p>
            </div>
            <div className="flex items-center gap-4">
              <PeriodSelector value={period} onChange={setPeriod} />
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="p-2 rounded-lg hover:bg-muted transition-colors disabled:opacity-50"
              >
                <RefreshCw
                  className={`h-5 w-5 ${isRefreshing ? "animate-spin" : ""}`}
                />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6 space-y-6">
        {/* Stats Cards */}
        <StatsCards period={period} />

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PortfolioChart period={period} />
          <PnLChart period={period} />
        </div>

        {/* Tables Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <PositionsTable />
          <MarketBreakdown period={period} />
          <TransactionsPanel />
        </div>

        {/* Trade History Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TradesTable period={period} />
          <SettlementsTable period={period} />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-4 mt-8">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          Data refreshes automatically every 60 seconds • Powered by Kalshi API
        </div>
      </footer>
    </div>
  );
}
