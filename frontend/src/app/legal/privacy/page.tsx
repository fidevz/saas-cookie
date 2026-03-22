import { Metadata } from "next";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";

export const metadata: Metadata = {
  title: "Privacy Policy",
};

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? "MyApp";

export default function PrivacyPolicyPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 pt-24 pb-16 px-4">
        <article className="mx-auto max-w-2xl">
          <div className="mb-10">
            <h1 className="text-3xl font-bold tracking-tight">Privacy Policy</h1>
            <p className="mt-2 text-sm text-muted-foreground">Last updated: January 2025</p>
            <p className="mt-4 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              <strong>Template notice:</strong> This is placeholder content. Replace with your actual Privacy Policy before going live.
            </p>
          </div>

          <div className="space-y-8 text-sm leading-relaxed">
            <section>
              <h2 className="text-lg font-semibold mb-3">1. Information We Collect</h2>
              <p className="text-muted-foreground">
                We collect information you provide directly to us, such as when you create an account, subscribe to our service, or contact us for support. This includes:
              </p>
              <ul className="mt-2 list-disc pl-5 text-muted-foreground space-y-1">
                <li>Name and email address</li>
                <li>Payment information (processed securely by Stripe)</li>
                <li>Usage data and interaction with our services</li>
                <li>Communications you send us</li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">2. How We Use Your Information</h2>
              <p className="text-muted-foreground">
                We use the information we collect to provide, maintain, and improve our services, process transactions, send you technical notices and support messages, and respond to your comments and questions.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">3. Data Sharing</h2>
              <p className="text-muted-foreground">
                We do not sell, trade, or rent your personal information to third parties. We may share information with trusted service providers who assist us in operating our website and conducting our business, subject to strict confidentiality agreements.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">4. Cookies</h2>
              <p className="text-muted-foreground">
                We use cookies and similar tracking technologies to maintain your session, remember your preferences, and analyze how our services are used. You can control cookies through your browser settings.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">5. Data Retention</h2>
              <p className="text-muted-foreground">
                We retain your personal information for as long as necessary to provide our services and fulfill the purposes outlined in this policy, unless a longer retention period is required by law.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">6. Security</h2>
              <p className="text-muted-foreground">
                We take reasonable measures to help protect information about you from loss, theft, misuse, unauthorized access, disclosure, alteration, and destruction. However, no security system is impenetrable.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">7. Your Rights</h2>
              <p className="text-muted-foreground">
                Depending on your location, you may have certain rights regarding your personal information, including the right to access, correct, or delete your data. Contact us to exercise these rights.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">8. Contact Us</h2>
              <p className="text-muted-foreground">
                If you have questions about this Privacy Policy, please contact us at privacy@{APP_NAME.toLowerCase()}.com.
              </p>
            </section>
          </div>
        </article>
      </main>
      <Footer />
    </div>
  );
}
