"use client";

import { useState } from "react";
import { Search, Loader2, ExternalLink, TrendingUp, BarChart3 } from "lucide-react";
import { Card } from "@/components/ui/card";

interface MarketData {
  ticker: string;
  title: string;
  subtitle?: string;
  yes_bid: number | null;
  yes_ask: number | null;
  no_bid: number | null;
  no_ask: number | null;
  volume_24h: number | null;
  open_interest: number | null;
  status: string;
  implied_probability: string | null;
}

interface AnalysisResult {
  ticker: string;
  market: MarketData | null;
  analysis: string;
  research_report: string | null;
}

export function URLAnalyzer() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!url.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("/api/research/analyze-url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to analyze URL");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* URL Input */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Analyze Kalshi Market</h2>
        <p className="text-muted-foreground text-sm mb-4">
          Paste a Kalshi market URL to get AI-powered analysis
        </p>
        
        <div className="flex gap-2">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://kalshi.com/markets/..."
            className="flex-1 px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
          />
          <button
            onClick={handleAnalyze}
            disabled={loading || !url.trim()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            Analyze
          </button>
        </div>

        {error && (
          <p className="mt-4 text-sm text-red-500">{error}</p>
        )}
      </Card>

      {/* Results */}
      {result && (
        <>
          {/* Market Overview */}
          {result.market && (
            <Card className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold">{result.market.title}</h3>
                  {result.market.subtitle && (
                    <p className="text-sm text-muted-foreground">{result.market.subtitle}</p>
                  )}
                </div>
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline flex items-center gap-1 text-sm"
                >
                  View on Kalshi
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-muted rounded-lg p-3">
                  <p className="text-sm text-muted-foreground">Yes Price</p>
                  <p className="text-lg font-semibold">
                    {result.market.yes_bid && result.market.yes_ask
                      ? `${result.market.yes_bid}¢ - ${result.market.yes_ask}¢`
                      : "N/A"}
                  </p>
                </div>
                <div className="bg-muted rounded-lg p-3">
                  <p className="text-sm text-muted-foreground">Implied Prob</p>
                  <p className="text-lg font-semibold">
                    {result.market.implied_probability || "N/A"}
                  </p>
                </div>
                <div className="bg-muted rounded-lg p-3">
                  <p className="text-sm text-muted-foreground flex items-center gap-1">
                    <TrendingUp className="h-3 w-3" />
                    24h Volume
                  </p>
                  <p className="text-lg font-semibold">
                    {result.market.volume_24h?.toLocaleString() || "N/A"}
                  </p>
                </div>
                <div className="bg-muted rounded-lg p-3">
                  <p className="text-sm text-muted-foreground flex items-center gap-1">
                    <BarChart3 className="h-3 w-3" />
                    Open Interest
                  </p>
                  <p className="text-lg font-semibold">
                    {result.market.open_interest?.toLocaleString() || "N/A"}
                  </p>
                </div>
              </div>
            </Card>
          )}

          {/* AI Analysis */}
          {result.research_report && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">AI Analysis</h3>
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <div className="whitespace-pre-wrap text-sm">
                  {result.research_report}
                </div>
              </div>
            </Card>
          )}

          {/* Technical Analysis */}
          {result.analysis && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Market Metrics</h3>
              <div className="whitespace-pre-wrap text-sm text-muted-foreground">
                {result.analysis}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
