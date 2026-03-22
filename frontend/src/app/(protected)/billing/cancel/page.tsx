import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { CancelSurvey } from "@/components/billing/cancel-survey";

export const metadata: Metadata = {
  title: "Cancel subscription",
};

export default function BillingCancelPage() {
  return (
    <div className="mx-auto max-w-xl space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <Link
          href="/billing"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to billing
        </Link>
      </div>

      <CancelSurvey />
    </div>
  );
}
