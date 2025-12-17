"use client";

import { useSummary, useWinRate } from "@/lib/hooks";
import { formatCents, formatCentsWithSign, formatPercent, getPnLColor } from "@/lib/utils";
import { Card, CardContent } from "./ui/card";
import { Period } from "@/lib/api";
import { TrendingUp, TrendingDown, Wallet, PieChart, Target, Activity } from "lucide-react";

interface StatsCardsProps {
  period: Period;
}

export function StatsCards({ period }: StatsCardsProps) {
  const { data: summary, isLoading: summaryLoading } = useSummary(period);
  const { data: winRate, isLoading: winRateLoading } = useWinRate(period);

  if (summaryLoading || winRateLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[...Array(6)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-4">
              <div className="h-4 bg-muted rounded w-20 mb-2" />
              <div className="h-8 bg-muted rounded w-24" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const stats = [
    {
      label: "Total Balance",
      value: formatCents(summary?.total_value ?? 0),
      icon: Wallet,
      color: "text-blue-500",
    },
    {
      label: "Cash",
      value: formatCents(summary?.balance ?? 0),
      icon: Activity,
      color: "text-slate-400",
    },
    {
      label: "Portfolio Value",
      value: formatCents(summary?.portfolio_value ?? 0),
      icon: PieChart,
      color: "text-purple-500",
    },
    {
      label: "Realized P/L",
      value: formatCentsWithSign(winRate?.net_pnl ?? 0),
      icon: (winRate?.net_pnl ?? 0) >= 0 ? TrendingUp : TrendingDown,
      color: getPnLColor(winRate?.net_pnl ?? 0),
    },
    {
      label: "Win Rate",
      value: formatPercent(winRate?.win_rate ?? 0),
      icon: Target,
      color: (winRate?.win_rate ?? 0) >= 50 ? "text-green-500" : "text-red-500",
    },
    {
      label: "Trades",
      value: `${summary?.trade_count ?? 0}`,
      subtext: `${winRate?.wins ?? 0}W / ${winRate?.losses ?? 0}L`,
      icon: Activity,
      color: "text-orange-500",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {stats.map((stat) => (
        <Card key={stat.label}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
              <span className="text-xs text-muted-foreground">{stat.label}</span>
            </div>
            <div className={`text-xl font-bold ${stat.color}`}>{stat.value}</div>
            {stat.subtext && (
              <div className="text-xs text-muted-foreground mt-1">{stat.subtext}</div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
