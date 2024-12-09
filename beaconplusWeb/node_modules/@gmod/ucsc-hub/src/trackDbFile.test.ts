import fs from 'fs'
import TrackDbFile from './trackDbFile'

test('reads a basic trackDb.txt file', () => {
  const input = fs.readFileSync('test/basic.trackDb.txt', 'utf8')
  const trackDb = new TrackDbFile(input)
  expect(trackDb).toMatchSnapshot()
})

test('gets settings', () => {
  const input = fs.readFileSync('test/superTrack.trackDb.txt', 'utf8')
  const trackDb = new TrackDbFile(input)
  expect(trackDb).toMatchSnapshot()
  expect(trackDb.settings('myFirstTrack')).toMatchSnapshot()
})

test('parses an extended trackDB.txt file', () => {
  const input = fs.readFileSync('test/extended.trackDb.txt', 'utf8')
  const trackDb = new TrackDbFile(input)
  expect(trackDb).toMatchSnapshot()
  expect(trackDb.settings('26_plus')).toMatchSnapshot()
})

test("throws if each track doesn't start with track", () =>
  expect(
    () =>
      new TrackDbFile('myTrack dnaseSignal\nbigDataUrl dnaseSignal.bigWig\n'),
  ).toThrow(/trackDb has .* instead of "track" as the first line/))

test('throws if a track is missing required keys', () =>
  expect(
    () => new TrackDbFile('track dnaseSignal\nbigDataUrl dnaseSignal.bigWig\n'),
  ).toThrow(/Track .* is missing required entry:/))

test("throws if each track isn't a parent track and doesn't have bigDataUrl", () =>
  expect(
    () =>
      new TrackDbFile(
        'track dnaseSignal\nshortLabel DNAse Signal\nlongLabel Depth of alignments of DNAse reads\ntype bigWig\n',
      ),
  ).toThrow(/Track .* is missing required key "bigDataUrl"/))

test('throws if neither a track nor its parents have a type', () =>
  expect(
    () =>
      new TrackDbFile(
        'track dnaseSignal\nbigDataUrl dnaseSignal.bigWig\nshortLabel DNAse Signal\nlongLabel Depth of alignments of DNAse reads\n',
      ),
  ).toThrow(
    /Neither track .* nor any of its parent tracks have the required key "type"/,
  ))

test("throws if trying to get settings for a track that doesn't exist", () =>
  expect(() =>
    new TrackDbFile(fs.readFileSync('test/basic.trackDb.txt', 'utf8')).settings(
      'nonexistent',
    ),
  ).toThrow(/Track nonexistent does not exist/))
