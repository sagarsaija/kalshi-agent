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
          <span className="text-sm text-muted-foreground">{fills.length} trades</span>
        </div>
      </CardHeader>
      <CardContent>
        {fills.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">No trades in this period</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2 font-medium text-muted-foreground">Time</th>
                  <th className="text-left py-2 font-medium text-muted-foreground">Market</th>
                  <th className="text-center py-2 font-medium text-muted-foreground">Side</th>
                  <th className="text-right py-2 font-medium text-muted-foreground">Qty</th>
                  <th className="text-right py-2 font-medium text-muted-foreground">Price</th>
                  <th className="text-right py-2 font-medium text-muted-foreground">Cost</th>
                </tr>
              </thead>
              <tbody>
                {fills.map((fill) => {
                  const price = fill.side === "yes" ? fill.yes_price : fill.no_price;
                  const cost = price * fill.count;
                  const isBuy = fill.action === "buy";

                  return (
                    <tr
                      key={fill.id}
                      className="border-b border-border/50 hover:bg-muted/50"
                    >
                      <td className="py-3 text-muted-foreground">
                        {fill.created_at ? formatRelativeTime(fill.created_at) : "-"}
                      </td>
                      <td className="py-3">
                        <div className="font-medium truncate max-w-[150px]">{fill.ticker}</div>
                      </td>
                      <td className="py-3 text-center">
                        <span
                          className={cn(
                            "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
                            fill.side === "yes"
                              ? "bg-green-500/10 text-green-500"
                              : "bg-red-500/10 text-red-500"
                          )}
                        >
                          {fill.action.toUpperCase()} {fill.side.toUpperCase()}
                        </span>
                      </td>
                      <td className="text-right py-3">{fill.count}</td>
                      <td className="text-right py-3">{price}¢</td>
                      <td
                        className={cn(
                          "text-right py-3 font-medium",
                          isBuy ? "text-red-400" : "text-green-400"
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
