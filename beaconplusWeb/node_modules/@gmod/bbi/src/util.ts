export class AbortError extends Error {
  public code: string

  public constructor(message: string) {
    super(message)
    this.code = 'ERR_ABORTED'
  }
}
// sort blocks by file offset and
// group blocks that are within 2KB of eachother
export function groupBlocks(blocks: { offset: bigint; length: bigint }[]) {
  blocks.sort((b0, b1) => Number(b0.offset) - Number(b1.offset))

  const blockGroups = []
  let lastBlock
  let lastBlockEnd
  for (const block of blocks) {
    if (
      lastBlock &&
      lastBlockEnd &&
      Number(block.offset) - lastBlockEnd <= 2000
    ) {
      lastBlock.length = BigInt(
        Number(lastBlock.length) +
          Number(block.length) -
          lastBlockEnd +
          Number(block.offset),
      )
      lastBlock.blocks.push(block)
    } else {
      blockGroups.push(
        (lastBlock = {
          blocks: [block],
          length: block.length,
          offset: block.offset,
        }),
      )
    }
    lastBlockEnd = Number(lastBlock.offset) + Number(lastBlock.length)
  }

  return blockGroups
}

/**
 * Properly check if the given AbortSignal is aborted.
 * Per the standard, if the signal reads as aborted,
 * this function throws either a DOMException AbortError, or a regular error
 * with a `code` attribute set to `ERR_ABORTED`.
 *
 * For convenience, passing `undefined` is a no-op
 *
 * @param {AbortSignal} [signal] an AbortSignal, or anything with an `aborted` attribute
 * @returns nothing
 */
export function checkAbortSignal(signal?: AbortSignal): void {
  if (!signal) {
    return
  }

  if (signal.aborted) {
    // console.log('bam aborted!')
    if (typeof DOMException === 'undefined') {
      const e = new AbortError('aborted')
      e.code = 'ERR_ABORTED'
      throw e
    } else {
      throw new DOMException('aborted', 'AbortError')
    }
  }
}

/**
 * Skips to the next tick, then runs `checkAbortSignal`.
 * Await this to inside an otherwise synchronous loop to
 * provide a place to break when an abort signal is received.
 * @param {AbortSignal} signal
 */
export async function abortBreakPoint(signal?: AbortSignal): Promise<void> {
  await Promise.resolve()
  checkAbortSignal(signal)
}
