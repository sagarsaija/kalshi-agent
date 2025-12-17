"use client";

import { usePositions } from "@/lib/hooks";
import { formatCents, formatCentsWithSign, getPnLColor, cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";

export function PositionsTable() {
  const { data, isLoading } = usePositions();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Open Positions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-12 bg-muted rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const positions = data?.positions ?? [];

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle>Open Positions</CardTitle>
          <span className="text-xs font-medium text-muted-foreground bg-muted px-2 py-1 rounded-full">
            {positions.length} positions
          </span>
        </div>
      </CardHeader>
      <CardContent>
        {positions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground text-sm">
            No open positions
          </div>
        ) : (
          <div className="overflow-x-auto -mx-5 px-5">
            <table className="kalshi-table">
              <thead>
                <tr>
                  <th>Market</th>
                  <th className="text-right">Position</th>
                  <th className="text-right">Exposure</th>
                  <th className="text-right">P/L</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((position) => (
                  <tr key={position.ticker}>
                    <td>
                      <div className="font-medium text-sm">
                        {position.ticker}
                      </div>
                      {position.market_title && (
                        <div className="text-xs text-muted-foreground truncate max-w-[180px]">
                          {position.market_title}
                        </div>
                      )}
                    </td>
                    <td className="text-right">
                      <span
                        className={cn(
                          "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
                          position.position > 0
                            ? "bg-kalshi-green/10 text-kalshi-green"
                            : position.position < 0
                            ? "bg-destructive/10 text-destructive"
                            : ""
                        )}
                      >
                        {position.position > 0 ? "+" : ""}
                        {Math.abs(position.position)}{" "}
                        {position.position > 0 ? "YES" : "NO"}
                      </span>
                    </td>
                    <td className="text-right text-sm">
                      {formatCents(position.market_exposure)}
                    </td>
                    <td
                      className={`text-right text-sm font-medium ${getPnLColor(
                        position.realized_pnl
                      )}`}
                    >
                      {formatCentsWithSign(position.realized_pnl)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
