"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";

type State = "loading" | "success" | "error";

export default function CancelEmailChangePage() {
  const searchParams = useSearchParams();
  const [state, setState] = useState<State>("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setState("error");
      setMessage("No token provided.");
      return;
    }

    api
      .post<{ detail: string }>("/users/me/email/cancel/", { token }, { skipAuth: true })
      .then((data) => {
        setState("success");
        setMessage(data.detail);
      })
      .catch((err) => {
        setState("error");
        setMessage(err instanceof Error ? err.message : "Something went wrong.");
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="mx-auto max-w-md py-16 text-center space-y-4">
      {state === "loading" && (
        <>
          <div className="text-2xl font-bold">Cancelling email change…</div>
          <p className="text-muted-foreground">Please wait a moment.</p>
        </>
      )}
      {state === "success" && (
        <>
          <div className="text-2xl font-bold">Email change cancelled</div>
          <p className="text-muted-foreground">{message}</p>
          <p className="text-sm text-muted-foreground">
            Your email address has not been changed.
          </p>
        </>
      )}
      {state === "error" && (
        <>
          <div className="text-2xl font-bold">Link invalid</div>
          <p className="text-muted-foreground">{message}</p>
          <p className="text-sm text-muted-foreground">
            The link may have expired or already been used.
          </p>
        </>
      )}
    </div>
  );
}
