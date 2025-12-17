"use client";

import { usePortfolioHistory } from "@/lib/hooks";
import { formatCents, formatDate } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Period } from "@/lib/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";

interface PortfolioChartProps {
  period: Period;
}

export function PortfolioChart({ period }: PortfolioChartProps) {
  const { data, isLoading } = usePortfolioHistory(period);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Portfolio Value</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] animate-pulse bg-muted rounded" />
        </CardContent>
      </Card>
    );
  }

  const history = data?.history ?? [];

  if (history.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Portfolio Value</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center text-muted-foreground">
            No portfolio history available
          </div>
        </CardContent>
      </Card>
    );
  }

  // Format data for chart
  const chartData = history.map((point) => ({
    timestamp: point.timestamp,
    date: formatDate(point.timestamp),
    value: point.total_value / 100, // Convert to dollars
    balance: point.balance / 100,
    portfolio: point.portfolio_value / 100,
  }));

  const minValue = Math.min(...chartData.map((d) => d.value)) * 0.95;
  const maxValue = Math.max(...chartData.map((d) => d.value)) * 1.05;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle>Portfolio Value</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis
                dataKey="date"
                stroke="#666"
                tick={{ fill: "#888", fontSize: 12 }}
                tickLine={{ stroke: "#666" }}
              />
              <YAxis
                domain={[minValue, maxValue]}
                stroke="#666"
                tick={{ fill: "#888", fontSize: 12 }}
                tickLine={{ stroke: "#666" }}
                tickFormatter={(value) => `$${value.toFixed(0)}`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1f2937",
                  border: "1px solid #374151",
                  borderRadius: "8px",
                }}
                labelStyle={{ color: "#9ca3af" }}
                formatter={(value: number) => [formatCents(value * 100), "Total Value"]}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#3b82f6"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorValue)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
