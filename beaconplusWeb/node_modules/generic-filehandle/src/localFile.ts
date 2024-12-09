import fs from 'fs'
import { Buffer } from 'buffer'
import { promisify } from 'es6-promisify'
import { GenericFilehandle, FilehandleOptions } from './filehandle'

const fsOpen = fs && promisify(fs.open)
const fsRead = fs && promisify(fs.read)
const fsFStat = fs && promisify(fs.fstat)
const fsReadFile = fs && promisify(fs.readFile)
const fsClose = fs && promisify(fs.close)

export default class LocalFile implements GenericFilehandle {
  private fd?: any
  private filename: string

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public constructor(source: string, opts: FilehandleOptions = {}) {
    this.filename = source
  }

  private getFd(): any {
    if (!this.fd) {
      this.fd = fsOpen(this.filename, 'r')
    }
    return this.fd
  }

  public async read(
    buffer: Buffer,
    offset = 0,
    length: number,
    position = 0,
  ): Promise<{ bytesRead: number; buffer: Buffer }> {
    const fetchLength = Math.min(buffer.length - offset, length)
    const ret = await fsRead(
      await this.getFd(),
      buffer,
      offset,
      fetchLength,
      position,
    )
    return { bytesRead: ret, buffer }
  }

  public async readFile(): Promise<Buffer>
  public async readFile(options: BufferEncoding): Promise<string>
  public async readFile<T extends undefined>(
    options:
      | Omit<FilehandleOptions, 'encoding'>
      | (Omit<FilehandleOptions, 'encoding'> & { encoding: T }),
  ): Promise<Buffer>
  public async readFile<T extends BufferEncoding>(
    options: Omit<FilehandleOptions, 'encoding'> & { encoding: T },
  ): Promise<string>
  public async readFile(
    options?: FilehandleOptions | BufferEncoding,
  ): Promise<Buffer | string> {
    return fsReadFile(this.filename, options)
  }
  // todo memoize
  public async stat(): Promise<any> {
    return fsFStat(await this.getFd())
  }

  public async close(): Promise<void> {
    return fsClose(await this.getFd())
  }
}
