export type JsonTokenType =
  | 'whitespace'
  | 'key'
  | 'string'
  | 'number'
  | 'boolean'
  | 'null'
  | 'punctuation'

export interface JsonToken {
  type: JsonTokenType
  value: string
}

/**
 * Pretty-print any value as JSON text. Falls back to `String(value)` if
 * serialization fails (e.g. cycles). Returns `''` for null/undefined.
 */
export function stringifyJson(value: unknown, pretty: boolean): string {
  if (value === null || value === undefined) return ''
  try {
    return pretty ? JSON.stringify(value, null, 2) : JSON.stringify(value)
  } catch {
    return String(value)
  }
}

/**
 * Tokenize a JSON string into typed runs for syntax highlighting.
 *
 * Intentionally permissive — if the input isn't strict JSON, anything we can
 * still classify is highlighted and the rest falls back to `punctuation`,
 * so partial / pretty-printed strings never break rendering.
 */
export function tokenizeJson(source: string): JsonToken[] {
  const tokens: JsonToken[] = []
  let i = 0

  while (i < source.length) {
    const ch = source[i]

    if (isWhitespace(ch)) {
      let j = i + 1
      while (j < source.length && isWhitespace(source[j])) j++
      tokens.push({ type: 'whitespace', value: source.slice(i, j) })
      i = j
      continue
    }

    if (ch === '"') {
      let j = i + 1
      while (j < source.length) {
        if (source[j] === '\\') { j += 2; continue }
        if (source[j] === '"') { j++; break }
        j++
      }
      const value = source.slice(i, j)
      // A string is a key if the next non-whitespace char is ':'.
      let k = j
      while (k < source.length && isWhitespace(source[k])) k++
      const isKey = source[k] === ':'
      tokens.push({ type: isKey ? 'key' : 'string', value })
      i = j
      continue
    }

    if (ch === '-' || isDigit(ch)) {
      let j = i + 1
      while (j < source.length && /[0-9.eE+\-]/.test(source[j])) j++
      tokens.push({ type: 'number', value: source.slice(i, j) })
      i = j
      continue
    }

    if (source.startsWith('true', i))  { tokens.push({ type: 'boolean', value: 'true' });  i += 4; continue }
    if (source.startsWith('false', i)) { tokens.push({ type: 'boolean', value: 'false' }); i += 5; continue }
    if (source.startsWith('null', i))  { tokens.push({ type: 'null',    value: 'null' });  i += 4; continue }

    tokens.push({ type: 'punctuation', value: ch })
    i++
  }

  return tokens
}

function isWhitespace(ch: string | undefined): boolean {
  return ch === ' ' || ch === '\t' || ch === '\n' || ch === '\r'
}

function isDigit(ch: string | undefined): boolean {
  return !!ch && ch >= '0' && ch <= '9'
}

/** Best-effort byte size of a JSON-serializable value. */
export function approxJsonSize(value: unknown): number {
  try {
    return new TextEncoder().encode(JSON.stringify(value) ?? '').byteLength
  } catch {
    return 0
  }
}
