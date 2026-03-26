import { Header } from "@/components/layout/header";
import { Hero } from "@/components/landing/hero";
import { Features } from "@/components/landing/features";
import { PricingSection } from "@/components/landing/pricing-section";
import { Testimonials } from "@/components/landing/testimonials";
import { CTA } from "@/components/landing/cta";
import { Footer } from "@/components/layout/footer";

export const dynamic = "force-dynamic";

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: process.env.NEXT_PUBLIC_APP_NAME ?? "MyApp",
  applicationCategory: "BusinessApplication",
  description: "The fastest way to build and ship your SaaS product.",
  offers: {
    "@type": "Offer",
    price: "9",
    priceCurrency: "USD",
  },
};

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
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
