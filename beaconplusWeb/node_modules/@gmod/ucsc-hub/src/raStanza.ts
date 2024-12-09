/**
 * Class representing an ra file stanza. Each stanza line is split into its key
 * and value and stored as a Map, so the usual Map methods can be used on the
 * stanza.
 */
export default class RaStanza {
  data: Record<string, string> = {}

  name?: string

  nameKey?: string

  constructor(
    stanza: string | string[] = [],
    options?: { checkIndent?: boolean; skipValidation?: boolean },
  ) {
    const { checkIndent = true, skipValidation = false } = options ?? {}
    let stanzaLines: string[]
    if (typeof stanza === 'string') {
      stanzaLines = stanza.trimEnd().split(/\r?\n/)
    } else if (stanza) {
      stanzaLines = stanza
    } else {
      stanzaLines = []
    }

    let currentIndent: string | undefined

    let continuedLine: string | undefined
    for (const line of stanzaLines) {
      if (line === '') {
        throw new Error('Invalid stanza, contained blank lines')
      }
      if (line.trim().startsWith('#')) {
        continue
      }
      if (line.trimEnd().endsWith('\\')) {
        const trimmedLine = line.trimEnd().slice(0, -1)
        if (continuedLine) {
          continuedLine += trimmedLine.trimStart()
        } else {
          continuedLine = trimmedLine
        }
        continue
      }
      let combinedLine = line
      if (continuedLine) {
        combinedLine = continuedLine + combinedLine.trimStart()
        continuedLine = undefined
      }
      if (currentIndent ?? checkIndent) {
        const indent = combinedLine.match(/^([ \t]+)/)
        if (currentIndent === undefined) {
          if (indent) {
            ;[, currentIndent] = indent
          } else {
            currentIndent = ''
          }
        } else if (
          (currentIndent === '' && indent !== null) ||
          (currentIndent && indent && currentIndent !== indent[1])
        ) {
          throw new Error('Inconsistent indentation of stanza')
        }
      } else {
        currentIndent = ''
      }
      const trimmedLine = combinedLine.trim()
      const sep = trimmedLine.indexOf(' ')
      if (sep === -1) {
        if (!this.nameKey) {
          throw new Error(
            'First line in a stanza must have both a key and a value',
          )
        }
        // Adding a key that already exists and has no value is a no-op
        if (this.data[trimmedLine]) {
          continue
        }
        this.data[trimmedLine] = ''
        continue
      }
      const key = trimmedLine.slice(0, sep)
      const value = trimmedLine.slice(sep + 1)
      if (this.data[key] && value !== this.data[key]) {
        throw new Error(
          'Got duplicate key with a different value in stanza: ' +
            `"${key}" key has both ${this.data[key]} and ${value}`,
        )
      }
      if (!this.nameKey) {
        this.nameKey = key
        this.name = trimmedLine.slice(sep + 1)
      }
      this.data[key] = value
    }

    if (!skipValidation) {
      this.validate()
    }
  }

  protected validate() {}
}
