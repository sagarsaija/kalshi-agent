"use client";

import { useDailyPnL, useCumulativePnL } from "@/lib/hooks";
import { formatCents, formatDate } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Period } from "@/lib/api";
import {
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ComposedChart,
  Line,
} from "recharts";
import { useState } from "react";

interface PnLChartProps {
  period: Period;
}

export function PnLChart({ period }: PnLChartProps) {
  const [showCumulative, setShowCumulative] = useState(true);
  const { data: dailyData, isLoading: dailyLoading } = useDailyPnL(period);
  const { data: cumulativeData, isLoading: cumulativeLoading } =
    useCumulativePnL(period);

  const isLoading = dailyLoading || cumulativeLoading;

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Profit / Loss</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] animate-pulse bg-muted rounded-lg" />
        </CardContent>
      </Card>
    );
  }

  const dailyPnL = dailyData?.daily_pnl ?? [];
  const cumulativePnL = cumulativeData?.cumulative_pnl ?? [];

  if (dailyPnL.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Profit / Loss</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center text-muted-foreground text-sm">
            No P/L data available
          </div>
        </CardContent>
      </Card>
    );
  }

  const chartData = dailyPnL.map((day, index) => ({
    date: formatDate(day.date),
    fullDate: day.date,
    daily: day.realized_pnl / 100,
    cumulative: (cumulativePnL[index]?.cumulative_pnl ?? 0) / 100,
    wins: day.wins,
    losses: day.losses,
    trades: day.trade_count,
  }));

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle>Profit / Loss</CardTitle>
          <button
            onClick={() => setShowCumulative(!showCumulative)}
            className="text-xs px-3 py-1.5 rounded-full bg-muted hover:bg-muted/80 transition-colors font-medium text-muted-foreground"
          >
            {showCumulative ? "Hide" : "Show"} Cumulative
          </button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={chartData}
              margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="hsl(var(--border))"
                strokeOpacity={0.5}
              />
              <XAxis
                dataKey="date"
                stroke="hsl(var(--muted-foreground))"
                tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
                tickLine={{ stroke: "hsl(var(--border))" }}
                axisLine={{ stroke: "hsl(var(--border))" }}
              />
              <YAxis
                yAxisId="daily"
                stroke="hsl(var(--muted-foreground))"
                tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
                tickLine={{ stroke: "hsl(var(--border))" }}
                axisLine={{ stroke: "hsl(var(--border))" }}
                tickFormatter={(value) => `$${value.toFixed(0)}`}
              />
              {showCumulative && (
                <YAxis
                  yAxisId="cumulative"
                  orientation="right"
                  stroke="hsl(var(--muted-foreground))"
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
                  tickLine={{ stroke: "hsl(var(--border))" }}
                  axisLine={{ stroke: "hsl(var(--border))" }}
                  tickFormatter={(value) => `$${value.toFixed(0)}`}
                />
              )}
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                  boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                }}
                labelStyle={{ color: "hsl(var(--muted-foreground))" }}
                itemStyle={{ color: "hsl(var(--foreground))" }}
                formatter={(value: number, name: string) => {
                  const label = name === "daily" ? "Daily P/L" : "Cumulative";
                  return [formatCents(value * 100), label];
                }}
              />
              <Bar yAxisId="daily" dataKey="daily" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.daily >= 0 ? "#00d26a" : "#ef4444"}
                    fillOpacity={0.85}
                  />
                ))}
              </Bar>
              {showCumulative && (
                <Line
                  yAxisId="cumulative"
                  type="monotone"
                  dataKey="cumulative"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
