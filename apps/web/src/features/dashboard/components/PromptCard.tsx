import { useState, type KeyboardEvent } from 'react'
import { Mic, ArrowUp } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useVoiceInput } from '@/shared/hooks/useVoiceInput'

interface PromptCardProps {
  onSubmit: (prompt: string) => void | Promise<void>
}

export function PromptCard({ onSubmit }: PromptCardProps) {
  const [prompt, setPrompt] = useState('')
  const voice = useVoiceInput({ value: prompt, onChange: setPrompt })

  const handleSend = () => {
    const text = prompt.trim()
    if (!text) return
    void onSubmit(text)
    setPrompt('')
  }

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="rounded-[12px] border border-[var(--border-faint)] bg-[var(--bg)] px-[18px] pt-4 pb-3 transition-colors focus-within:border-[var(--accent-line)]">
      <textarea
        value={prompt}
        onChange={e => setPrompt(e.target.value)}
        onKeyDown={onKey}
        rows={2}
        placeholder="Describe an automation. Copilot drafts the workflow, wires the nodes, and proposes it on the canvas."
        className="min-h-[60px] w-full resize-none border-none bg-transparent text-[14.5px] leading-[1.5] text-[var(--text)] outline-none placeholder:text-[var(--text-faint)]"
      />

      <div className="mt-2 flex items-center justify-end gap-1">
        <button
          type="button"
          onClick={voice.toggle}
          disabled={!voice.supported}
          title={
            voice.supported
              ? voice.listening
                ? 'Stop dictation'
                : 'Dictate'
              : 'Voice not supported in this browser'
          }
          className={cn(
            'inline-flex h-7 w-7 items-center justify-center rounded-[7px] transition-colors',
            voice.listening
              ? 'animate-pulse bg-[var(--err)]/15 text-[var(--err)]'
              : 'text-[var(--text-mute)] hover:bg-[var(--surface)] hover:text-[var(--text)]',
            !voice.supported && 'cursor-not-allowed opacity-40',
          )}
        >
          <Mic className="h-3.5 w-3.5" />
        </button>

        <button
          type="button"
          onClick={handleSend}
          disabled={!prompt.trim()}
          title="Send to Copilot"
          className="inline-flex h-7 w-7 items-center justify-center rounded-[7px] bg-[var(--text)] text-[var(--bg)] transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-30"
        >
          <ArrowUp className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}
