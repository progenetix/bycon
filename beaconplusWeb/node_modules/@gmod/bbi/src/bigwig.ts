import { BlockView } from './block-view'
import { BBI, RequestOptions } from './bbi'

export class BigWig extends BBI {
  /**
   * Retrieves a BlockView of a specific zoomLevel
   *
   * @param scale - number
   * @param opts - An object containing basesPerSpan (e.g. pixels per basepair) or scale used to infer the zoomLevel to use
   */
  protected async getView(scale: number, opts: RequestOptions) {
    const { zoomLevels, refsByName, fileSize, isBigEndian, uncompressBufSize } =
      await this.getHeader(opts)
    const basesPerPx = 1 / scale
    let maxLevel = zoomLevels.length
    if (!fileSize) {
      // if we don't know the file size, we can't fetch the highest zoom level :-(
      maxLevel -= 1
    }

    for (let i = maxLevel; i >= 0; i -= 1) {
      const zh = zoomLevels[i]
      if (zh && zh.reductionLevel <= 2 * basesPerPx) {
        const indexOffset = Number(zh.indexOffset)

        return new BlockView(
          this.bbi,
          refsByName,
          indexOffset,
          isBigEndian,
          uncompressBufSize > 0,
          'summary',
        )
      }
    }
    return this.getUnzoomedView(opts)
  }
}
