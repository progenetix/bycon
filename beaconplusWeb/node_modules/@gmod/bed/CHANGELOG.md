## [2.1.3](https://github.com/GMOD/bed-js/compare/v2.1.2...v2.1.3) (2024-3-25)



- Fix autoSql with comments in column names

## [2.1.2](https://github.com/GMOD/bed-js/compare/v2.1.1...v2.1.2) (2022-07-24)

- Add comment string to autoSql types

## [2.1.1](https://github.com/GMOD/bed-js/compare/v2.1.0...v2.1.1) (2022-07-24)

- Make autoSql a public class field

# [2.1.0](https://github.com/GMOD/bed-js/compare/v2.0.8...v2.1.0) (2022-07-24)

- Typescriptify module and bump some devdeps

## [2.0.8](https://github.com/GMOD/bed-js/compare/v2.0.7...v2.0.8) (2022-03-30)

- Publish src directory for better source maps

## [2.0.7](https://github.com/GMOD/bed-js/compare/v2.0.6...v2.0.7) (2022-03-07)

- Add esm module export to package.json

## [2.0.6](https://github.com/GMOD/bed-js/compare/v2.0.5...v2.0.6) (2021-08-21)

- Simplify build pipeline

## [2.0.5](https://github.com/GMOD/bed-js/compare/v2.0.4...v2.0.5) (2020-12-23)

- Allow comments inside of the autosql table, seen in some clinvar bb

## [2.0.4](https://github.com/GMOD/bed-js/compare/v2.0.3...v2.0.4) (2020-12-03)

- Allow for badly formatted comments not entirely within a quote, was exhibited
  by https://hgdownload.soe.ucsc.edu/gbdb/hg19/gnomAD/pLI/pliByGene.bb

## [2.0.3](https://github.com/GMOD/bed-js/compare/v2.0.2...v2.0.3) (2020-07-09)

- Use pre-generated pegjs parser for smaller bundle size

<a name="2.0.2"></a>

## [2.0.2](https://github.com/GMOD/bed-js/compare/v2.0.1...v2.0.2) (2019-11-12)

- Small autoSql grammar improvements e.g. allow \_ in autoSql names (for
  `_mouseover` from ucsc)

<a name="2.0.1"></a>

## [2.0.1](https://github.com/GMOD/bed-js/compare/v2.0.0...v2.0.1) (2019-11-03)

- Add fix for names that contain underscores

# [2.0.0](https://github.com/GMOD/bed-js/compare/v1.0.4...v2.0.0) (2019-04-15)

### Major changes

- API now processes just text lines with the parseLine method
- Remove snake case of results
- Returned values match autoSql very faithfully and uses the naming from UCSC
  e.g. exact strings from autoSql {chrom, chromStart, chromEnd}
- Accepts a opts.uniqueId for the parseLine method which adds this to the
  featureData
- Parses the default BED schema with a defaultBedSchema.as autoSql definition
  instead of a separate method

## [1.0.4](https://github.com/GMOD/bed-js/compare/v1.0.3...v1.0.4) (2019-04-14)

- Changed parseBedText to accept an Options argument with offset and optionally
  a uniqueId

## [1.0.3](https://github.com/GMOD/bed-js/compare/v1.0.2...v1.0.3) (2019-04-02)

- Fix usage of autoSql
- Use commonjs2 target of the webpack library build

## [1.0.2](https://github.com/GMOD/bed-js/compare/v1.0.1...v1.0.2) (2019-04-02)

- Fixed dist package on npm

## [1.0.1](https://github.com/GMOD/bed-js/compare/v1.0.0...v1.0.1) (2019-04-02)

- Added BED12 support
- Improved documentation
- Fixed babel loader for webpack

# 1.0.0 (2019-02-22)

- Initial version with autoSql, BED support
- Default autoSql types compiled into module with webpack
