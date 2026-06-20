import type { Metadata } from 'next'
import Link from 'next/link'
import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'

export const metadata: Metadata = {
  title: 'About',
  description:
    'Why RunMyCrew exists: a single platform where teams and AI agents share the same workflows.',
}

export default function AboutPage() {
  return (
    <>
      <MarketingNav />
      <main>
        <section className="pb-12 pt-[120px] sm:pt-[170px]">
          <Container className="max-w-[760px] px-7">
            <p className="m-0 text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
              Company · About
            </p>
            <h1 className="m-0 mt-3 text-[clamp(32px,4vw,48px)] font-[560] leading-[1.1] tracking-[-0.022em] text-foreground">
              About RunMyCrew
            </h1>
            <p className="mt-4 text-[15px] text-muted-foreground">
              The automation system for teams and the AI agents working
              alongside them.
            </p>
          </Container>
        </section>

        <section className="pb-24">
          <Container className="max-w-[760px] px-7">
            <article className="prose prose-invert max-w-none text-[15px] leading-[1.7]">
              <h2>What we&rsquo;re building</h2>
              <p>
                Most companies have integration sprawl — a workflow runs in
                Zapier, a script runs on Cron, an AI agent runs in some
                separate framework, and none of them know about each other.
                When something breaks, finding which surface owns the failure
                takes longer than fixing it.
              </p>
              <p>
                RunMyCrew is a single platform where workflows, integrations,
                runs, and AI agents live in one graph, one logging pane, one
                permission model. Whether the run was triggered by a Gmail
                event, a webhook, a schedule, or a Crew AI agent, you see
                exactly what happened at every step and you can replay or
                edit it from the same editor.
              </p>

              <h2>Principles</h2>
              <ul>
                <li>
                  <strong>Open-source by default.</strong> The product is{' '}
                  <a
                    href="https://github.com/bibektimilsina00/runmycrew"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    available on GitHub
                  </a>{' '}
                  and ships as a single Docker Compose stack you can
                  self-host. Hosted RunMyCrew is the same code with our
                  operational hardening.
                </li>
                <li>
                  <strong>Action over abstraction.</strong> The fastest path
                  to running automation should not require learning a DSL,
                  building a CI pipeline, or hiring an integration consultant.
                </li>
                <li>
                  <strong>You own your data.</strong> No training on your
                  prompts or content without opt-in, no advertising tracking,
                  no sharing with brokers. Documented in the{' '}
                  <Link href="/privacy">Privacy Policy</Link>.
                </li>
                <li>
                  <strong>Production reality.</strong> Every workflow is
                  observable end-to-end — payloads, retries, durations — so
                  on-call engineers can debug the same way they would a
                  microservice.
                </li>
                <li>
                  <strong>Honest pricing.</strong> Self-host is free forever;
                  the hosted plan charges only for runs and seats. No
                  per-integration tax, no &ldquo;upgrade for SSO&rdquo;
                  surprise on the enterprise tier.
                </li>
              </ul>

              <h2>Who&rsquo;s behind it</h2>
              <p>
                RunMyCrew is founded by Bibek Timilsina, a software engineer
                based in Kathmandu, Nepal. The product evolved from years of
                hand-rolling integration glue for product teams and watching
                that glue rot. The platform is currently developed in the open;
                contributors are welcome.
              </p>

              <h2>How to reach us</h2>
              <p>
                See <Link href="/contact">the contact page</Link> for the
                right inbox by topic. For everything else, GitHub Issues is
                the public bug tracker:{' '}
                <a
                  href="https://github.com/bibektimilsina00/runmycrew/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  github.com/bibektimilsina00/runmycrew/issues
                </a>
                .
              </p>
            </article>
          </Container>
        </section>
      </main>
      <MarketingFooter />
    </>
  )
}
