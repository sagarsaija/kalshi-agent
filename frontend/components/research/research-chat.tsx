"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Bot, User } from "lucide-react";
import { Card } from "@/components/ui/card";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export function ResearchChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hi! I'm your Kalshi market research assistant. Ask me about any prediction market, paste a Kalshi URL for analysis, or ask general questions about market trends and opportunities.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      // Check if input contains a Kalshi URL
      const kalshiUrl = input.match(/https?:\/\/kalshi\.com\/[^\s]+/)?.[0];

      const response = await fetch("/api/research/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: input,
          kalshi_url: kalshiUrl,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response");
      }

      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.response || "I apologize, but I couldn't generate a response.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "I encountered an error processing your request. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="flex flex-col h-[600px]">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold">Research Assistant</h2>
        <p className="text-sm text-muted-foreground">
          Ask questions about Kalshi markets
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {message.role === "assistant" && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                <Bot className="h-4 w-4 text-primary" />
              </div>
            )}
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              <p className="text-xs opacity-50 mt-1">
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
            {message.role === "user" && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                <User className="h-4 w-4 text-primary-foreground" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
              <Bot className="h-4 w-4 text-primary" />
            </div>
            <div className="bg-muted rounded-lg p-3">
              <Loader2 className="h-4 w-4 animate-spin" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-border">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about a market or paste a Kalshi URL..."
            className="flex-1 px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Try: "What's the probability Bitcoin hits $100k?" or paste a Kalshi URL
        </p>
      </div>
    </Card>
  );
}
