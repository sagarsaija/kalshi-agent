"use client";

import { useQuery } from "@tanstack/react-query";
import { api, Period } from "./api";

export function useBalance() {
  return useQuery({
    queryKey: ["balance"],
    queryFn: api.getBalance,
  });
}

export function usePositions() {
  return useQuery({
    queryKey: ["positions"],
    queryFn: api.getPositions,
  });
}

export function usePortfolioHistory(period: Period) {
  return useQuery({
    queryKey: ["portfolio-history", period],
    queryFn: () => api.getPortfolioHistory(period),
  });
}

export function useSummary(period: Period) {
  return useQuery({
    queryKey: ["summary", period],
    queryFn: () => api.getSummary(period),
  });
}

export function useFills(period: Period, limit = 100) {
  return useQuery({
    queryKey: ["fills", period, limit],
    queryFn: () => api.getFills(period, limit),
  });
}

export function useSettlements(period: Period, limit = 100) {
  return useQuery({
    queryKey: ["settlements", period, limit],
    queryFn: () => api.getSettlements(period, limit),
  });
}

export function useRecentTrades(limit = 20) {
  return useQuery({
    queryKey: ["recent-trades", limit],
    queryFn: () => api.getRecentTrades(limit),
  });
}

export function useDailyPnL(period: Period) {
  return useQuery({
    queryKey: ["daily-pnl", period],
    queryFn: () => api.getDailyPnL(period),
  });
}

export function useCumulativePnL(period: Period) {
  return useQuery({
    queryKey: ["cumulative-pnl", period],
    queryFn: () => api.getCumulativePnL(period),
  });
}

export function useWinRate(period: Period) {
  return useQuery({
    queryKey: ["win-rate", period],
    queryFn: () => api.getWinRate(period),
  });
}

export function useMarketBreakdown(period: Period) {
  return useQuery({
    queryKey: ["market-breakdown", period],
    queryFn: () => api.getMarketBreakdown(period),
  });
}
