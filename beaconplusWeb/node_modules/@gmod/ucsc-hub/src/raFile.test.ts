import fs from 'fs'
import RaFile from './raFile'

test('creates an empty ra file', () => {
  const raFile = new RaFile()
  expect(raFile.nameKey).toBeUndefined()
})

test('parses a simple three stanza file', () => {
  const input = fs.readFileSync('test/basic.ra', 'utf8')
  const raFile = new RaFile(input)
  expect(raFile).toMatchSnapshot()
  expect(raFile.nameKey).toEqual('key1')
})

test('parses a file with comments', () => {
  const input = fs.readFileSync('test/comments.ra', 'utf8')
  const raFile = new RaFile(input)
  expect(raFile).toMatchSnapshot()

  expect(raFile.nameKey).toEqual('key1')
})

test('handles CRLF newlines', () => {
  const input =
    'key1 valueA\r\n' +
    'key2 valueB\r\n\r\n' +
    '# A comment\r\n\r\n' +
    'key1 valueC\r\n' +
    'key2 valueD\r\n'
  const raFile = new RaFile(input)
  expect(raFile).toMatchSnapshot()
  expect(raFile.nameKey).toEqual('key1')
})

test('parses a list of stanzas', () => {
  const input = [
    'key1 valueA\nkey2 valueB\n',
    '# A comment\n',
    'key1 valueC\nkey2 valueD\n',
  ]
  const raFile = new RaFile(input)
  expect(raFile).toMatchSnapshot()
  expect(raFile.nameKey).toEqual('key1')
})

test('handles indented stanzas', () => {
  const input = fs.readFileSync('test/indented.ra', 'utf8')
  const raFile = new RaFile(input)
  expect(raFile).toMatchSnapshot()
  expect(raFile.nameKey).toEqual('key1')
})

test('throws on an empty stanza', () => {
  expect(() => new RaFile('')).toThrow(/Invalid stanza, was empty/)
})

test('throws if stanzas have mismatched keys', () => {
  expect(
    () => new RaFile(fs.readFileSync('test/mismatchKeys.ra', 'utf8')),
  ).toThrow(/must have the same key/)
})

test('throws if stanzas have duplicate names', () => {
  expect(
    () => new RaFile(fs.readFileSync('test/duplicateName.ra', 'utf8')),
  ).toThrow(/duplicate stanza name/)
})
