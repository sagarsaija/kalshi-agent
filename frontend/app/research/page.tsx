"use client";

import { useState } from "react";
import Link from "next/link";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { URLAnalyzer } from "@/components/research/url-analyzer";
import { ResearchChat } from "@/components/research/research-chat";
import { MarketExplorer } from "@/components/research/market-explorer";
import { TrendingMarkets } from "@/components/research/trending-markets";
import { Search, MessageSquare, TrendingUp, BarChart3 } from "lucide-react";

export default function ResearchPage() {
  const [activeTab, setActiveTab] = useState<"analyze" | "explore" | "chat">("analyze");

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 lg:px-6">
          <div className="flex h-16 items-center justify-between">
            {/* Logo & Nav */}
            <div className="flex items-center gap-8">
              <Link href="/" className="text-2xl font-bold text-primary">
                Kalshi Agent
              </Link>
              <nav className="flex items-center gap-6">
                <Link
                  href="/"
                  className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  href="/research"
                  className="text-sm font-medium text-foreground hover:text-primary transition-colors"
                >
                  Research
                </Link>
                <Link
                  href="/trading-bot"
                  className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                >
                  Trading Bot
                </Link>
              </nav>
            </div>

            {/* Right side controls */}
            <div className="flex items-center gap-3">
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 lg:px-6 py-6">
        {/* Page Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Market Research</h1>
          <p className="text-muted-foreground">
            AI-powered analysis of Kalshi prediction markets
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6 border-b border-border pb-4">
          <button
            onClick={() => setActiveTab("analyze")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              activeTab === "analyze"
                ? "bg-primary text-primary-foreground"
                : "bg-muted hover:bg-muted/80"
            }`}
          >
            <Search className="h-4 w-4" />
            Analyze URL
          </button>
          <button
            onClick={() => setActiveTab("explore")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              activeTab === "explore"
                ? "bg-primary text-primary-foreground"
                : "bg-muted hover:bg-muted/80"
            }`}
          >
            <TrendingUp className="h-4 w-4" />
            Explore Markets
          </button>
          <button
            onClick={() => setActiveTab("chat")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              activeTab === "chat"
                ? "bg-primary text-primary-foreground"
                : "bg-muted hover:bg-muted/80"
            }`}
          >
            <MessageSquare className="h-4 w-4" />
            Research Chat
          </button>
        </div>

        {/* Tab Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content Area */}
          <div className="lg:col-span-2">
            {activeTab === "analyze" && <URLAnalyzer />}
            {activeTab === "explore" && <MarketExplorer />}
            {activeTab === "chat" && <ResearchChat />}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <TrendingMarkets />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-6 mt-8">
        <div className="container mx-auto px-4 lg:px-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-primary">
                Kalshi Agent
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              Powered by Claude Sonnet 4.5 via Fal AI
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
