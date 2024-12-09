import RaStanza from './raStanza'

/**
 * Class representing an ra file. Each file is composed of multiple stanzas, and
 * each stanza is separated by one or more blank lines. Each stanza is stored in
 * a Map with the key being the value of the first key-value pair in the stanza.
 * The usual Map methods can be used on the file. An additional method `add()`
 * is available to take a raw line of text and break it up into a key and value
 * and add them to the class. This should be favored over `set()` when possible,
 * as it performs more validity checks than using `set()`.
 * @extends Map
 * @property {undefined|string} nameKey - The key of the first line of all the
 * stanzas (`undefined` if the stanza has no lines yet).
 * @throws {Error} Throws if an empty stanza is added, if the key in the first
 * key-value pair of each stanze isn't the same, or if two stanzas have the same
 * value for the key-value pair in their first lines.
 * @param {(string|string[])} [raFile=[]] - An ra file, either as a single
 * string or an array of strings with one stanza per entry. Supports both LF
 * and CRLF line terminators.
 * @param {object} options
 * @param {boolean} options.checkIndent [true] - Check if a the stanzas within
 * the file are indented consistently and keep track of the indentation
 */
export default class RaFile {
  data: Record<string, RaStanza | undefined> = {}

  nameKey?: string

  constructor(
    raFile: string | string[] = [],
    options?: { checkIndent?: boolean; skipValidation?: boolean },
  ) {
    const { checkIndent = true, skipValidation = false } = options ?? {}
    let stanzas: string[]
    if (typeof raFile === 'string') {
      stanzas = raFile.trimEnd().split(/(?:[\t ]*\r?\n){2,}/)
    } else if (raFile) {
      stanzas = raFile
    } else {
      stanzas = []
    }
    for (const stanza of stanzas) {
      if (stanza === '') {
        throw new Error('Invalid stanza, was empty')
      }
      if (stanza.trim().startsWith('#')) {
        const stanzaLines = stanza
          .trimEnd()
          .split(/\r?\n/)
          .map(line => line.trim())
        if (stanzaLines.every(line => line.startsWith('#'))) {
          continue
        }
      }
      const raStanza = new RaStanza(stanza, { checkIndent })
      if (!this.nameKey) {
        this.nameKey = raStanza.nameKey
      } else if (raStanza.nameKey !== this.nameKey) {
        throw new Error(
          'The first line in each stanza must have the same key. ' +
            `Saw both ${this.nameKey} and ${raStanza.nameKey}`,
        )
      }
      if (!raStanza.name) {
        throw new Error(`No stanza name: ${raStanza.name}`)
      }
      if (this.data[raStanza.name]) {
        throw new Error(`Got duplicate stanza name: ${raStanza.name}`)
      }

      this.data[raStanza.name] = raStanza
    }

    if (!skipValidation) {
      this.validate()
    }
  }

  protected validate() {}
}
