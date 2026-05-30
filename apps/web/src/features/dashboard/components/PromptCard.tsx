import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { Mic, ArrowUp } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useToast } from '@/shared/components'

interface PromptCardProps {
  onSubmit: (prompt: string) => void | Promise<void>
  busy?: boolean
}

// Minimal Web Speech API shape — not in lib.dom by default.
interface RecogResult {
  isFinal: boolean
  0: { transcript: string }
}
interface RecogEvent {
  resultIndex: number
  results: { length: number; [i: number]: RecogResult }
}
interface Recog {
  continuous: boolean
  interimResults: boolean
  lang: string
  start: () => void
  stop: () => void
  onresult: ((e: RecogEvent) => void) | null
  onend: (() => void) | null
  onerror: (() => void) | null
}
type RecogCtor = new () => Recog

export function PromptCard({ onSubmit, busy }: PromptCardProps) {
  const { toast } = useToast()
  const [prompt, setPrompt] = useState('')
  const [listening, setListening] = useState(false)
  const recRef = useRef<Recog | null>(null)
  const baseRef = useRef('')

  const RecogCtor: RecogCtor | undefined =
    typeof window === 'undefined'
      ? undefined
      : (window as unknown as { SpeechRecognition?: RecogCtor; webkitSpeechRecognition?: RecogCtor })
          .SpeechRecognition ??
        (window as unknown as { webkitSpeechRecognition?: RecogCtor }).webkitSpeechRecognition
  const voiceSupported = !!RecogCtor

  const toggleVoice = () => {
    if (!RecogCtor) {
      toast('Voice not supported in this browser', { variant: 'warn' })
      return
    }
    if (listening) {
      recRef.current?.stop()
      return
    }
    const rec = new RecogCtor()
    rec.continuous = true
    rec.interimResults = true
    rec.lang = 'en-US'
    baseRef.current = prompt + (prompt && !prompt.endsWith(' ') ? ' ' : '')
    rec.onresult = (e: RecogEvent) => {
      let interim = ''
      let appended = ''
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i]
        if (r.isFinal) appended += r[0].transcript
        else interim += r[0].transcript
      }
      if (appended) baseRef.current += appended
      setPrompt(baseRef.current + interim)
    }
    rec.onend = () => {
      setListening(false)
      recRef.current = null
    }
    rec.onerror = () => {
      setListening(false)
      recRef.current = null
    }
    rec.start()
    recRef.current = rec
    setListening(true)
  }

  // Stop dictation on unmount
  useEffect(() => () => recRef.current?.stop(), [])

  const handleSend = () => {
    const text = prompt.trim()
    if (!text || busy) return
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
        disabled={busy}
        rows={2}
        placeholder="Describe an automation. Copilot drafts the workflow, wires the nodes, and proposes it on the canvas."
        className="min-h-[60px] w-full resize-none border-none bg-transparent text-[14.5px] leading-[1.5] text-[var(--text)] outline-none placeholder:text-[var(--text-faint)] disabled:opacity-60"
      />

      <div className="mt-2 flex items-center justify-end gap-1">
        <button
          type="button"
          onClick={toggleVoice}
          disabled={!voiceSupported || busy}
          title={
            voiceSupported
              ? listening
                ? 'Stop dictation'
                : 'Dictate'
              : 'Voice not supported in this browser'
          }
          className={cn(
            'inline-flex h-7 w-7 items-center justify-center rounded-[7px] transition-colors',
            listening
              ? 'animate-pulse bg-[var(--err)]/15 text-[var(--err)]'
              : 'text-[var(--text-mute)] hover:bg-[var(--surface)] hover:text-[var(--text)]',
            (!voiceSupported || busy) && 'cursor-not-allowed opacity-40',
          )}
        >
          <Mic className="h-3.5 w-3.5" />
        </button>

        <button
          type="button"
          onClick={handleSend}
          disabled={!prompt.trim() || busy}
          title="Send to Copilot"
          className="inline-flex h-7 w-7 items-center justify-center rounded-[7px] bg-[var(--text)] text-[var(--bg)] transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-30"
        >
          <ArrowUp className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}
