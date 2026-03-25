import { Header } from "@/components/layout/header";
import { Hero } from "@/components/landing/hero";
import { Features } from "@/components/landing/features";
import { PricingSection } from "@/components/landing/pricing-section";
import { Testimonials } from "@/components/landing/testimonials";
import { CTA } from "@/components/landing/cta";
import { Footer } from "@/components/layout/footer";

export const dynamic = "force-dynamic";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <Hero />
        <Features />
        <PricingSection />
        <Testimonials />
        <CTA />
      </main>
      <Footer />
    </div>
  );
}
