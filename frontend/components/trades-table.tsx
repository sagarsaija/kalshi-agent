"use client";

import { useFills } from "@/lib/hooks";
import { formatCents, formatRelativeTime, cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Period } from "@/lib/api";

interface TradesTableProps {
  period: Period;
}

export function TradesTable({ period }: TradesTableProps) {
  const { data, isLoading } = useFills(period, 50);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-muted rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const fills = data?.fills ?? [];

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle>Recent Trades</CardTitle>
          <span className="text-xs font-medium text-muted-foreground bg-muted px-2 py-1 rounded-full">
            {fills.length} trades
          </span>
        </div>
      </CardHeader>
      <CardContent>
        {fills.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground text-sm">
            No trades in this period
          </div>
        ) : (
          <div className="overflow-x-auto -mx-5 px-5">
            <table className="kalshi-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Market</th>
                  <th className="text-center">Side</th>
                  <th className="text-right">Qty</th>
                  <th className="text-right">Price</th>
                  <th className="text-right">Cost</th>
                </tr>
              </thead>
              <tbody>
                {fills.map((fill) => {
                  const price =
                    fill.side === "yes" ? fill.yes_price : fill.no_price;
                  const cost = price * fill.count;
                  const isBuy = fill.action === "buy";

                  return (
                    <tr key={fill.id}>
                      <td className="text-muted-foreground text-xs">
                        {fill.created_at
                          ? formatRelativeTime(fill.created_at)
                          : "-"}
                      </td>
                      <td>
                        <div className="font-medium text-sm truncate max-w-[120px]">
                          {fill.ticker}
                        </div>
                      </td>
                      <td className="text-center">
                        <span
                          className={cn(
                            "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
                            fill.side === "yes"
                              ? "bg-kalshi-green/10 text-kalshi-green"
                              : "bg-destructive/10 text-destructive"
                          )}
                        >
                          {fill.action.toUpperCase()} {fill.side.toUpperCase()}
                        </span>
                      </td>
                      <td className="text-right text-sm">{fill.count}</td>
                      <td className="text-right text-sm">{price}¢</td>
                      <td
                        className={cn(
                          "text-right text-sm font-medium",
                          isBuy ? "text-destructive" : "text-kalshi-green"
                        )}
                      >
                        {isBuy ? "-" : "+"}
                        {formatCents(cost)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
