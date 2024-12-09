import { parse } from './autoSql'
import { AutoSqlPreSchema } from './util'
import * as types from './as/autoSqlSchemas'

export default Object.fromEntries(
  Object.entries(types).map(([key, val]) => [
    key,
    parse(val.trim()) as AutoSqlPreSchema,
  ]),
)
