//@ts-nocheck
export async function readJSON(url, readFile, options = {}) {
  const { defaultContent = {} } = options
  let str
  try {
    str = await readFile(url, { encoding: 'utf8' })
    return JSON.parse(str)
  } catch (error) {
    if (error.code === 'ENOENT' || error.status === 404) {
      return defaultContent
    }
    throw error
  }
}

export function foo() {}
