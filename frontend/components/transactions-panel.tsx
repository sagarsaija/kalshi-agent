"use client";

import { useState } from "react";
import {
  useTransactions,
  useTransactionsSummary,
  useAddTransaction,
  useDeleteTransaction,
} from "@/lib/hooks";
import { formatCents, formatDateTime, cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { X } from "lucide-react";

export function TransactionsPanel() {
  const [showForm, setShowForm] = useState(false);
  const [type, setType] = useState<"deposit" | "withdrawal">("deposit");
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");

  const { data: transactions, isLoading: loadingTransactions } =
    useTransactions();
  const { data: summary, isLoading: loadingSummary } = useTransactionsSummary();
  const addTransaction = useAddTransaction();
  const deleteTransaction = useDeleteTransaction();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const amountCents = Math.round(parseFloat(amount) * 100);
    if (amountCents > 0) {
      addTransaction.mutate(
        { type, amount: amountCents, note: note || undefined },
        {
          onSuccess: () => {
            setAmount("");
            setNote("");
            setShowForm(false);
          },
        }
      );
    }
  };

  const handleDelete = (id: number) => {
    if (confirm("Delete this transaction?")) {
      deleteTransaction.mutate(id);
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle>Deposits & Withdrawals</CardTitle>
          <button
            onClick={() => setShowForm(!showForm)}
            className={cn(
              "text-xs px-3 py-1.5 rounded-full font-medium transition-all duration-200",
              showForm
                ? "bg-muted text-muted-foreground hover:bg-muted/80"
                : "bg-primary text-primary-foreground hover:opacity-90"
            )}
          >
            {showForm ? "Cancel" : "+ Add"}
          </button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary */}
        {!loadingSummary && summary && (
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div className="bg-kalshi-green/10 rounded-lg p-3 text-center">
              <div className="text-kalshi-green font-semibold">
                {formatCents(summary.total_deposits)}
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">
                Deposited
              </div>
            </div>
            <div className="bg-destructive/10 rounded-lg p-3 text-center">
              <div className="text-destructive font-semibold">
                {formatCents(summary.total_withdrawals)}
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">
                Withdrawn
              </div>
            </div>
            <div className="bg-kalshi-blue/10 rounded-lg p-3 text-center">
              <div className="text-kalshi-blue font-semibold">
                {formatCents(summary.net_deposited)}
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">Net</div>
            </div>
          </div>
        )}

        {/* Add form */}
        {showForm && (
          <form
            onSubmit={handleSubmit}
            className="space-y-3 p-4 bg-muted/50 rounded-xl animate-fade-in"
          >
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setType("deposit")}
                className={cn(
                  "flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all duration-200",
                  type === "deposit"
                    ? "bg-kalshi-green text-white"
                    : "bg-muted hover:bg-muted/80 text-muted-foreground"
                )}
              >
                Deposit
              </button>
              <button
                type="button"
                onClick={() => setType("withdrawal")}
                className={cn(
                  "flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all duration-200",
                  type === "withdrawal"
                    ? "bg-destructive text-white"
                    : "bg-muted hover:bg-muted/80 text-muted-foreground"
                )}
              >
                Withdrawal
              </button>
            </div>
            <input
              type="number"
              step="0.01"
              min="0"
              placeholder="Amount ($)"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-background border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
              required
            />
            <input
              type="text"
              placeholder="Note (optional)"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-background border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
            />
            <button
              type="submit"
              disabled={addTransaction.isPending}
              className="w-full py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium disabled:opacity-50 hover:opacity-90 transition-all"
            >
              {addTransaction.isPending ? "Adding..." : "Add Transaction"}
            </button>
          </form>
        )}

        {/* Transaction list */}
        {loadingTransactions ? (
          <div className="h-32 animate-pulse bg-muted rounded-lg" />
        ) : (
          <div className="space-y-1 max-h-52 overflow-y-auto">
            {transactions?.transactions.length === 0 ? (
              <div className="text-center text-muted-foreground text-sm py-6">
                No transactions yet. Add your first deposit!
              </div>
            ) : (
              transactions?.transactions.map((t) => (
                <div
                  key={t.id}
                  className="flex items-center justify-between py-2.5 px-3 hover:bg-muted/50 rounded-lg group transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={cn(
                        "text-xs px-2 py-1 rounded-md font-medium",
                        t.type === "deposit"
                          ? "bg-kalshi-green/15 text-kalshi-green"
                          : "bg-destructive/15 text-destructive"
                      )}
                    >
                      {t.type === "deposit" ? "+" : "−"}
                    </span>
                    <div>
                      <div
                        className={cn(
                          "font-semibold text-sm",
                          t.type === "deposit"
                            ? "text-kalshi-green"
                            : "text-destructive"
                        )}
                      >
                        {formatCents(t.amount)}
                      </div>
                      {t.note && (
                        <div className="text-xs text-muted-foreground">
                          {t.note}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">
                      {formatDateTime(t.created_at)}
                    </span>
                    <button
                      onClick={() => handleDelete(t.id)}
                      className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-destructive/10 text-destructive transition-all"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
