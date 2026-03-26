import { Metadata } from "next";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";

export const metadata: Metadata = {
  title: "Terms of Service",
};

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? "MyApp";

export default function TermsOfServicePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 pt-24 pb-16 px-4">
        <article className="mx-auto max-w-2xl">
          <div className="mb-10">
            <h1 className="text-3xl font-bold tracking-tight">Terms of Service</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Last updated: January 2025
            </p>
            <p className="mt-4 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              <strong>Template notice:</strong> This is placeholder content. Replace with your actual Terms of Service before going live.
            </p>
          </div>

          <div className="prose prose-slate max-w-none space-y-8 text-sm leading-relaxed">
            <section>
              <h2 className="text-lg font-semibold mb-3">1. Acceptance of Terms</h2>
              <p className="text-muted-foreground">
                By accessing and using {APP_NAME} (&quot;the Service&quot;), you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by these terms, please do not use the Service.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">2. Description of Service</h2>
              <p className="text-muted-foreground">
                {APP_NAME} provides [describe your service here]. The Service is provided &quot;as is&quot; and we reserve the right to modify or discontinue it at any time with or without notice.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">3. User Accounts</h2>
              <p className="text-muted-foreground">
                You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account. You agree to notify us immediately of any unauthorized use of your account.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">4. Payment and Billing</h2>
              <p className="text-muted-foreground">
                Subscription fees are billed in advance on a monthly or annual basis. All fees are non-refundable except as required by law. We reserve the right to change pricing with 30 days notice.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">5. Privacy</h2>
              <p className="text-muted-foreground">
                Your use of the Service is also governed by our Privacy Policy, which is incorporated into these Terms by reference.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">6. Intellectual Property</h2>
              <p className="text-muted-foreground">
                The Service and its original content, features, and functionality are owned by {APP_NAME} and are protected by applicable intellectual property laws.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">7. Termination</h2>
              <p className="text-muted-foreground">
                We reserve the right to terminate or suspend your account at our discretion, without notice, for conduct that we believe violates these Terms or is harmful to other users, us, or third parties.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">8. Limitation of Liability</h2>
              <p className="text-muted-foreground">
                To the maximum extent permitted by law, {APP_NAME} shall not be liable for any indirect, incidental, special, consequential, or punitive damages resulting from your use of the Service.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">9. Contact</h2>
              <p className="text-muted-foreground">
                If you have any questions about these Terms, please contact us at legal@{APP_NAME.toLowerCase()}.com.
              </p>
            </section>
          </div>
        </article>
      </main>
      <Footer />
    </div>
  );
}
