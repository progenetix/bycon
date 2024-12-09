export declare class BamError extends Error {
}
/** Error caused by encountering a part of the BAM spec that has not yet been implemented */
export declare class BamUnimplementedError extends Error {
}
/** An error caused by malformed data.  */
export declare class BamMalformedError extends BamError {
}
/**
 * An error caused by attempting to read beyond the end of the defined data.
 */
export declare class BamBufferOverrunError extends BamMalformedError {
}
/**
 * An error caused by data being too big, exceeding a size limit.
 */
export declare class BamSizeLimitError extends BamError {
}
/**
 * An invalid argument was supplied to a bam-js method or object.
 */
export declare class BamArgumentError extends BamError {
}
