"use client";

import { useSettlements } from "@/lib/hooks";
import { formatCents, formatCentsWithSign, formatRelativeTime, getPnLColor, cn } from "@/lib/utils";
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
          <span className="text-sm text-muted-foreground">{settlements.length} settlements</span>
        </div>
      </CardHeader>
      <CardContent>
        {settlements.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No settlements in this period
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2 font-medium text-muted-foreground">Time</th>
                  <th className="text-left py-2 font-medium text-muted-foreground">Market</th>
                  <th className="text-center py-2 font-medium text-muted-foreground">Result</th>
                  <th className="text-right py-2 font-medium text-muted-foreground">Contracts</th>
                  <th className="text-right py-2 font-medium text-muted-foreground">Payout</th>
                </tr>
              </thead>
              <tbody>
                {settlements.map((settlement) => {
                  const contracts = settlement.yes_count || settlement.no_count;
                  const side = settlement.yes_count > 0 ? "YES" : "NO";

                  return (
                    <tr
                      key={settlement.id}
                      className="border-b border-border/50 hover:bg-muted/50"
                    >
                      <td className="py-3 text-muted-foreground">
                        {settlement.settled_at ? formatRelativeTime(settlement.settled_at) : "-"}
                      </td>
                      <td className="py-3">
                        <div className="font-medium truncate max-w-[150px]">
                          {settlement.ticker}
                        </div>
                      </td>
                      <td className="py-3 text-center">
                        <div className="flex items-center justify-center gap-1">
                          {settlement.is_win ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : (
                            <XCircle className="h-4 w-4 text-red-500" />
                          )}
                          <span
                            className={cn(
                              "text-xs font-medium",
                              settlement.is_win ? "text-green-500" : "text-red-500"
                            )}
                          >
                            {settlement.market_result.toUpperCase()}
                          </span>
                        </div>
                      </td>
                      <td className="text-right py-3">
                        {contracts} {side}
                      </td>
                      <td className={cn("text-right py-3 font-medium", getPnLColor(settlement.revenue))}>
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
