"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function ProtectedError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 text-center py-16">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10 mb-6">
        <span className="text-2xl font-bold text-destructive">!</span>
      </div>
      <h1 className="text-2xl font-bold tracking-tight">Something went wrong</h1>
      <p className="mt-3 text-base text-muted-foreground max-w-sm">
        An unexpected error occurred. Please try again or contact support if the problem persists.
      </p>
      {error.digest && (
        <p className="mt-2 text-xs text-muted-foreground font-mono">
          Error ID: {error.digest}
        </p>
      )}
      <div className="mt-8 flex gap-3">
        <Button onClick={reset}>Try again</Button>
        <Button asChild variant="outline">
          <Link href="/dashboard">Go to Dashboard</Link>
        </Button>
      </div>
    </div>
  );
}
