"use client";

import { useState, useEffect } from "react";
import { Search, Loader2, ExternalLink, TrendingUp } from "lucide-react";
import { Card } from "@/components/ui/card";

interface Market {
  ticker: string;
  title: string;
  subtitle?: string;
  yes_bid: number | null;
  yes_ask: number | null;
  volume_24h: number | null;
  status: string;
  implied_probability?: string;
}

export function MarketExplorer() {
  const [searchQuery, setSearchQuery] = useState("");
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    setSearched(true);

    try {
      const response = await fetch(`/api/research/search?q=${encodeURIComponent(searchQuery)}&limit=20`);
      
      if (!response.ok) {
        throw new Error("Search failed");
      }

      const data = await response.json();
      setMarkets(data.markets || []);
    } catch (err) {
      console.error("Search error:", err);
      setMarkets([]);
    } finally {
      setLoading(false);
    }
  };

  const getMidPrice = (market: Market) => {
    if (market.yes_bid && market.yes_ask) {
      return ((market.yes_bid + market.yes_ask) / 2).toFixed(1);
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Search */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Explore Markets</h2>
        <p className="text-muted-foreground text-sm mb-4">
          Search for Kalshi markets by keyword
        </p>
        
        <div className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search markets (e.g., Bitcoin, Fed, Election)"
            className="flex-1 px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
          <button
            onClick={handleSearch}
            disabled={loading || !searchQuery.trim()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            Search
          </button>
        </div>
      </Card>

      {/* Results */}
      {searched && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">
              {markets.length > 0 ? `${markets.length} Markets Found` : "No Results"}
            </h3>
          </div>

          {markets.length > 0 ? (
            <div className="space-y-3">
              {markets.map((market) => (
                <div
                  key={market.ticker}
                  className="p-4 bg-muted rounded-lg hover:bg-muted/80 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium">{market.title}</h4>
                      {market.subtitle && (
                        <p className="text-sm text-muted-foreground">{market.subtitle}</p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-sm">
                        <span className="text-muted-foreground">
                          Ticker: <span className="font-mono">{market.ticker}</span>
                        </span>
                        {getMidPrice(market) && (
                          <span className="text-green-500">
                            Yes: {getMidPrice(market)}¢
                          </span>
                        )}
                        {market.volume_24h && (
                          <span className="flex items-center gap-1 text-muted-foreground">
                            <TrendingUp className="h-3 w-3" />
                            {market.volume_24h.toLocaleString()} vol
                          </span>
                        )}
                      </div>
                    </div>
                    <a
                      href={`https://kalshi.com/markets/${market.ticker}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline flex items-center gap-1 text-sm"
                    >
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-8">
              No markets found for "{searchQuery}". Try a different search term.
            </p>
          )}
        </Card>
      )}

      {/* Quick Search Suggestions */}
      {!searched && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Popular Searches</h3>
          <div className="flex flex-wrap gap-2">
            {["Bitcoin", "Fed Rate", "Election", "GDP", "Inflation", "S&P 500", "Weather", "Sports"].map(
              (term) => (
                <button
                  key={term}
                  onClick={() => {
                    setSearchQuery(term);
                    setTimeout(handleSearch, 100);
                  }}
                  className="px-3 py-1.5 bg-muted hover:bg-muted/80 rounded-full text-sm transition-colors"
                >
                  {term}
                </button>
              )
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
