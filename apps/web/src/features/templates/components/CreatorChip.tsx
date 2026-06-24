import type { TemplateCreator } from '../types/templatesTypes'

/**
 * Tiny creator attribution chip — avatar tile (initial) + first name.
 * Used inside `TemplateCard` bottom meta strip without disturbing the
 * existing layout, and on the detail page as a larger profile card.
 */

interface CreatorChipProps {
  creator: TemplateCreator | null
  variant?: 'card' | 'detail'
}

export function CreatorChip({ creator, variant = 'card' }: CreatorChipProps) {
  if (!creator) return null

  const displayName =
    creator.full_name?.trim() ||
    creator.email?.split('@')[0] ||
    'Anonymous'
  const initial = displayName.charAt(0).toUpperCase()

  if (variant === 'detail') {
    return (
      <div className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-[8px] bg-[var(--accent)] text-[12px] font-semibold text-white">
          {creator.avatar_url ? (
            <img
              src={creator.avatar_url}
              alt={displayName}
              className="h-full w-full rounded-[8px] object-cover"
            />
          ) : (
            initial
          )}
        </div>
        <div className="flex flex-col">
          <span className="text-[12.5px] font-semibold text-[var(--text)]">
            {displayName}
          </span>
          <span className="text-[10.5px] text-[var(--text-faint)]">Creator</span>
        </div>
      </div>
    )
  }

  return (
    <span className="flex items-center gap-1.5 text-[10px] font-mono text-[var(--text-faint)] tracking-[0.06em] uppercase">
      <span className="flex h-[14px] w-[14px] items-center justify-center rounded-[3px] bg-[var(--accent)] text-[8px] font-bold text-white">
        {creator.avatar_url ? (
          <img
            src={creator.avatar_url}
            alt={displayName}
            className="h-full w-full rounded-[3px] object-cover"
          />
        ) : (
          initial
        )}
      </span>
      <span className="truncate max-w-[100px]">{displayName}</span>
    </span>
  )
}
