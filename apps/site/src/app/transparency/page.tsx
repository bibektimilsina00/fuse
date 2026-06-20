import type { Metadata } from 'next'
import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'

export const metadata: Metadata = {
  title: 'Transparency',
  description:
    'The subprocessors RunMyCrew relies on, the data they process, where they process it, and our data-retention schedule.',
}

const PRIVACY_EMAIL = 'privacy@runmycrew.com'

type Subprocessor = {
  name: string
  service: string
  data: string
  region: string
  dpa: string
}

const SUBPROCESSORS: Subprocessor[] = [
  {
    name: 'DigitalOcean',
    service: 'VPS hosting + block storage',
    data: 'All product data (in-memory + at-rest disk).',
    region: 'EU (Frankfurt)',
    dpa: 'https://www.digitalocean.com/legal/data-processing-agreement',
  },
  {
    name: 'Cloudflare',
    service: 'DNS + TLS edge + bot mitigation',
    data: 'IP address, request metadata. No request body inspection.',
    region: 'Global edge',
    dpa: 'https://www.cloudflare.com/cloudflare-customer-dpa/',
  },
  {
    name: 'GitHub',
    service: 'Source code repository + container registry (GHCR)',
    data: 'Source code + built container images. No customer data.',
    region: 'US',
    dpa: 'https://docs.github.com/en/site-policy/privacy-policies/global-privacy-practices',
  },
  {
    name: 'Stripe',
    service: 'Payment processing',
    data: 'Email, name, card details (held by Stripe — never on our servers).',
    region: 'US / EU',
    dpa: 'https://stripe.com/legal/dpa',
  },
  {
    name: 'Google (LLC)',
    service:
      'Optional: Google Sign-In OIDC, Gemini LLM (Crew AI), connected-account APIs',
    data: 'OpenID profile fields; LLM prompts only when Crew AI uses Gemini; user data only via connectors you authorized.',
    region: 'US / EU',
    dpa: 'https://cloud.google.com/terms/data-processing-addendum',
  },
  {
    name: 'Anthropic',
    service: 'Optional: Claude LLM (Crew AI)',
    data:
      'LLM prompts only when Crew AI uses Claude. Anthropic does not train on API inputs by default.',
    region: 'US',
    dpa: 'https://www.anthropic.com/legal/dpa',
  },
  {
    name: 'OpenAI',
    service: 'Optional: GPT LLM (Crew AI)',
    data: 'LLM prompts only when Crew AI uses GPT. API inputs are not used for training.',
    region: 'US',
    dpa: 'https://openai.com/policies/data-processing-addendum',
  },
  {
    name: 'Meta Platforms',
    service: 'Optional: Meta API (Facebook / Instagram / WhatsApp / Ads)',
    data: 'Only data your workflows explicitly read or write.',
    region: 'US / EU',
    dpa: 'https://developers.facebook.com/terms/dpa/',
  },
  {
    name: 'Sentry / GlitchTip (optional)',
    service: 'Error tracking',
    data: 'Stack traces, request paths, sanitized error context. No request bodies.',
    region: 'EU (self-hosted on same VPS when GLITCHTIP_DSN unset)',
    dpa: 'https://sentry.io/legal/dpa/',
  },
]

export default function TransparencyPage() {
  return (
    <>
      <MarketingNav />
      <main>
        <section className="pb-12 pt-[120px] sm:pt-[170px]">
          <Container className="max-w-[860px] px-7">
            <p className="m-0 text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
              Trust · Transparency
            </p>
            <h1 className="m-0 mt-3 text-[clamp(32px,4vw,48px)] font-[560] leading-[1.1] tracking-[-0.022em] text-foreground">
              Transparency
            </h1>
            <p className="mt-4 text-[15px] text-muted-foreground">
              Subprocessors, regional data flow, and our retention schedule —
              audited and updated as our infrastructure changes.
            </p>
          </Container>
        </section>

        <section className="pb-24">
          <Container className="max-w-[860px] px-7">
            <article className="prose prose-invert max-w-none text-[15px] leading-[1.7]">
              <h2 id="subprocessors">Subprocessors</h2>
              <p>
                A subprocessor is a third-party vendor that may process
                customer data on RunMyCrew&rsquo;s behalf. We use the minimum
                viable set. Each has a Data Processing Agreement in place.
              </p>
              <table>
                <thead>
                  <tr>
                    <th>Vendor</th>
                    <th>Service</th>
                    <th>Data processed</th>
                    <th>Region</th>
                    <th>DPA</th>
                  </tr>
                </thead>
                <tbody>
                  {SUBPROCESSORS.map((s) => (
                    <tr key={s.name}>
                      <td>{s.name}</td>
                      <td>{s.service}</td>
                      <td>{s.data}</td>
                      <td>{s.region}</td>
                      <td>
                        <a
                          href={s.dpa}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          link
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p>
                When we add or change a subprocessor we publish the change here
                at least 30 days in advance. Object via{' '}
                <a href={`mailto:${PRIVACY_EMAIL}`}>{PRIVACY_EMAIL}</a>.
              </p>

              <h2 id="retention">Data retention schedule</h2>
              <table>
                <thead>
                  <tr>
                    <th>Data class</th>
                    <th>Retention</th>
                    <th>After retention</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Account profile</td>
                    <td>While account is active</td>
                    <td>Deleted within 30 days of account deletion</td>
                  </tr>
                  <tr>
                    <td>Workflow definitions, knowledge bases</td>
                    <td>While account is active</td>
                    <td>Deleted on user action / account deletion</td>
                  </tr>
                  <tr>
                    <td>Run history (free)</td>
                    <td>7 days</td>
                    <td>Hard-deleted</td>
                  </tr>
                  <tr>
                    <td>Run history (pro)</td>
                    <td>30 days</td>
                    <td>Hard-deleted</td>
                  </tr>
                  <tr>
                    <td>Run history (enterprise)</td>
                    <td>Configurable, up to 1 year</td>
                    <td>Hard-deleted</td>
                  </tr>
                  <tr>
                    <td>OAuth tokens, API keys</td>
                    <td>Until disconnected by user</td>
                    <td>Encryption key destroyed</td>
                  </tr>
                  <tr>
                    <td>Operational logs (IP, UA, request path)</td>
                    <td>30 days</td>
                    <td>Rolled off automatically</td>
                  </tr>
                  <tr>
                    <td>Encrypted database backups</td>
                    <td>14 days rolling</td>
                    <td>Overwritten</td>
                  </tr>
                  <tr>
                    <td>Invoices (tax compliance)</td>
                    <td>Up to 10 years per jurisdiction</td>
                    <td>Retained for legal obligation only</td>
                  </tr>
                  <tr>
                    <td>Support correspondence</td>
                    <td>24 months</td>
                    <td>Deleted</td>
                  </tr>
                </tbody>
              </table>

              <h2 id="regions">Where data is processed</h2>
              <p>
                The primary production region is the European Union
                (Frankfurt). LLM API calls reach the provider&rsquo;s nearest
                region (typically US). Meta and Google API calls follow the
                connected account&rsquo;s home region.
              </p>

              <h2 id="incidents">Disclosed incidents</h2>
              <p>
                None to date. Any future incident that meaningfully affects
                customer data will be disclosed here and notified to affected
                users by email within 72 hours of discovery, as required by
                GDPR Art. 33.
              </p>

              <h2 id="reports">Government &amp; law-enforcement requests</h2>
              <p>
                None to date. If we receive a request that requires us to hand
                over customer data, we will notify the affected customer
                immediately unless legally prohibited.
              </p>

              <h2 id="contact">Contact</h2>
              <p>
                Privacy / DPA / subprocessor questions:{' '}
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
