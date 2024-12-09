import parser from './autoSql'
import types from './defaultTypes'
import { detectTypes, AutoSqlSchema, AutoSqlPreSchema } from './util'

const strandMap = { '.': 0, '-': -1, '+': 1 }

// heuristic that a BED file is BED12 like...the number in col 10 is blockCount-like
function isBed12Like(fields: string[]) {
  return (
    fields.length >= 12 &&
    !Number.isNaN(parseInt(fields[9], 10)) &&
    fields[10]?.split(',').filter(f => !!f).length === parseInt(fields[9], 10)
  )
}
export default class BED {
  public autoSql: AutoSqlSchema

  private attemptDefaultBed?: boolean

  constructor(args: { autoSql?: string; type?: string } = {}) {
    if (args.autoSql) {
      this.autoSql = detectTypes(parser.parse(args.autoSql) as AutoSqlPreSchema)
    } else if (args.type) {
      if (!types[args.type]) {
        throw new Error('Type not found')
      }
      this.autoSql = detectTypes(types[args.type])
    } else {
      this.autoSql = detectTypes(types.defaultBedSchema)
      this.attemptDefaultBed = true
    }
  }

  /*
   * parses a line of text as a BED line with the loaded autoSql schema
   *
   * @param line - a BED line as tab delimited text or array
   * @param opts - supply opts.uniqueId
   * @return a object representing a feature
   */
  parseLine(line: string | string[], opts: { uniqueId?: string } = {}) {
    const { autoSql } = this
    const { uniqueId } = opts
    const fields = Array.isArray(line) ? line : line.split('\t')

    let feature = {} as Record<string, any>
    if (
      !this.attemptDefaultBed ||
      (this.attemptDefaultBed && isBed12Like(fields))
    ) {
      for (let i = 0; i < autoSql.fields.length; i++) {
        const autoField = autoSql.fields[i]
        let columnVal: any = fields[i]
        const { isNumeric, isArray, arrayIsNumeric, name } = autoField
        if (columnVal === null || columnVal === undefined) {
          break
        }
        if (columnVal !== '.') {
          if (isNumeric) {
            const num = Number(columnVal)
            columnVal = Number.isNaN(num) ? columnVal : num
          } else if (isArray) {
            columnVal = columnVal.split(',')
            if (columnVal[columnVal.length - 1] === '') {
              columnVal.pop()
            }
            if (arrayIsNumeric) {
              columnVal = columnVal.map(Number)
            }
          }

          feature[name] = columnVal
        }
      }
    } else {
      const fieldNames = ['chrom', 'chromStart', 'chromEnd', 'name']
      feature = Object.fromEntries(
        fields.map((f, i) => [fieldNames[i] || 'field' + i, f]),
      )
      feature.chromStart = +feature.chromStart
      feature.chromEnd = +feature.chromEnd
      if (!Number.isNaN(Number.parseFloat(feature.field4))) {
        feature.score = +feature.field4
        delete feature.field4
      }
      if (feature.field5 === '+' || feature.field5 === '-') {
        feature.strand = feature.field5
        delete feature.field5
      }
    }
    if (uniqueId) {
      feature.uniqueId = uniqueId
    }
    feature.strand = strandMap[feature.strand as keyof typeof strandMap] || 0

    feature.chrom = decodeURIComponent(feature.chrom)
    return feature
  }
}
