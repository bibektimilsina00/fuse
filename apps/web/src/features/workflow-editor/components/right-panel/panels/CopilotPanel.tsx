import { useEffect, useState } from 'react'
import {
  Send, Zap, Check, X, Plus, History,
  Copy, RotateCcw, Square, ArrowDown,
} from 'lucide-react'
import { cn } from '@/lib/cn'
import { Dropdown, DropdownTrigger, DropdownContent } from '@/shared/components'
import { useCopilotChat } from '../../../hooks/useCopilotChat'
import { useCopilotDiffStore } from '../../../stores/copilotDiffStore'
import { CopilotMessage } from './copilot/CopilotMessage'
import { CopilotEmptyState } from './copilot/CopilotEmptyState'
import { CopilotToolChips } from './copilot/CopilotToolChips'

function DiffBanner() {
  const { active, summary, accept, reject } = useCopilotDiffStore()
  if (!active || !summary) return null
  const parts = [
    summary.added.length ? `+${summary.added.length} new` : '',
    summary.edited.length ? `~${summary.edited.length} edited` : '',
    summary.deleted.length ? `-${summary.deleted.length} removed` : '',
  ].filter(Boolean)
  return (
    <div className="mx-3 mb-2 flex items-center gap-2 rounded-[10px] border border-[var(--accent-line)] bg-[var(--accent-line)]/10 px-3 py-2">
      <span className="flex-1 text-[12px] text-[var(--text)]">
        Copilot proposed changes — {parts.join(', ')}
      </span>
      <button
        onClick={reject}
        className="flex items-center gap-1 rounded-[6px] px-2 py-1 text-[11.5px] text-[var(--text-mute)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
      >
        <X className="h-3 w-3" /> Reject
      </button>
      <button
        onClick={accept}
        className="flex items-center gap-1 rounded-[6px] bg-[var(--text)] px-2 py-1 text-[11.5px] text-[var(--bg)] transition-colors hover:opacity-90"
      >
        <Check className="h-3 w-3" /> Accept
      </button>
    </div>
  )
}

function TypingDots() {
  return (
    <span className="flex items-center gap-1 py-0.5">
      {[0, 1, 2].map(i => (
        <span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-[var(--text-faint)]"
          style={{ animation: `copilot-bounce 1.2s infinite ease-in-out ${i * 0.15}s` }}
        />
      ))}
    </span>
  )
}

function StreamingCursor() {
  return (
    <span
      aria-hidden
      className="ml-[1px] inline-block h-[14px] w-[6px] translate-y-[2px] rounded-[1px] bg-[var(--text-mute)] align-middle"
      style={{ animation: 'copilot-cursor 0.9s steps(2) infinite' }}
    />
  )
}

interface MessageActionsProps {
  onCopy: () => void
  onRetry?: () => void
}

function MessageActions({ onCopy, onRetry }: MessageActionsProps) {
  return (
    <div className="mt-1 flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
      <button
        onClick={onCopy}
        title="Copy"
        className="flex items-center gap-1 rounded-[5px] px-1.5 py-0.5 text-[10.5px] text-[var(--text-faint)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
      >
        <Copy className="h-3 w-3" /> Copy
      </button>
      {onRetry && (
        <button
          onClick={onRetry}
          title="Retry from this prompt"
          className="flex items-center gap-1 rounded-[5px] px-1.5 py-0.5 text-[10.5px] text-[var(--text-faint)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
        >
          <RotateCcw className="h-3 w-3" /> Retry
        </button>
      )}
    </div>
  )
}

export function CopilotPanel() {
  const {
    msgs, input, setInput, busy, error,
    slashOpen, slashIdx, setSlashIdx, slashFilter,
    streamRef, inputRef,
    quickActions, send, cancel, retryFromAssistant,
    onKeyDown, selectSlashCommand,
    sessions, sessionId, newChat, loadSession, deleteSession,
  } = useCopilotChat()

  const [stickToBottom, setStickToBottom] = useState(true)

  // Track whether the user has scrolled the stream away from the bottom.
  // When they're pinned, new tokens auto-scroll; when they scroll up,
  // show a Jump-to-latest pill instead of fighting the scroll position.
  useEffect(() => {
    const el = streamRef.current
    if (!el) return
    const onScroll = () => {
      const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 24
      setStickToBottom(atBottom)
    }
    el.addEventListener('scroll', onScroll, { passive: true })
    return () => el.removeEventListener('scroll', onScroll)
  }, [streamRef])

  const jumpToBottom = () => {
    const el = streamRef.current
    if (!el) return
    el.scrollTop = el.scrollHeight
    setStickToBottom(true)
  }

  const lastIdx = msgs.length - 1
  const lastAssistantIsLive =
    busy && msgs[lastIdx]?.role === 'assistant'

  return (
    <>
      <style>{`
        @keyframes copilot-bounce {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40%            { transform: scale(1);   opacity: 1;   }
        }
        @keyframes copilot-cursor {
          0%, 100% { opacity: 1; }
          50%      { opacity: 0; }
        }
      `}</style>

      <div className="flex h-full flex-col overflow-hidden">
        {/* Header — new chat, history, provider */}
        <div className="flex shrink-0 items-center gap-1.5 border-b border-[var(--border-faint)] px-3 py-2">
          <button
            onClick={newChat}
            title="New chat"
            className="flex items-center gap-1 rounded-[6px] px-2 py-1 text-[11.5px] text-[var(--text-mute)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
          >
            <Plus className="h-3 w-3" /> New
          </button>

          <Dropdown>
            <DropdownTrigger>
              <button
                title="Chat history"
                className="flex items-center gap-1 rounded-[6px] px-2 py-1 text-[11.5px] text-[var(--text-mute)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
              >
                <History className="h-3 w-3" /> History
              </button>
            </DropdownTrigger>
            <DropdownContent className="max-h-64 w-60 overflow-auto">
              {sessions.length === 0 ? (
                <div className="px-2.5 py-2 text-[12px] text-[var(--text-faint)]">No saved chats</div>
              ) : (
                sessions.map(s => (
                  <div
                    key={s.id}
                    className="group flex items-center gap-1 rounded-[6px] px-2 py-1.5 hover:bg-[var(--surface-2)]"
                  >
                    <button
                      onClick={() => void loadSession(s.id)}
                      className={cn(
                        'flex-1 truncate text-left text-[12px]',
                        s.id === sessionId ? 'text-[var(--text)]' : 'text-[var(--text-mute)]',
                      )}
                    >
                      {s.title}
                    </button>
                    <button
                      onClick={() => void deleteSession(s.id)}
                      className="shrink-0 text-[var(--text-faint)] opacity-0 transition-opacity hover:text-[var(--err)] group-hover:opacity-100"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))
              )}
            </DropdownContent>
          </Dropdown>
        </div>

        {/* Message stream */}
        <div className="relative min-h-0 flex-1">
          <div
            ref={streamRef}
            className="h-full overflow-y-auto px-4 py-4 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
          >
            {msgs.length === 0 && !busy && (
              <CopilotEmptyState onSend={(text) => void send(text)} disabled={busy} />
            )}
            <div className="flex flex-col gap-3">
              {msgs.map((m, i) => {
                // Skip empty assistant bubbles — placeholder until first token / tool starts.
                if (
                  m.role === 'assistant' &&
                  !m.content.trim() &&
                  !(m.toolCalls && m.toolCalls.length)
                ) {
                  return null
                }
                const isLastAssistant = m.role === 'assistant' && i === lastIdx
                const isStreaming = busy && isLastAssistant
                return (
                  <div
                    key={i}
                    className={cn(
                      'group flex max-w-full',
                      m.role === 'user' ? 'justify-end' : 'items-start',
                    )}
                  >
                    <div className={cn(
                      'flex flex-col',
                      m.role === 'user' ? 'max-w-[85%] items-end' : 'min-w-0 flex-1',
                    )}>
                      <div
                        className={cn(
                          'copilot-chat text-[13.5px] leading-[1.6] text-[var(--text)]',
                          m.role === 'user' && 'rounded-[12px] bg-[var(--surface-2)] px-3 py-1.5 text-[13px] leading-[1.5]',
                        )}
                      >
                        {m.toolCalls && m.toolCalls.length > 0 && (
                          <CopilotToolChips calls={m.toolCalls} />
                        )}
                        {m.role === 'assistant' ? (
                          <>
                            <CopilotMessage content={m.content} />
                            {isStreaming && m.content.trim() && <StreamingCursor />}
                          </>
                        ) : (
                          <div className="whitespace-pre-wrap break-words">{m.content}</div>
                        )}
                      </div>
                      {!isStreaming && (
                        <MessageActions
                          onCopy={() => void navigator.clipboard.writeText(m.content)}
                          onRetry={m.role === 'assistant' ? () => retryFromAssistant(i) : undefined}
                        />
                      )}
                    </div>
                  </div>
                )
              })}

              {/* Typing indicator — only while no assistant content / tool has streamed yet. */}
              {busy &&
                !(
                  lastAssistantIsLive &&
                  (msgs[lastIdx].content.trim() ||
                    (msgs[lastIdx].toolCalls && msgs[lastIdx].toolCalls!.length > 0))
                ) && (
                  <div className="rounded-[10px] bg-[var(--surface)] px-3 py-2 w-fit">
                    <TypingDots />
                  </div>
                )}
            </div>
          </div>

          {/* Jump-to-latest pill */}
          {!stickToBottom && msgs.length > 0 && (
            <button
              onClick={jumpToBottom}
              className="absolute bottom-3 left-1/2 -translate-x-1/2 inline-flex items-center gap-1.5 rounded-full border border-[var(--border-soft)] bg-[var(--bg-2)] px-3 py-1.5 text-[11.5px] font-medium text-[var(--text-mute)] shadow-[0_8px_24px_-8px_oklch(0_0_0/0.5)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
              title="Jump to latest"
            >
              <ArrowDown className="h-3.5 w-3.5" /> Latest
            </button>
          )}

        </div>

        {/* Quick action chips */}
        <div className="flex shrink-0 flex-wrap gap-1.5 px-4 pb-3">
          {quickActions.map(qa => (
            <button
              key={qa.text}
              disabled={busy}
              onClick={() => void send(qa.text)}
              className={cn(
                'flex items-center gap-1 rounded-full border border-[var(--border-faint)] px-2.5 py-1 text-[11.5px] text-[var(--text-mute)]',
                'transition-colors hover:border-[var(--border-soft)] hover:bg-[var(--surface)] hover:text-[var(--text)]',
                'disabled:pointer-events-none disabled:opacity-40',
              )}
            >
              <Zap className="h-3 w-3" />
              {qa.label}
            </button>
          ))}
        </div>

        {/* Proposed-changes diff banner */}
        <DiffBanner />

        {error && (
          <div className="mx-3 mb-2 rounded-[8px] border border-[var(--err)]/30 bg-[var(--err)]/10 px-3 py-2 text-[11.5px] text-[var(--err)]">
            {error}
          </div>
        )}

        {/* Composer */}
        <div className="shrink-0 border-t border-[var(--border-faint)] p-3">
          <div className="relative">
            {slashOpen && slashFilter.length > 0 && (
              <div className="absolute bottom-[calc(100%+6px)] left-0 right-0 overflow-hidden rounded-[10px] border border-[var(--border)] bg-[var(--bg-2)] shadow-lg">
                {slashFilter.map((c, i) => (
                  <button
                    key={c.cmd}
                    onMouseEnter={() => setSlashIdx(i)}
                    onClick={() => selectSlashCommand(c.cmd)}
                    className={cn(
                      'flex w-full items-center gap-2.5 px-3 py-2 text-left text-[12px] transition-colors',
                      i === slashIdx ? 'bg-[var(--surface)]' : 'hover:bg-[var(--surface)]',
                    )}
                  >
                    <c.Icon className="h-3.5 w-3.5 shrink-0 text-[var(--text-faint)]" />
                    <span className="font-mono text-[var(--text)]">{c.cmd}</span>
                    <span className="text-[var(--text-faint)]">{c.hint}</span>
                  </button>
                ))}
              </div>
            )}

            <div className="flex items-end gap-2 rounded-[10px] border border-[var(--border-faint)] bg-[var(--bg)] px-3 py-2 transition-colors focus-within:border-[var(--border-soft)]">
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Ask anything, or type / for commands…"
                rows={1}
                disabled={busy}
                className={cn(
                  'min-h-[20px] max-h-[120px] flex-1 resize-none bg-transparent text-[12.5px] leading-relaxed text-[var(--text)] outline-none',
                  'placeholder:text-[var(--text-dim)] disabled:opacity-50',
                  '[scrollbar-width:none] [&::-webkit-scrollbar]:hidden',
                )}
                style={{ height: 'auto' }}
                onInput={e => {
                  const el = e.currentTarget
                  el.style.height = 'auto'
                  el.style.height = `${el.scrollHeight}px`
                }}
              />
              {busy ? (
                <button
                  onClick={cancel}
                  title="Stop generating"
                  className={cn(
                    'flex h-6 w-6 shrink-0 items-center justify-center rounded-[6px]',
                    'bg-[var(--err)] text-[var(--bg)] transition-colors hover:opacity-90',
                  )}
                >
                  <Square className="h-3 w-3 fill-current" />
                </button>
              ) : (
                <button
                  disabled={!input.trim()}
                  onClick={() => void send()}
                  title="Send"
                  className={cn(
                    'flex h-6 w-6 shrink-0 items-center justify-center rounded-[6px] bg-[var(--text)] text-[var(--bg)] transition-colors',
                    'hover:opacity-90 disabled:pointer-events-none disabled:opacity-30',
                  )}
                >
                  <Send className="h-3 w-3" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
