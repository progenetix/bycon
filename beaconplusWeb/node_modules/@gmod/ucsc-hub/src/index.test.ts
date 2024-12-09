import { RaFile, RaStanza } from './index'

describe('ucsc-hub-js', () => {
  it('imports modules', () => {
    expect(RaFile).not.toBeNull()
    expect(RaStanza).not.toBeNull()
  })
})
