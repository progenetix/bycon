## [4.0.4](https://github.com/GMOD/bbi-js/compare/v4.0.3...v4.0.4) (2024-3-5)



- Fix issue fetching data from file where refNames are not sorted (#59)

## [4.0.3](https://github.com/GMOD/bbi-js/compare/v4.0.2...v4.0.3) (2024-01-16)

### Performance Improvements

- optimize `parseBigBedBlock` ([#58](https://github.com/GMOD/bbi-js/issues/58))
  ([eb3f7a4](https://github.com/GMOD/bbi-js/commit/eb3f7a4885c4e8262c6e3e63696b533e53072463))

* Small perf improvement (#58)

## [4.0.2](https://github.com/GMOD/bbi-js/compare/v4.0.1...v4.0.2) (2023-07-30)

- Fix issue with fetching headers that are large in certain cases

## [4.0.1](https://github.com/GMOD/bbi-js/compare/v4.0.0...v4.0.1) (2023-07-13)

- Fix eslint plugin being in dependencies Accidentally

# [4.0.0](https://github.com/GMOD/bbi-js/compare/v3.0.1...v4.0.0) (2023-05-05)

- Improve typescripting, refactoring
- Options argument only accepts {signal}, not just signal now

## [3.0.1](https://github.com/GMOD/bbi-js/compare/v3.0.0...v3.0.1) (2023-04-21)

### Features

- explicit buffer import ([#53](https://github.com/GMOD/bbi-js/issues/53))
  ([2699c98](https://github.com/GMOD/bbi-js/commit/2699c983dea380bbb56773058ba3f233c833d9c8))

* Add explicit Buffer import

# [3.0.0](https://github.com/GMOD/bbi-js/compare/v2.0.5...v3.0.0) (2023-01-11)

- Update to rxjs 7

## [2.0.5](https://github.com/GMOD/bbi-js/compare/v2.0.4...v2.0.5) (2022-12-17)

- Cleanup package.json and README

## [2.0.4](https://github.com/GMOD/bbi-js/compare/v2.0.3...v2.0.4) (2022-10-15)

- Use plain TextDecoder for decoding autoSql

## [2.0.3](https://github.com/GMOD/bbi-js/compare/v2.0.2...v2.0.3) (2022-10-10)

- Add BigInt64 polyfill for older safari

## [2.0.2](https://github.com/GMOD/bbi-js/compare/v2.0.1...v2.0.2) (2022-07-18)

- Make basesCovered a number instead of BigInt

## [2.0.1](https://github.com/GMOD/bbi-js/compare/v2.0.0...v2.0.1) (2022-07-18)

- Bump generic-filehandle 2->3

# [2.0.0](https://github.com/GMOD/bbi-js/compare/v1.0.35...v2.0.0) (2022-07-18)

- Use binary-parser instead of @gmod/binary-parser, with some optimizations.
  This uses BigInt and TextDecoder, so requires a major version bump

## [1.0.35](https://github.com/GMOD/bbi-js/compare/v1.0.34...v1.0.35) (2022-04-22)

- Produce actual ESM module for the "module" field in package.json, was commonJS
- Add sourceMap:true to tsconfig

## [1.0.34](https://github.com/GMOD/bbi-js/compare/v1.0.33...v1.0.34) (2022-03-11)

### Reverts

- Revert "Use subarray instead of slice since slice is deprecated under node
  xref 'https://nodejs.org/api/buffer.html#bufslicestart-end'"
  ([44116cc](https://github.com/GMOD/bbi-js/commit/44116cce54601727d37f1c449bfcc60c1b4e602d))

* Back to slice instead of subarray, as subarray returned a UInt8Array instead
  of a true Buffer

## [1.0.33](https://github.com/GMOD/bbi-js/compare/v1.0.32...v1.0.33) (2022-02-25)

- Use subarray instead of slice since slice is deprecated under node xref
  'https://nodejs.org/api/buffer.html#bufslicestart-end'"

## [1.0.32](https://github.com/GMOD/bbi-js/compare/v1.0.31...v1.0.32) (2022-02-16)

- Use pako to decode on command line instead of using zlib to avoid need to
  manually polyfill zlib

## [1.0.31](https://github.com/GMOD/bbi-js/compare/v1.0.30...v1.0.31) (2021-12-14)

- Add esm module builds with less babelification for smaller bundle sizes

## [1.0.30](https://github.com/GMOD/bbi-js/compare/v1.0.29...v1.0.30) (2020-06-25)

- Use abortable-promise-cache instead of abortable-memoize
- Allow opts parameter to getHeader instead of just abortsignal

## [1.0.29](https://github.com/GMOD/bbi-js/compare/v1.0.28...v1.0.29) (2020-01-28)

- Accidentally made the package include itself as dependency in 1.0.28,
  republish

## [1.0.28](https://github.com/GMOD/bbi-js/compare/v1.0.27...v1.0.28) (2020-01-28)

- Change typescript interface to use object keys instead of Map type for
  refsByName, refsById
- Typescript only release change

## [1.0.27](https://github.com/GMOD/bbi-js/compare/v1.0.26...v1.0.27) (2020-01-10)

- Reduce number of requests needed on initial header
- Add definedFieldCount to the returned Header

Thanks to @skinner for both of these contributions!

## [1.0.26](https://github.com/GMOD/bbi-js/compare/v1.0.25...v1.0.26) (2019-11-10)

- Fix important bug with fixed step bigwig files not using the proper start
  coordinate

## [1.0.25](https://github.com/GMOD/bbi-js/compare/v1.0.24...v1.0.25) (2019-11-03)

- Add fix for files with a large header, if autoSql is large in a bigbed file
  would be likely scenario

## [1.0.24](https://github.com/GMOD/bbi-js/compare/v1.0.23...v1.0.24) (2019-10-29)

- Fix the uniqueIds generated via the bigbed features

## [1.0.23](https://github.com/GMOD/bbi-js/compare/v1.0.22...v1.0.23) (2019-10-06)

- Small refactor of `filehandle.read()` to make it more robust

## [1.0.22](https://github.com/GMOD/bbi-js/compare/v1.0.21...v1.0.22) (2019-06-13)

- Bump generic-filehandle
- Add more checks for abort signal to allow early bailing

## [1.0.21](https://github.com/GMOD/bbi-js/compare/v1.0.20...v1.0.21) (2019-05-09)

- Add fix for reading files with greater than 256 contigs

## [1.0.20](https://github.com/GMOD/bbi-js/compare/v1.0.19...v1.0.20) (2019-05-06)

- Add fix that prevented accessing the lowest zoom/reduction level

## [1.0.19](https://github.com/GMOD/bbi-js/compare/v1.0.18...v1.0.19) (2019-05-02)

- Add regression fix since 1.0.16 for uncompressed files. Thanks to @lidaof for
  reporting!

## [1.0.18](https://github.com/GMOD/bbi-js/compare/v1.0.17...v1.0.18) (2019-05-02)

- Improve error handling of the observables (issue #20, pull #21)
- Bump generic-filehandle to 1.0.9 to fix compatibility with native browser
  fetch

## [1.0.17](https://github.com/GMOD/bbi-js/compare/v1.0.16...v1.0.17) (2019-04-30)

- Use some standard rxjs notions for combining operator results
- Add parsing of the extraIndex data in BigBed, allowing you to call
  bigbed.searchExtraIndex(name[,opts])

## [1.0.16](https://github.com/GMOD/bbi-js/compare/v1.0.15...v1.0.16) (2019-04-23)

- Pre-compile binary-parser instances for faster
- Important: fixed bug that caused bigwig summary blocks to not be returned in
  output

## [1.0.15](https://github.com/GMOD/bbi-js/compare/v1.0.14...v1.0.15) (2019-04-18)

- Make important performance improvement for BigWig data

## [1.0.14](https://github.com/GMOD/bbi-js/compare/v1.0.12...v1.0.14) (2019-04-17)

- Improve documentation for integration with @gmod/bed@2
- Fix some cases where abortSignal was passed incorrectly to filehandle

## [1.0.13](https://github.com/GMOD/bbi-js/compare/v1.0.12...v1.0.13) (2019-04-14)

- Added uniqueId to objects returned from BigBed to avoid issue with duplicates

## [1.0.12](https://github.com/GMOD/bbi-js/compare/v1.0.11...v1.0.12) (2019-04-12)

- Fix returning bigbed objects on empty regions

## [1.0.11](https://github.com/GMOD/bbi-js/compare/v1.0.10...v1.0.11) (2019-04-10)

- Removed polyfill of Array.prototype.flat which modifies global scope

## [1.0.10](https://github.com/GMOD/bbi-js/compare/v1.0.9...v1.0.10) (2019-04-09)

- Fix misinterpretation of variable step wig files in this module (the span is
  not variable in variable step files, only the step, use bedGraphToBigWig for
  variable span)
- Improved docs

## [1.0.9](https://github.com/GMOD/bbi-js/compare/v1.0.8...v1.0.9) (2019-04-05)

- Added caching of networking requests (thanks @rbuels for the
  abortable-promise-cache module!)
- Fix some type errors on the range class
- Correct using span on fixed size wiggle types

## [1.0.8](https://github.com/GMOD/bbi-js/compare/v1.0.7...v1.0.8) (2019-04-01)

- Fix @babel/runtime in deployed package
- Bugfix to the url argument to the BigWig/BigBed

## [1.0.7](https://github.com/GMOD/bbi-js/compare/v1.0.6...v1.0.7) (2019-04-01)

- Added getFeatureStream which returns an Observable from rxjs
- Added url option to BigWig and BigBed constructors to allow usage of
  RemoteFile filehandle
- Added typescript backend for better processing

## [1.0.6](https://github.com/GMOD/bbi-js/compare/v1.0.5...v1.0.6) (2019-03-15)

- Fix issue with fixed step and variable step bigwig files not working at all

## [1.0.5](https://github.com/GMOD/bbi-js/compare/v1.0.4...v1.0.5) (2019-03-07)

- Fix issue with jest being in deps instead of devDeps

## [1.0.4](https://github.com/GMOD/bbi-js/compare/v1.0.3...v1.0.4) (2019-01-28)

- Add renameRefSeqs functionality where you can apply a callback to the refseq
  names
- Consistently apply start/end coordinate filters at different zoom levels

## [1.0.3](https://github.com/GMOD/bbi-js/compare/v1.0.2...v1.0.3) (2019-01-27)

- Fix issue with properly inflating chunks (issue #1)

## [1.0.2](https://github.com/GMOD/bbi-js/compare/v1.0.1...v1.0.2) (2019-01-24)

- Added regenerator-runtime to babel dist compilation

## [1.0.1](https://github.com/GMOD/bbi-js/compare/v1.0.0...v1.0.1) (2019-01-24)

- Added exports for BigWig and BigBed. const {BigWig, BigBed} =
  require('@gmod/bbi')

# 1.0.0 (2019-01-23)

- Initial version
- Has support for bigwig and bigbed files
