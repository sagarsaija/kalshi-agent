"use client";

import { useMarketBreakdown } from "@/lib/hooks";
import {
  formatCents,
  formatCentsWithSign,
  formatPercent,
  getPnLColor,
  cn,
} from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Period } from "@/lib/api";

interface MarketBreakdownProps {
  period: Period;
}

export function MarketBreakdown({ period }: MarketBreakdownProps) {
  const { data, isLoading } = useMarketBreakdown(period);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>P/L by Market</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-10 bg-muted rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const breakdown = data?.breakdown ?? [];

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle>P/L by Market</CardTitle>
      </CardHeader>
      <CardContent>
        {breakdown.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground text-sm">
            No market data available
          </div>
        ) : (
          <div className="space-y-4">
            {breakdown.slice(0, 10).map((market) => {
              const maxPnL = Math.max(...breakdown.map((m) => Math.abs(m.pnl)));
              const barWidth = (Math.abs(market.pnl) / maxPnL) * 100;

              return (
                <div key={market.ticker} className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-sm truncate max-w-[160px]">
                      {market.ticker}
                    </span>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {market.wins}W/{market.losses}L (
                        {formatPercent(market.win_rate)})
                      </span>
                      <span
                        className={cn(
                          "font-semibold text-sm whitespace-nowrap",
                          getPnLColor(market.pnl)
                        )}
                      >
                        {formatCentsWithSign(market.pnl)}
                      </span>
                    </div>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className={cn(
                        "h-full rounded-full transition-all duration-500",
                        market.pnl >= 0 ? "bg-kalshi-green" : "bg-destructive"
                      )}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
