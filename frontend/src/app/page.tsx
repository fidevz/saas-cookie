import { Header } from "@/components/layout/header";
import { Hero } from "@/components/landing/hero";
import { Features } from "@/components/landing/features";
import { PricingSection } from "@/components/landing/pricing-section";
import { Testimonials } from "@/components/landing/testimonials";
import { CTA } from "@/components/landing/cta";
import { Footer } from "@/components/layout/footer";
import { getPlans } from "@/lib/stripe";
import { Plan } from "@/types";

async function fetchPlans(): Promise<Plan[]> {
  try {
    return await getPlans();
  } catch {
    return [];
  }
}

export default async function HomePage() {
  const plans = await fetchPlans();

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <Hero />
        <Features />
        <PricingSection plans={plans} />
        <Testimonials />
        <CTA />
      </main>
      <Footer />
    </div>
  );
}
