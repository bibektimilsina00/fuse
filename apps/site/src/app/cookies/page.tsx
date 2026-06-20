import type { Metadata } from 'next'
import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'

export const metadata: Metadata = {
  title: 'Cookie Policy',
  description:
    'What cookies and local-storage entries RunMyCrew uses, and how to control them.',
}

const LAST_UPDATED = 'June 20, 2026'
const PRIVACY_EMAIL = 'privacy@runmycrew.com'

export default function CookiesPage() {
  return (
    <>
      <MarketingNav />
      <main>
        <section className="pb-12 pt-[120px] sm:pt-[170px]">
          <Container className="max-w-[760px] px-7">
            <p className="m-0 text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
              Legal · Cookies
            </p>
            <h1 className="m-0 mt-3 text-[clamp(32px,4vw,48px)] font-[560] leading-[1.1] tracking-[-0.022em] text-foreground">
              Cookie Policy
            </h1>
            <p className="mt-4 text-[14px] text-muted-foreground">
              Last updated: {LAST_UPDATED}
            </p>
          </Container>
        </section>

        <section className="pb-24">
          <Container className="max-w-[760px] px-7">
            <article className="prose prose-invert max-w-none text-[15px] leading-[1.7]">
              <p>
                RunMyCrew uses a minimal set of first-party storage entries to
                operate the product. We do <strong>not</strong> use
                advertising cookies, third-party analytics that profile you, or
                any cross-site tracking pixels. This policy lists every entry,
                its purpose, its lifespan, and how to control it.
              </p>

              <h2 id="storage">First-party storage</h2>
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Purpose</th>
                    <th>Lifespan</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>
                      <code>runmycrew-auth-token</code>
                    </td>
                    <td>localStorage</td>
                    <td>
                      Authenticated session JWT. Required to use the product.
                    </td>
                    <td>Until logout / expiry</td>
                  </tr>
                  <tr>
                    <td>
                      <code>runmycrew-theme</code>
                    </td>
                    <td>localStorage</td>
                    <td>UI theme preference (light / dark / system).</td>
                    <td>Persistent</td>
                  </tr>
                  <tr>
                    <td>
                      <code>runmycrew-scheme</code>
                    </td>
                    <td>localStorage</td>
                    <td>Color-scheme palette preference.</td>
                    <td>Persistent</td>
                  </tr>
                  <tr>
                    <td>
                      <code>runmycrew-workspace-v2</code>
                    </td>
                    <td>localStorage</td>
                    <td>Last-active workspace id (so you land in the right place).</td>
                    <td>Persistent</td>
                  </tr>
                  <tr>
                    <td>
                      <code>runmycrew-editor-layout</code>
                    </td>
                    <td>localStorage</td>
                    <td>
                      Workflow editor panel sizes / collapsed state.
                    </td>
                    <td>Persistent</td>
                  </tr>
                  <tr>
                    <td>
                      <code>runmycrew-runs</code>
                    </td>
                    <td>localStorage</td>
                    <td>Recently viewed runs cache (rendering only).</td>
                    <td>Persistent</td>
                  </tr>
                </tbody>
              </table>

              <h2 id="third-party">Third-party</h2>
              <p>
                We do not embed third-party advertising tags. Where we use
                third-party services, they may set their own cookies:
              </p>
              <ul>
                <li>
                  <strong>Stripe</strong> — required for payment processing on
                  the billing page. Stripe&rsquo;s cookies are governed by{' '}
                  <a
                    href="https://stripe.com/privacy"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Stripe&rsquo;s Privacy Policy
                  </a>
                  .
                </li>
                <li>
                  <strong>Google Identity Services</strong> — only loaded when
                  you click &ldquo;Sign in with Google.&rdquo; Google may set
                  cookies on its own domain during the OAuth handshake; see{' '}
                  <a
                    href="https://policies.google.com/technologies/cookies"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Google&rsquo;s cookie policy
                  </a>
                  .
                </li>
                <li>
                  <strong>Cloudflare</strong> — DNS and TLS-edge service. May
                  set a <code>__cf_bm</code> cookie for bot mitigation; never
                  used for tracking.
                </li>
              </ul>

              <h2 id="control">How to control</h2>
              <ul>
                <li>
                  Clear browser data for <code>runmycrew.com</code> and{' '}
                  <code>app.runmycrew.com</code> at any time.
                </li>
                <li>
                  Sign out from <strong>Settings → Account</strong> to remove
                  the auth token.
                </li>
                <li>
                  Block third-party cookies entirely in your browser. Stripe
                  and Google sign-in may stop working as a side effect; the
                  rest of the Service is unaffected.
                </li>
              </ul>

              <h2 id="contact">Contact</h2>
              <p>
                Cookie-related questions:{' '}
                <a href={`mailto:${PRIVACY_EMAIL}`}>{PRIVACY_EMAIL}</a>
              </p>
            </article>
          </Container>
        </section>
      </main>
      <MarketingFooter />
    </>
  )
}
