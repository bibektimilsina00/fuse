import type { Metadata } from 'next'
import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'

export const metadata: Metadata = {
  title: 'Terms of Service',
  description: 'The terms governing your use of RunMyCrew.',
}

const LAST_UPDATED = 'June 20, 2026'
const CONTACT_EMAIL = 'support@runmycrew.com'

export default function TermsPage() {
  return (
    <>
      <MarketingNav />
      <main>
        <section className="pb-12 pt-[120px] sm:pt-[170px]">
          <Container className="max-w-[760px] px-7">
            <p className="m-0 text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
              Legal
            </p>
            <h1 className="m-0 mt-3 text-[clamp(32px,4vw,48px)] font-[560] leading-[1.1] tracking-[-0.022em] text-foreground">
              Terms of Service
            </h1>
            <p className="mt-4 text-[14px] text-muted-foreground">Last updated: {LAST_UPDATED}</p>
          </Container>
        </section>

        <section className="pb-24">
          <Container className="max-w-[760px] px-7">
            <article className="prose prose-invert max-w-none text-[15px] leading-[1.7]">
              <p>
                These Terms of Service (&ldquo;Terms&rdquo;) govern your access to and
                use of the RunMyCrew automation platform at runmycrew.com (the
                &ldquo;Service&rdquo;). By creating an account or using the Service you
                agree to these Terms.
              </p>

              <h2>1. Account</h2>
              <p>
                You must be at least 16 years old to use the Service. You are
                responsible for keeping your credentials secure and for all activity
                under your account.
              </p>

              <h2>2. Acceptable use</h2>
              <p>You agree not to use the Service to:</p>
              <ul>
                <li>Violate any law, regulation, or third-party right.</li>
                <li>Send spam or unsolicited messages.</li>
                <li>Attempt to access workspaces or data you do not own.</li>
                <li>Reverse-engineer, scrape, or attack the Service.</li>
                <li>Run workflows that abuse connected third-party APIs (rate limits, ToS).</li>
              </ul>

              <h2>3. Your content</h2>
              <p>
                You own the workflows, data, and content you create in the Service.
                You grant us a limited license to host, process, and execute that
                content solely to provide the Service to you. We do not use your
                content to train models without your explicit opt-in.
              </p>

              <h2>4. Third-party services</h2>
              <p>
                The Service integrates with third-party APIs (Google, Meta, Slack,
                etc.). Your use of those APIs is subject to their respective terms.
                We are not responsible for outages, billing, or policy changes by
                third parties.
              </p>

              <h2>5. Beta features</h2>
              <p>
                Features marked &ldquo;beta&rdquo; are provided as-is, without SLA, and
                may change or be removed at any time.
              </p>

              <h2>6. Pricing &amp; refunds</h2>
              <p>
                Paid plans are billed monthly or annually in advance. Refunds are
                granted at our discretion within 14 days of a charge for unused
                portions.
              </p>

              <h2>7. Termination</h2>
              <p>
                You may cancel your account at any time from the product UI. We may
                suspend or terminate accounts that violate these Terms, with notice
                where reasonable. Upon termination we will delete your data within
                30 days, except where retention is required by law.
              </p>

              <h2>8. Warranty disclaimer</h2>
              <p>
                The Service is provided &ldquo;AS IS&rdquo; without warranties of any
                kind, express or implied, including merchantability, fitness for a
                particular purpose, and non-infringement. We do not guarantee that
                the Service will be uninterrupted or error-free.
              </p>

              <h2>9. Limitation of liability</h2>
              <p>
                To the maximum extent permitted by law, RunMyCrew shall not be liable
                for any indirect, incidental, special, or consequential damages, or
                for loss of profits, data, or business, arising out of or related to
                the Service. Aggregate liability is limited to the amount you paid us
                in the 12 months preceding the claim.
              </p>

              <h2>10. Changes</h2>
              <p>
                We may update these Terms. Material changes will be announced at
                least 30 days in advance. Continued use after the effective date
                constitutes acceptance.
              </p>

              <h2>11. Governing law</h2>
              <p>
                These Terms are governed by the laws of Nepal, without regard to
                conflict-of-law principles.
              </p>

              <h2>12. Contact</h2>
              <p>
                Questions: <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>.
              </p>
            </article>
          </Container>
        </section>
      </main>
      <MarketingFooter />
    </>
  )
}
