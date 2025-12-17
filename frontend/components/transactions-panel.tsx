"use client";

import { useState } from "react";
import {
  useTransactions,
  useTransactionsSummary,
  useAddTransaction,
  useDeleteTransaction,
} from "@/lib/hooks";
import { formatCents, formatDateTime } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";

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
            className="text-xs px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-700 text-white transition-colors"
          >
            {showForm ? "Cancel" : "+ Add"}
          </button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary */}
        {!loadingSummary && summary && (
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div className="bg-green-500/10 rounded p-2 text-center">
              <div className="text-green-500 font-medium">
                {formatCents(summary.total_deposits)}
              </div>
              <div className="text-xs text-muted-foreground">Deposited</div>
            </div>
            <div className="bg-red-500/10 rounded p-2 text-center">
              <div className="text-red-500 font-medium">
                {formatCents(summary.total_withdrawals)}
              </div>
              <div className="text-xs text-muted-foreground">Withdrawn</div>
            </div>
            <div className="bg-blue-500/10 rounded p-2 text-center">
              <div className="text-blue-500 font-medium">
                {formatCents(summary.net_deposited)}
              </div>
              <div className="text-xs text-muted-foreground">Net</div>
            </div>
          </div>
        )}

        {/* Add form */}
        {showForm && (
          <form
            onSubmit={handleSubmit}
            className="space-y-3 p-3 bg-muted/50 rounded-lg"
          >
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setType("deposit")}
                className={`flex-1 py-1.5 px-3 rounded text-sm font-medium transition-colors ${
                  type === "deposit"
                    ? "bg-green-600 text-white"
                    : "bg-muted hover:bg-muted/80 text-muted-foreground"
                }`}
              >
                Deposit
              </button>
              <button
                type="button"
                onClick={() => setType("withdrawal")}
                className={`flex-1 py-1.5 px-3 rounded text-sm font-medium transition-colors ${
                  type === "withdrawal"
                    ? "bg-red-600 text-white"
                    : "bg-muted hover:bg-muted/80 text-muted-foreground"
                }`}
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
              className="w-full px-3 py-2 rounded bg-background border border-border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            <input
              type="text"
              placeholder="Note (optional)"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="w-full px-3 py-2 rounded bg-background border border-border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={addTransaction.isPending}
              className="w-full py-2 rounded bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium disabled:opacity-50 transition-colors"
            >
              {addTransaction.isPending ? "Adding..." : "Add Transaction"}
            </button>
          </form>
        )}

        {/* Transaction list */}
        {loadingTransactions ? (
          <div className="h-32 animate-pulse bg-muted rounded" />
        ) : (
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {transactions?.transactions.length === 0 ? (
              <div className="text-center text-muted-foreground text-sm py-4">
                No transactions yet. Add your first deposit!
              </div>
            ) : (
              transactions?.transactions.map((t) => (
                <div
                  key={t.id}
                  className="flex items-center justify-between py-2 px-2 hover:bg-muted/50 rounded group"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`text-xs px-2 py-0.5 rounded ${
                        t.type === "deposit"
                          ? "bg-green-500/20 text-green-500"
                          : "bg-red-500/20 text-red-500"
                      }`}
                    >
                      {t.type === "deposit" ? "+" : "-"}
                    </span>
                    <div>
                      <div
                        className={`font-medium text-sm ${
                          t.type === "deposit"
                            ? "text-green-500"
                            : "text-red-500"
                        }`}
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
                      className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-400 text-xs px-1 transition-opacity"
                    >
                      ×
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
