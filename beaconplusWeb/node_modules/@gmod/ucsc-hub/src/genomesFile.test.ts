import fs from 'fs'
import GenomesFile from './genomesFile'

describe('GenomesFile', () => {
  it('reads a basic genomes.txt file', () => {
    const input = fs.readFileSync('test/basic.genomes.txt', 'utf8')
    const genomesFile = new GenomesFile(input)
    expect(genomesFile).toMatchSnapshot()
  })

  it("throws if the file doesn't start with a genomes entry", () =>
    expect(
      () => new GenomesFile('assembly hg19\ntrackDb hg19/trackDb.txt'),
    ).toThrow(/file must begin with a line like/))

  it('throws if a genome entry is missing a required field', () =>
    expect(
      () =>
        new GenomesFile(
          'genome hg19\ntrackDb hg19/trackDb.txt\n\ngenome hg38\norganism Homo sapiens',
        ),
    ).toThrow(/is missing required entry:/))
})
