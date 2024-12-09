## [3.1.2](https://github.com/GMOD/generic-filehandle/compare/v3.1.1...v3.1.2) (2024-3-4)



- Fix response.buffer deprecation warning (always use response.arrayBuffer and Buffer.from)

## [3.1.1](https://github.com/GMOD/generic-filehandle/compare/v3.1.0...v3.1.1) (2023-09-09)

- Use bind to make sure fetch has the right scope

# [3.1.0](https://github.com/GMOD/generic-filehandle/compare/v3.0.1...v3.1.0) (2023-08-28)

- Look for fetch in globalThis

## [3.0.1](https://github.com/GMOD/generic-filehandle/compare/v3.0.0...v3.0.1) (2022-12-17)

- Fix sourceMap

# [3.0.0](https://github.com/GMOD/generic-filehandle/compare/v2.2.3...v3.0.0) (2022-07-18)

- Remove the utility that converts a RemoteFile into a LocalFile when a file:/// is passed in

## [2.2.3](https://github.com/GMOD/generic-filehandle/compare/v2.2.2...v2.2.3) (2022-05-19)

### Features

- explicit buffer import ([#102](https://github.com/GMOD/generic-filehandle/issues/102)) ([a9223d6](https://github.com/GMOD/generic-filehandle/commit/a9223d65c4f19c59e86c0959c0512f2f83fd6ab0))

* Explicitly import Buffer to try to help deployment on some bundlers

## [2.2.2](https://github.com/GMOD/generic-filehandle/compare/v2.2.1...v2.2.2) (2021-12-14)

- Add esm module build with less babelification for smaller bundle size

## [2.2.1](https://github.com/GMOD/generic-filehandle/compare/v2.2.0...v2.2.1) (2021-10-03)

- Make this.url a protected instead of private field

# [2.2.0](https://github.com/GMOD/generic-filehandle/compare/v2.1.0...v2.2.0) (2021-09-22)

### Features

- resolve empty for node-specific modules in browser context ([#88](https://github.com/GMOD/generic-filehandle/issues/88)) ([044ab0f](https://github.com/GMOD/generic-filehandle/commit/044ab0f581c6937f98e309855e50f5102c0a94e8))

* Use "browser" field of package.json to hide localFile import of 'fs' instead of hiding behind webpack flag. Thanks to @manzt for contributing! (#88)

# [2.1.0](https://github.com/GMOD/generic-filehandle/compare/v2.0.3...v2.1.0) (2021-03-10)

- Refetch with cache:'reload' header on CORS error to bypass Chrome cache pollution

## [2.0.3](https://github.com/GMOD/generic-filehandle/compare/v2.0.2...v2.0.3) (2020-06-05)

- Fix ability to supply things like Authorization token to the constructor

example syntax

```
const f = new RemoteFile("http://yourwebsite/file.bam", {
  overrides: {
    headers: {
      Authorization: "Basic YWxhZGRpbjpvcGVuc2VzYW1l",
    },
  },
});
```

## [2.0.2](https://github.com/GMOD/generic-filehandle/compare/v2.0.1...v2.0.2) (2020-04-07)

- Upgrade dependencies

## [2.0.1](https://github.com/GMOD/generic-filehandle/compare/v2.0.0...v2.0.1) (2019-10-25)

- Fix the typescript typings for stat and some other things

# [2.0.0](https://github.com/GMOD/generic-filehandle/compare/v1.0.9...v2.0.0) (2019-06-05)

- Update to use Node.js return type e.g. {buffer,bytesRead} instead of just bytesRead

## [1.0.9](https://github.com/GMOD/generic-filehandle/compare/v1.0.8...v1.0.9) (2019-05-01)

- Add ability to read a fetch response's Body().buffer() instead of Body.arrayBuffer() that is normally returned
- Fix issue with using un-polyfilled fetch

## [1.0.8](https://github.com/GMOD/generic-filehandle/compare/v1.0.7...v1.0.8) (2019-04-17)

- Properly added typescript type declaration files to the distribution

## [1.0.7](https://github.com/GMOD/generic-filehandle/compare/v1.0.6...v1.0.7) (2019-04-16)

- Remove polyfill of fetch, now uses "globalThis" fetch or supply opts.fetch to the constructor of RemoteFile (@rbuels, pull #8)
- Translates file:// URL to LocalFile in the implementation (@rbuels, pull #7)
- Allow adding fetch overrides to the constructor of RemoteFile
- Make LocalFile lazily evaluate opening the file until usage

## [1.0.6](https://github.com/GMOD/generic-filehandle/compare/v1.0.5...v1.0.6) (2019-04-15)

- Added documentation about the Options object
- Added encoding option to the Options for readFile which can return text if specified as utf8 or you can also directly call filehandle.readFile('utf8')

## [1.0.5](https://github.com/cmdcolin/generic-filehandle/compare/v1.0.4...v1.0.5) (2019-04-12)

- Added BlobFile class, implementation (thanks @garrettjstevens!)

## [1.0.4](https://github.com/cmdcolin/node-filehandle/compare/v1.0.2...v1.0.4) (2019-04-11)

- Add @types/node for typescript

## [1.0.3](https://github.com/cmdcolin/node-filehandle/compare/v1.0.2...v1.0.3) (2019-04-11)

- Downgrade quick-lru for node 6

## [1.0.2](https://github.com/cmdcolin/node-filehandle/compare/v1.0.1...v1.0.2) (2019-04-10)

- Fix usage of fetch headers
- Add overrides parameter to options

## 1.0.1 (2019-04-10)

- Fix some typescript definitions

## 1.0.0

- Initial implementation of a filehandle object with local and remote support
