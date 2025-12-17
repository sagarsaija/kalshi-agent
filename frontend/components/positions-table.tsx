"use client";

import { usePositions } from "@/lib/hooks";
import { formatCents, formatCentsWithSign, getPnLColor } from "@/lib/utils";
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
          <span className="text-sm text-muted-foreground">{positions.length} positions</span>
        </div>
      </CardHeader>
      <CardContent>
        {positions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">No open positions</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2 font-medium text-muted-foreground">Market</th>
                  <th className="text-right py-2 font-medium text-muted-foreground">Position</th>
                  <th className="text-right py-2 font-medium text-muted-foreground">Exposure</th>
                  <th className="text-right py-2 font-medium text-muted-foreground">P/L</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((position) => (
                  <tr key={position.ticker} className="border-b border-border/50 hover:bg-muted/50">
                    <td className="py-3">
                      <div className="font-medium">{position.ticker}</div>
                      {position.market_title && (
                        <div className="text-xs text-muted-foreground truncate max-w-[200px]">
                          {position.market_title}
                        </div>
                      )}
                    </td>
                    <td className="text-right py-3">
                      <span
                        className={
                          position.position > 0
                            ? "text-green-500"
                            : position.position < 0
                            ? "text-red-500"
                            : ""
                        }
                      >
                        {position.position > 0 ? "+" : ""}
                        {position.position} {position.position > 0 ? "YES" : "NO"}
                      </span>
                    </td>
                    <td className="text-right py-3">{formatCents(position.market_exposure)}</td>
                    <td className={`text-right py-3 ${getPnLColor(position.realized_pnl)}`}>
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
