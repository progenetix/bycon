import RaStanza from './raStanza'
import TrackDbFile from './trackDbFile'
import { validateRequiredFieldsArePresent } from './util'

/**
 * Class representing a "single-file" hub.txt file that contains all the
 * sections of a hub in a single file.
 */
export default class SingleFileHub {
  public genome: RaStanza

  public tracks: TrackDbFile

  public hubData: RaStanza

  constructor(hubText: string) {
    const [hubSection, genomeSection, ...trackSections] = hubText
      .trimEnd()
      .split(/(?:[\t ]*\r?\n){2,}/)
    this.hubData = new RaStanza(hubSection)
    this.validateHub()

    this.genome = new RaStanza(genomeSection)
    this.validateGenomeSection()

    this.tracks = new TrackDbFile(trackSections.join('\n\n'), {
      skipValidation: false,
    })
  }

  protected validateHub() {
    if (this.hubData.nameKey !== 'hub') {
      throw new Error('Hub file must begin with a line like "hub <hub_name>"')
    }

    validateRequiredFieldsArePresent(this.hubData, [
      'hub',
      'shortLabel',
      'longLabel',
      'email',
      'descriptionUrl',
    ])
  }

  protected validateGenomeSection() {
    if (this.genome.nameKey !== 'genome') {
      throw new Error(
        'Genomes file must begin with a line like "genome <genome_name>"',
      )
    }
  }
}
