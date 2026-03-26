"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { api } from "@/lib/api";

type State = "loading" | "success" | "error";

export default function CancelEmailChangePage() {
  const t = useTranslations("settings.cancelEmailChange");
  const searchParams = useSearchParams();
  const [state, setState] = useState<State>("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setState("error");
      setMessage(t("noToken"));
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
        setMessage(err instanceof Error ? err.message : t("failed"));
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="mx-auto max-w-md py-16 text-center space-y-4">
      {state === "loading" && (
        <>
          <div className="text-2xl font-bold">{t("loadingTitle")}</div>
          <p className="text-muted-foreground">{t("loadingDescription")}</p>
        </>
      )}
      {state === "success" && (
        <>
          <div className="text-2xl font-bold">{t("successTitle")}</div>
          <p className="text-muted-foreground">{message}</p>
          <p className="text-sm text-muted-foreground">
            {t("successDescription")}
          </p>
        </>
      )}
      {state === "error" && (
        <>
          <div className="text-2xl font-bold">{t("errorTitle")}</div>
          <p className="text-muted-foreground">{message}</p>
          <p className="text-sm text-muted-foreground">
            {t("errorDescription")}
          </p>
        </>
      )}
    </div>
  );
}
