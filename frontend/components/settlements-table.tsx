"use client";

import { useSettlements } from "@/lib/hooks";
import {
  formatCents,
  formatCentsWithSign,
  formatRelativeTime,
  getPnLColor,
  cn,
} from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Period } from "@/lib/api";
import { CheckCircle, XCircle } from "lucide-react";

interface SettlementsTableProps {
  period: Period;
}

export function SettlementsTable({ period }: SettlementsTableProps) {
  const { data, isLoading } = useSettlements(period, 50);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Settlements</CardTitle>
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

  const settlements = data?.settlements ?? [];

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle>Settlements</CardTitle>
          <span className="text-xs font-medium text-muted-foreground bg-muted px-2 py-1 rounded-full">
            {settlements.length} settlements
          </span>
        </div>
      </CardHeader>
      <CardContent>
        {settlements.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground text-sm">
            No settlements in this period
          </div>
        ) : (
          <div className="overflow-x-auto -mx-5 px-5">
            <table className="kalshi-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Market</th>
                  <th className="text-center">Result</th>
                  <th className="text-right">Contracts</th>
                  <th className="text-right">Payout</th>
                </tr>
              </thead>
              <tbody>
                {settlements.map((settlement) => {
                  const contracts = settlement.yes_count || settlement.no_count;
                  const side = settlement.yes_count > 0 ? "YES" : "NO";

                  return (
                    <tr key={settlement.id}>
                      <td className="text-muted-foreground text-xs">
                        {settlement.settled_at
                          ? formatRelativeTime(settlement.settled_at)
                          : "-"}
                      </td>
                      <td>
                        <div className="font-medium text-sm truncate max-w-[120px]">
                          {settlement.ticker}
                        </div>
                      </td>
                      <td className="text-center">
                        <div className="flex items-center justify-center gap-1.5">
                          {settlement.is_win ? (
                            <CheckCircle className="h-4 w-4 text-kalshi-green" />
                          ) : (
                            <XCircle className="h-4 w-4 text-destructive" />
                          )}
                          <span
                            className={cn(
                              "text-xs font-medium",
                              settlement.is_win
                                ? "text-kalshi-green"
                                : "text-destructive"
                            )}
                          >
                            {settlement.market_result.toUpperCase()}
                          </span>
                        </div>
                      </td>
                      <td className="text-right text-sm">
                        <span
                          className={cn(
                            "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
                            side === "YES"
                              ? "bg-kalshi-green/10 text-kalshi-green"
                              : "bg-destructive/10 text-destructive"
                          )}
                        >
                          {contracts} {side}
                        </span>
                      </td>
                      <td
                        className={cn(
                          "text-right text-sm font-medium",
                          getPnLColor(settlement.revenue)
                        )}
                      >
                        {formatCentsWithSign(settlement.revenue)}
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
