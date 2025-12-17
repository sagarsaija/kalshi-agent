"use client";

import { useState } from "react";
import { Period } from "@/lib/api";
import { PeriodSelector } from "@/components/ui/period-selector";
import { ThemeToggle } from "@/components/ui/theme-toggle";
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
      {/* Header - Kalshi Style */}
      <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 lg:px-6">
          <div className="flex h-16 items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-2">
                <span className="text-2xl font-bold text-primary">Kalshi</span>
                <span className="text-sm text-muted-foreground font-medium">
                  Dashboard
                </span>
              </div>
            </div>

            {/* Right side controls */}
            <div className="flex items-center gap-3">
              <PeriodSelector value={period} onChange={setPeriod} />
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="p-2 rounded-lg hover:bg-muted transition-colors disabled:opacity-50"
                title="Refresh data"
              >
                <RefreshCw
                  className={`h-5 w-5 text-muted-foreground ${
                    isRefreshing ? "animate-spin" : ""
                  }`}
                />
              </button>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 lg:px-6 py-6 space-y-6">
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
      <footer className="border-t border-border py-6 mt-8">
        <div className="container mx-auto px-4 lg:px-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-primary">Kalshi</span>
              <span className="text-sm text-muted-foreground">
                Personal Dashboard
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              Data refreshes automatically every 60 seconds • Powered by Kalshi
              API
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
