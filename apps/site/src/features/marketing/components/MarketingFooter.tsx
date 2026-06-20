import Link from 'next/link'
import { BrandMark } from './BrandMark'
import { FOOTER_COLS, FOOTER_LEGAL } from '../data/site'

/**
 * Site footer. Five-column grid (brand + 4 link columns) + a legal row
 * at the bottom.
 */
export function MarketingFooter() {
  return (
    <footer className="border-t border-border">
      <div className="mx-auto grid max-w-[1280px] grid-cols-2 gap-8 px-7 pb-12 pt-16 sm:grid-cols-3 lg:grid-cols-[1.4fr_1fr_1fr_1fr_1fr]">
        <div className="col-span-2 sm:col-span-3 lg:col-span-1">
          <Link href="/" className="flex items-center gap-[9px]">
            <BrandMark className="h-[24px] w-[24px] text-primary" />
            <span className="text-[17px] font-semibold tracking-[-0.03em] text-foreground">
              RunMyCrew
            </span>
          </Link>
        </div>
        {FOOTER_COLS.map((col) => (
          <div key={col.title}>
            <div className="mb-4 text-[13.5px] font-semibold text-foreground/80">
              {col.title}
            </div>
            <div className="flex flex-col gap-[11px]">
              {col.items.map((item) => {
                const external = /^https?:\/\//.test(item.href)
                return (
                  <Link
                    key={item.label}
                    href={item.href}
                    {...(external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
                    className="text-[13.5px] text-muted-foreground transition-colors hover:text-foreground/80"
                  >
                    {item.label}
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </div>
      <div className="mx-auto flex max-w-[1280px] flex-wrap items-center gap-x-[22px] gap-y-2 border-t border-border px-7 pb-10 pt-6">
        <span className="text-[13px] text-muted-foreground/70">© 2026 RunMyCrew</span>
        {FOOTER_LEGAL.map((item) => (
          <Link
            key={item.label}
            href={item.href}
            className="text-[13px] text-muted-foreground transition-colors hover:text-foreground/80"
          >
            {item.label}
          </Link>
        ))}
      </div>
    </footer>
  )
}
