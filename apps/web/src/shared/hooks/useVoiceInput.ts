import { useEffect, useRef, useState } from 'react'

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

interface Options {
  value: string
  onChange: (next: string) => void
  lang?: string
}

/**
 * Toggleable speech-to-text that appends transcripts to a controlled text value.
 * `supported` reflects browser availability; `toggle()` starts/stops a session;
 * interim results stream live, final results are persisted on stop.
 */
export function useVoiceInput({ value, onChange, lang = 'en-US' }: Options) {
  const [listening, setListening] = useState(false)
  const recRef = useRef<Recog | null>(null)
  const baseRef = useRef('')

  const RecogCtor: RecogCtor | undefined =
    typeof window === 'undefined'
      ? undefined
      : (window as unknown as { SpeechRecognition?: RecogCtor; webkitSpeechRecognition?: RecogCtor })
          .SpeechRecognition ??
        (window as unknown as { webkitSpeechRecognition?: RecogCtor }).webkitSpeechRecognition
  const supported = !!RecogCtor

  const toggle = () => {
    if (!RecogCtor) return
    if (listening) {
      recRef.current?.stop()
      return
    }
    const rec = new RecogCtor()
    rec.continuous = true
    rec.interimResults = true
    rec.lang = lang
    baseRef.current = value + (value && !value.endsWith(' ') ? ' ' : '')
    rec.onresult = (e: RecogEvent) => {
      let interim = ''
      let appended = ''
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i]
        if (r.isFinal) appended += r[0].transcript
        else interim += r[0].transcript
      }
      if (appended) baseRef.current += appended
      onChange(baseRef.current + interim)
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

  useEffect(() => () => recRef.current?.stop(), [])

  return { supported, listening, toggle }
}
