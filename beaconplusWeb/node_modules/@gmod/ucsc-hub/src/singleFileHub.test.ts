import fs from 'fs'
import SingleFileHub from './singleFileHub'

// test that singleFileHub can parse singleFileAssemblyHub.txt
test('single-file hub', () => {
  // NOTE: this file was slightly modified from the
  // original to fix inconsistent indentation
  const input = fs.readFileSync(
    'test/singleFileAssemblyHub.GCF_000002985.6.hub.txt',
    'utf8',
  )
  const singleFileHub = new SingleFileHub(input)
  expect(singleFileHub).toMatchSnapshot()
  expect(singleFileHub.genome).toMatchSnapshot()
  expect(singleFileHub.tracks).toMatchSnapshot()
})
