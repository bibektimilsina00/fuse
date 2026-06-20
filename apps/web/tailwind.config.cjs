/** @type {import('tailwindcss').Config} */
const v = (variable) => `var(${variable})`

module.exports = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // ── Fuse design tokens ────────────────────────────────────────────
        bg:    v('--bg'),
        bg2:   v('--bg-2'),
        surface: { DEFAULT: v('--surface'), 2: v('--surface-2'), 3: v('--surface-3') },
        border:  { DEFAULT: v('--border'), soft: v('--border-soft'), faint: v('--border-faint') },
        text:    { DEFAULT: v('--text'), mute: v('--text-mute'), faint: v('--text-faint'), dim: v('--text-dim') },
        accent:  { DEFAULT: v('--accent'), soft: v('--accent-soft'), line: v('--accent-line') },
        ok:   v('--ok'),
        warn: v('--warn'),
        err:  v('--err'),

        // ── shadcn/ui token aliases (maps to Fuse vars via CSS) ───────────
        background:  v('--background'),
        foreground:  v('--foreground'),
        card: {
          DEFAULT:    v('--card'),
          foreground: v('--card-foreground'),
        },
        popover: {
          DEFAULT:    v('--popover'),
          foreground: v('--popover-foreground'),
        },
        primary: {
          DEFAULT:    v('--primary'),
          foreground: v('--primary-foreground'),
        },
        secondary: {
          DEFAULT:    v('--secondary'),
          foreground: v('--secondary-foreground'),
        },
        muted: {
          DEFAULT:    v('--muted'),
          foreground: v('--muted-foreground'),
        },
        destructive: {
          DEFAULT:    v('--destructive'),
          foreground: v('--destructive-foreground'),
        },
        input:  v('--input'),
        ring:   v('--ring'),
      },

      fontFamily: {
        ui:   ['Inter Tight', 'Geist', 'Helvetica Neue', 'system-ui', 'sans-serif'],
        mono: ['Geist Mono', 'ui-monospace', 'SF Mono', 'Menlo', 'monospace'],
      },

      // ── Consolidated font scale — 5 sizes only ───────────────────────────
      fontSize: {
        xs:   ['11px', { lineHeight: '1.45' }],   // caption, mono labels
        sm:   ['13px', { lineHeight: '1.5'  }],   // body, UI default
        base: ['14px', { lineHeight: '1.5'  }],   // comfortable reading
        lg:   ['15px', { lineHeight: '1.4'  }],   // heading-sm
        xl:   ['18px', { lineHeight: '1.3'  }],   // sub-heading
        '2xl':['22px', { lineHeight: '1.2'  }],   // heading
        '3xl':['28px', { lineHeight: '1.15' }],   // display
      },

      letterSpacing: {
        tight:  '-0.02em',
        normal: '-0.005em',
        wide:   '0.04em',
        wider:  '0.08em',
        widest: '0.10em',
      },

      borderRadius: {
        sm:   v('--r-sm'),
        md:   v('--r-md'),
        lg:   v('--r-lg'),
        xl:   '20px',
        full: '9999px',
      },

      // ── 4px spacing scale ────────────────────────────────────────────────
      spacing: {
        px: '1px', 0: '0px',
        0.5: '2px',  1: '4px',   1.5: '6px',  2: '8px',
        2.5: '10px', 3: '12px',  3.5: '14px', 4: '16px',
        4.5: '18px', 5: '20px',  5.5: '22px', 6: '24px',
        7:   '28px', 8: '32px',  9:   '36px', 10: '40px',
        11:  '44px', 12: '48px', 14:  '56px', 16: '64px',
        20:  '80px', 24: '96px',
        sidebar: '244px',
      },

      // ── Elevation shadows (theme-aware via CSS vars) ─────────────────────
      boxShadow: {
        float:    'var(--shadow-float)',
        panel:    'var(--shadow-panel)',
        modal:    'var(--shadow-modal)',
        dropdown: 'var(--shadow-dropdown)',
      },

      transitionDuration: { fast: '100ms', base: '150ms', slow: '200ms' },
      transitionTimingFunction: {
        ui:     'cubic-bezier(0.25, 0.1, 0.25, 1)',
        spring: 'cubic-bezier(0.16, 1, 0.3, 1)',
      },

      keyframes: {
        'fade-in':   { from: { opacity: '0' }, to: { opacity: '1' } },
        'slide-up':  { from: { opacity: '0', transform: 'translateY(6px) scale(0.98)' }, to: { opacity: '1', transform: 'translateY(0) scale(1)' } },
        'toast-in':  { from: { opacity: '0', transform: 'translateY(12px) scale(0.96)' }, to: { opacity: '1', transform: 'translateY(0) scale(1)' } },
        'toast-out': { from: { opacity: '1', transform: 'translateY(0) scale(1)' }, to: { opacity: '0', transform: 'translateY(8px) scale(0.96)' } },
        // shadcn/ui animation keyframes
        'accordion-down': { from: { height: '0' }, to: { height: 'var(--radix-accordion-content-height)' } },
        'accordion-up':   { from: { height: 'var(--radix-accordion-content-height)' }, to: { height: '0' } },
      },

      animation: {
        'fade-in':         'fade-in 150ms ease-out',
        'slide-up':        'slide-up 200ms cubic-bezier(0.16, 1, 0.3, 1)',
        'toast-in':        'toast-in 220ms cubic-bezier(0.16, 1, 0.3, 1)',
        'toast-out':       'toast-out 180ms ease-in forwards',
        'accordion-down':  'accordion-down 200ms ease-out',
        'accordion-up':    'accordion-up 200ms ease-out',
      },
    },
  },
  plugins: [
    require('tailwindcss-animate'),
  ],
}

