import { Metadata } from "next";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { PricingSection } from "@/components/landing/pricing-section";
import { getPlans } from "@/lib/stripe";
import { Plan } from "@/types";

export const metadata: Metadata = {
  title: "Pricing",
  description: "Simple, transparent pricing for teams of all sizes.",
};

async function fetchPlans(): Promise<Plan[]> {
  try {
    return await getPlans();
  } catch {
    return [];
  }
}

export default async function PricingPage() {
  const plans = await fetchPlans();

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 pt-16">
        <PricingSection plans={plans} />
      </main>
      <Footer />
    </div>
  );
}
