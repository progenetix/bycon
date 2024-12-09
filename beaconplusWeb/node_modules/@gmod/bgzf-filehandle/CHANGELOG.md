# v1.4.6

- Add explicit 'buffer' import

# v1.4.5

- Bump generic-filehandle 2->3

# v1.4.4

- Publish src directory for better source maps

# 1.4.3

- Add optimization to avoid data copying during unzip operations

# 1.4.2

- Make nodeUnzip return `Promise<Buffer>`

# 1.4.1

- Add typescript and ESM build to module

# 1.4.0

- Use "browser" field in package.json to choose node vs pako unzip

# v1.3.4

- Improve gzip error message

# v1.3.3

- Bugfix for unzipChunkSize

# v1.3.2

- Bugfix for unzipChunkSize

# v1.3.1

- Create unzipChunkSize

# v1.3.0

- Improved build system
- Create unzipChunk

# v1.2.3

- Fix babel runtime

# v1.2.2

- Change util.promisify->es6-promisify

# v1.2.1

- Fix pako unzip in browser

# v1.2.0

- Add tests for unzip

# v1.1.0

- Initial nodejs package
- Work with bgzip indexed fasta files
