import RaFile from './raFile'
import { validateRequiredFieldsArePresent } from './util'

/**
 * Class representing a genomes.txt file.
 * @extends RaFile
 * @param {(string|string[])} [genomesFile=[]] - A genomes.txt file as a string
 * @throws {Error} Throws if the first line of the hub.txt file doesn't start
 * with "genome <genome_name>" or if it has invalid entries
 */
export default class GenomesFile extends RaFile {
  public validate(requiredFields = ['genome', 'trackDb']) {
    // TODO: check if genome is hosted by UCSC and if not, require twoBitPath and groups

    if (this.nameKey !== 'genome') {
      throw new Error(
        'Genomes file must begin with a line like "genome <genome_name>"',
      )
    }

    for (const [genomeName, genome] of Object.entries(this.data)) {
      validateRequiredFieldsArePresent(
        genome!,
        requiredFields,
        `genome ${genomeName}`,
      )
    }
  }
}
