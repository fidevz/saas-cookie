import { Metadata } from "next";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";

export const metadata: Metadata = {
  title: "Cookie Policy",
};

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? "MyApp";

export default function CookiePolicyPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 pt-24 pb-16 px-4">
        <article className="mx-auto max-w-2xl">
          <div className="mb-10">
            <h1 className="text-3xl font-bold tracking-tight">Cookie Policy</h1>
            <p className="mt-2 text-sm text-muted-foreground">Last updated: January 2025</p>
            <p className="mt-4 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              <strong>Template notice:</strong> This is placeholder content. Replace with your actual Cookie Policy before going live.
            </p>
          </div>

          <div className="space-y-8 text-sm leading-relaxed">
            <section>
              <h2 className="text-lg font-semibold mb-3">1. Introduction</h2>
              <p className="text-muted-foreground">
                This Cookie Policy explains how {APP_NAME} (&quot;we&quot;, &quot;us&quot;, or &quot;[YOUR COMPANY NAME]&quot;) uses cookies and similar tracking technologies when you visit or use our service. By using our service, you agree to the use of cookies as described in this policy.
              </p>
              <p className="mt-3 text-muted-foreground">
                Cookies are small text files placed on your device by websites you visit. They are widely used to make websites work more efficiently and to provide information to site owners. Cookies can be &quot;session&quot; cookies (deleted when you close your browser) or &quot;persistent&quot; cookies (remaining on your device for a set period or until you delete them).
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">2. Types of Cookies We Use</h2>

              <div className="space-y-6">
                <div>
                  <h3 className="text-base font-medium mb-2">2.1 Essential Cookies</h3>
                  <p className="text-muted-foreground">
                    These cookies are strictly necessary for our service to function. Without them, core features like authentication and session management would not work. You cannot opt out of essential cookies.
                  </p>
                  <ul className="mt-3 list-disc pl-5 text-muted-foreground space-y-1">
                    <li>
                      <strong>Session cookie</strong> — Maintains your authenticated session. Set when you log in and cleared when you log out or your session expires.
                    </li>
                    <li>
                      <strong>CSRF token</strong> — Protects against cross-site request forgery attacks. Required for all state-changing requests.
                    </li>
                    <li>
                      <strong>Authentication refresh token</strong> — Stored as an HttpOnly cookie to securely refresh your access token without re-authentication. Not accessible via JavaScript.
                    </li>
                  </ul>
                </div>

                <div>
                  <h3 className="text-base font-medium mb-2">2.2 Analytics Cookies (Optional)</h3>
                  <p className="text-muted-foreground">
                    We may use analytics cookies to understand how visitors interact with our service. This helps us improve the user experience and identify issues. These cookies are optional and you can opt out at any time.
                  </p>
                  <ul className="mt-3 list-disc pl-5 text-muted-foreground space-y-1">
                    <li>
                      <strong>PostHog</strong> — Product analytics to track feature usage and user flows. Data is used exclusively to improve our product. PostHog can be configured to respect Do Not Track signals.
                    </li>
                    <li>
                      <strong>Google Analytics 4 (GA4)</strong> — Web analytics to understand traffic sources and user behavior. Data is anonymized where possible. You can opt out via Google&apos;s opt-out browser add-on.
                    </li>
                  </ul>
                  <p className="mt-3 text-muted-foreground">
                    If we use analytics, we will ask for your consent before setting analytics cookies where required by applicable law (e.g., in the EU/EEA under GDPR).
                  </p>
                </div>

                <div>
                  <h3 className="text-base font-medium mb-2">2.3 Payment Cookies</h3>
                  <p className="text-muted-foreground">
                    When you interact with our billing and subscription features, our payment processor sets cookies necessary for secure payment handling.
                  </p>
                  <ul className="mt-3 list-disc pl-5 text-muted-foreground space-y-1">
                    <li>
                      <strong>Stripe</strong> — Sets cookies to prevent fraud, remember your payment preferences, and ensure secure checkout sessions. These cookies are controlled by Stripe and subject to their privacy policy.
                    </li>
                  </ul>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">3. Third-Party Services</h2>
              <p className="text-muted-foreground">
                The following third-party services may set cookies or collect data when you use {APP_NAME}:
              </p>
              <ul className="mt-3 list-disc pl-5 text-muted-foreground space-y-2">
                <li>
                  <strong>Stripe</strong> — Payment processing. Their cookies support fraud prevention and checkout state.{" "}
                  <a
                    href="https://stripe.com/privacy"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline hover:text-foreground"
                  >
                    Stripe Privacy Policy
                  </a>
                </li>
                <li>
                  <strong>PostHog / Google Analytics 4</strong> — Product and web analytics. Used to understand usage patterns and improve the product. Data is not sold to third parties.
                </li>
                <li>
                  <strong>Sentry</strong> — Error tracking. Collects technical information about errors to help us fix bugs. Does not track user behavior for advertising.{" "}
                  <a
                    href="https://sentry.io/privacy/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline hover:text-foreground"
                  >
                    Sentry Privacy Policy
                  </a>
                </li>
              </ul>
              <p className="mt-3 text-muted-foreground">
                We do not use advertising cookies or sell your data to advertising networks.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">4. How to Control Cookies</h2>
              <p className="text-muted-foreground">
                You can control and manage cookies in several ways. Note that disabling cookies may impact your ability to use some features of our service.
              </p>
              <div className="mt-3 space-y-3 text-muted-foreground">
                <div>
                  <p className="font-medium text-foreground">Browser settings</p>
                  <p>
                    Most browsers allow you to view, delete, and block cookies. Find instructions for your browser:
                  </p>
                  <ul className="mt-2 list-disc pl-5 space-y-1">
                    <li>
                      <a href="https://support.google.com/chrome/answer/95647" target="_blank" rel="noopener noreferrer" className="underline hover:text-foreground">
                        Google Chrome
                      </a>
                    </li>
                    <li>
                      <a href="https://support.mozilla.org/en-US/kb/enable-and-disable-cookies-website-preferences" target="_blank" rel="noopener noreferrer" className="underline hover:text-foreground">
                        Mozilla Firefox
                      </a>
                    </li>
                    <li>
                      <a href="https://support.apple.com/guide/safari/manage-cookies-sfri11471/mac" target="_blank" rel="noopener noreferrer" className="underline hover:text-foreground">
                        Apple Safari
                      </a>
                    </li>
                    <li>
                      <a href="https://support.microsoft.com/en-us/microsoft-edge/delete-cookies-in-microsoft-edge-63947406-40ac-c3b8-57b9-2a946a29ae09" target="_blank" rel="noopener noreferrer" className="underline hover:text-foreground">
                        Microsoft Edge
                      </a>
                    </li>
                  </ul>
                </div>
                <div>
                  <p className="font-medium text-foreground">Opt-out tools</p>
                  <p>
                    For analytics cookies specifically, you can opt out using Google&apos;s{" "}
                    <a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener noreferrer" className="underline hover:text-foreground">
                      Analytics Opt-out Browser Add-on
                    </a>{" "}
                    or by enabling Do Not Track in your browser.
                  </p>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">5. Updates to This Policy</h2>
              <p className="text-muted-foreground">
                We may update this Cookie Policy from time to time to reflect changes in our practices or for legal, operational, or regulatory reasons. We will notify you of any material changes by updating the &quot;Last updated&quot; date at the top of this page. Your continued use of our service after such changes constitutes acceptance of the updated policy.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold mb-3">6. Contact</h2>
              <p className="text-muted-foreground">
                If you have questions or concerns about this Cookie Policy or our use of cookies, please contact us at{" "}
                <a
                  href="mailto:[YOUR EMAIL]"
                  className="underline hover:text-foreground"
                >
                  [YOUR EMAIL]
                </a>
                .
              </p>
            </section>
          </div>
        </article>
      </main>
      <Footer />
    </div>
  );
}
