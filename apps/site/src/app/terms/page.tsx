import type { Metadata } from 'next'
import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'

export const metadata: Metadata = {
  title: 'Terms of Service',
  description:
    'The terms governing your use of RunMyCrew. Acceptable use, payments, IP, liability, and termination.',
}

const LAST_UPDATED = 'June 20, 2026'
const EFFECTIVE_DATE = 'June 20, 2026'
const CONTACT_EMAIL = 'legal@runmycrew.com'

export default function TermsPage() {
  return (
    <>
      <MarketingNav />
      <main>
        <section className="pb-12 pt-[120px] sm:pt-[170px]">
          <Container className="max-w-[760px] px-7">
            <p className="m-0 text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
              Legal · Terms
            </p>
            <h1 className="m-0 mt-3 text-[clamp(32px,4vw,48px)] font-[560] leading-[1.1] tracking-[-0.022em] text-foreground">
              Terms of Service
            </h1>
            <p className="mt-4 text-[14px] text-muted-foreground">
              Last updated: {LAST_UPDATED} · Effective: {EFFECTIVE_DATE}
            </p>
          </Container>
        </section>

        <section className="pb-24">
          <Container className="max-w-[760px] px-7">
            <article className="prose prose-invert max-w-none text-[15px] leading-[1.7]">
              <p>
                These Terms of Service (&ldquo;Terms&rdquo;) govern your access
                to and use of the RunMyCrew automation platform at{' '}
                <a href="https://runmycrew.com">runmycrew.com</a> and{' '}
                <a href="https://app.runmycrew.com">app.runmycrew.com</a> and
                related APIs, integrations, documentation, and email
                notifications (collectively, the &ldquo;Service&rdquo;). The
                Service is operated by RunMyCrew (proprietor: Bibek Timilsina)
                (&ldquo;RunMyCrew,&rdquo; &ldquo;we,&rdquo; &ldquo;us&rdquo;).
              </p>
              <p>
                By creating an account or otherwise accessing the Service, you
                agree to be bound by these Terms and by our{' '}
                <a href="/privacy">Privacy Policy</a>. If you do not agree, do
                not use the Service.
              </p>

              <h2 id="account">1. Account</h2>
              <p>
                You must be at least 16 years old to use the Service. If you
                create an account on behalf of an organization, you represent
                that you are authorized to bind that organization. You are
                responsible for keeping credentials secure and for all activity
                under your account. Notify us immediately at{' '}
                <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a> on
                suspected compromise.
              </p>

              <h2 id="acceptable-use">2. Acceptable use</h2>
              <p>You agree not to use the Service to:</p>
              <ul>
                <li>Violate any law, regulation, or third-party right.</li>
                <li>
                  Send unsolicited bulk messages (spam) via Gmail, Slack,
                  Discord, WhatsApp, SMS, or any other integration.
                </li>
                <li>
                  Attempt to access workspaces, runs, credentials, or data you
                  do not own or have not been invited to.
                </li>
                <li>Reverse-engineer, scrape, fuzz, or attack the Service.</li>
                <li>
                  Run workflows that abuse a connected third-party API
                  (rate-limit evasion, ToS violation, scraping at scale).
                </li>
                <li>
                  Build a competing service by exfiltrating internal APIs or
                  proprietary content.
                </li>
                <li>
                  Use the Service to generate or disseminate content that is
                  unlawful, hateful, defamatory, or sexually exploitative of
                  minors.
                </li>
              </ul>
              <p>
                We may suspend or terminate accounts that violate this section
                with or without notice, at our discretion.
              </p>

              <h2 id="content">3. Your content</h2>
              <p>
                You retain ownership of the workflows, prompts, files, and
                content you create on the Service (&ldquo;Customer
                Content&rdquo;). You grant RunMyCrew a worldwide, non-exclusive,
                royalty-free license to host, process, store, transmit, modify
                in trivial ways (compression, format conversion), display, and
                execute Customer Content solely to provide the Service to you,
                comply with your instructions, and meet legal obligations.
                The license terminates when you delete the content or your
                account, subject to our backup-rotation schedule (see the{' '}
                <a href="/privacy#retention">Privacy Policy</a>).
              </p>
              <p>
                <strong>No training without opt-in.</strong> We do not use
                Customer Content, prompts, run outputs, or third-party data
                received via your connected accounts to train any AI/ML model
                without your separate, affirmative opt-in.
              </p>

              <h2 id="third-party">4. Third-party services</h2>
              <p>
                The Service integrates with third-party APIs (Google, Meta,
                Slack, GitHub, Notion, Stripe, OpenAI, Anthropic, and others).
                Your use of those APIs is governed by the respective
                third-party terms. We are not responsible for outages, billing,
                policy changes, or content moderation decisions made by those
                third parties.
              </p>
              <p>
                You are responsible for keeping connected-account permissions
                current and for revoking access if you stop using the Service
                (via the third-party&rsquo;s connections / business-integration
                settings).
              </p>

              <h2 id="beta">5. Beta &amp; preview features</h2>
              <p>
                Features marked &ldquo;beta,&rdquo; &ldquo;preview,&rdquo; or
                &ldquo;early access&rdquo; are provided as-is, without SLA, and
                may be modified, throttled, or removed at any time. We may
                publish telemetry from beta features at an aggregated and
                anonymized level for product improvement.
              </p>

              <h2 id="pricing">6. Pricing, billing &amp; refunds</h2>
              <ul>
                <li>
                  Paid plans are billed monthly or annually in advance through
                  Stripe. Taxes are added where required.
                </li>
                <li>
                  Plan limits (runs per month, seats, retention) are documented
                  on the <a href="/pricing">pricing page</a>. Overages may
                  result in throttling or upgrade prompts.
                </li>
                <li>
                  Refunds are granted at our discretion within 14 days of a
                  charge for unused portions; legally mandated refunds (EU
                  consumer rules, etc.) always apply.
                </li>
                <li>
                  You can downgrade or cancel at any time from the billing
                  panel. Downgrades take effect at the end of the current billing
                  period.
                </li>
              </ul>

              <h2 id="termination">7. Suspension &amp; termination</h2>
              <p>
                You may delete your account at any time from{' '}
                <strong>Settings → Account → Delete account</strong>. We may
                suspend or terminate accounts that (a) violate these Terms,
                (b) materially endanger the Service or other users, or
                (c) are inactive for 24 months. Where reasonable, we provide
                advance notice and an opportunity to cure.
              </p>
              <p>
                On termination we delete your data within 30 days, except where
                retention is required by law (e.g. invoices for tax records).
                See the <a href="/data-deletion">Data Deletion</a> page for
                detail.
              </p>

              <h2 id="warranty">8. Warranty disclaimer</h2>
              <p>
                The Service is provided &ldquo;AS IS&rdquo; and &ldquo;AS
                AVAILABLE,&rdquo; without warranties of any kind, express or
                implied, including merchantability, fitness for a particular
                purpose, title, and non-infringement. We do not warrant that
                the Service will be uninterrupted, error-free, or secure
                against every possible threat. You bear the risk of using AI
                generation features for any high-stakes use case and should
                independently review every output before acting on it.
              </p>

              <h2 id="liability">9. Limitation of liability</h2>
              <p>
                To the maximum extent permitted by law, RunMyCrew and its
                personnel shall not be liable for any indirect, incidental,
                special, consequential, exemplary, or punitive damages, or for
                loss of profits, revenue, data, or business opportunity, arising
                out of or related to the Service, even if advised of the
                possibility of such damages. Our aggregate liability for any
                claim arising out of or relating to the Service is limited to
                the amount you paid us in the 12 months preceding the event
                giving rise to the claim, or USD $100, whichever is greater.
              </p>
              <p>
                Some jurisdictions do not allow limitations of implied
                warranties or exclusion of consequential damages; in those
                jurisdictions the above limitations apply only to the maximum
                extent permitted by law.
              </p>

              <h2 id="indemnification">10. Indemnification</h2>
              <p>
                You agree to indemnify and hold RunMyCrew harmless from any
                claim, damage, or expense (including reasonable attorneys&rsquo;
                fees) arising from your Customer Content, your use of the
                Service in breach of these Terms, or your violation of any law
                or third-party right.
              </p>

              <h2 id="ip">11. Intellectual property</h2>
              <p>
                The Service, including all software, design, documentation,
                trademarks, and the &ldquo;RunMyCrew&rdquo; / &ldquo;Crew
                AI&rdquo; names and logos, is owned by RunMyCrew and protected
                by copyright, trademark, and other laws. Open-source components
                are governed by their respective licenses (see{' '}
                <a
                  href="https://github.com/bibektimilsina00/runmycrew"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  the repository
                </a>
                ). You receive only the licenses expressly granted here.
              </p>

              <h2 id="changes">12. Changes to the Service or Terms</h2>
              <p>
                We may update these Terms. Material changes will be announced
                at least 30 days in advance via the product UI and email.
                Continued use after the effective date constitutes acceptance.
                Material changes to the Service&rsquo;s feature set are
                communicated through the <a href="/changelog">changelog</a>.
              </p>

              <h2 id="law">13. Governing law &amp; disputes</h2>
              <p>
                These Terms are governed by the laws of Nepal, without regard
                to conflict-of-law principles. Any dispute will be resolved
                first by good-faith negotiation, then by binding arbitration in
                Kathmandu, Nepal, except that either party may seek injunctive
                relief in any court of competent jurisdiction to protect its
                intellectual property. Consumers in the EU, UK, and other
                jurisdictions with mandatory consumer-protection rules retain
                the protections of their local law.
              </p>

              <h2 id="entire">14. Entire agreement &amp; severability</h2>
              <p>
                These Terms, together with the Privacy Policy, Cookie Policy,
                and any plan-specific addendums, constitute the entire
                agreement between you and RunMyCrew with respect to the
                Service. If any provision is held unenforceable, the remaining
                provisions remain in full force.
              </p>

              <h2 id="contact">15. Contact</h2>
              <p>
                Legal notices: <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
                <br />
                Postal: address available on request to{' '}
                <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>.
              </p>
            </article>
          </Container>
        </section>
      </main>
      <MarketingFooter />
    </>
  )
}
