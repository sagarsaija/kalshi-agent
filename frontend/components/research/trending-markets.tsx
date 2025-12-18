"use client";

import { useState, useEffect } from "react";
import { TrendingUp, Loader2, ExternalLink, RefreshCw } from "lucide-react";
import { Card } from "@/components/ui/card";

interface TrendingMarket {
  ticker: string;
  title: string;
  yes_bid: number | null;
  yes_ask: number | null;
  volume_24h: number | null;
  implied_probability: string | null;
}

export function TrendingMarkets() {
  const [markets, setMarkets] = useState<TrendingMarket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTrending = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/research/trending?limit=8");
      
      if (!response.ok) {
        throw new Error("Failed to fetch trending markets");
      }

      const data = await response.json();
      setMarkets(data.markets || []);
    } catch (err) {
      setError("Failed to load trending markets");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrending();
  }, []);

  const getMidPrice = (market: TrendingMarket) => {
    if (market.yes_bid && market.yes_ask) {
      return ((market.yes_bid + market.yes_ask) / 2).toFixed(1);
    }
    return null;
  };

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          <h3 className="font-semibold">Trending Markets</h3>
        </div>
        <button
          onClick={fetchTrending}
          disabled={loading}
          className="p-1.5 hover:bg-muted rounded-lg transition-colors"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <p className="text-sm text-muted-foreground text-center py-4">{error}</p>
      ) : (
        <div className="space-y-2">
          {markets.map((market, index) => (
            <a
              key={market.ticker}
              href={`https://kalshi.com/markets/${market.ticker}`}
              target="_blank"
              rel="noopener noreferrer"
              className="block p-3 bg-muted rounded-lg hover:bg-muted/80 transition-colors group"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate group-hover:text-primary transition-colors">
                    {market.title}
                  </p>
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    {getMidPrice(market) && (
                      <span className="text-green-500 font-medium">
                        {getMidPrice(market)}¢
                      </span>
                    )}
                    {market.implied_probability && (
                      <span>{market.implied_probability}</span>
                    )}
                    {market.volume_24h && (
                      <span>{market.volume_24h.toLocaleString()} vol</span>
                    )}
                  </div>
                </div>
                <ExternalLink className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 ml-2" />
              </div>
            </a>
          ))}
        </div>
      )}

      {!loading && markets.length === 0 && !error && (
        <p className="text-sm text-muted-foreground text-center py-4">
          No trending markets available
        </p>
      )}
    </Card>
  );
}
