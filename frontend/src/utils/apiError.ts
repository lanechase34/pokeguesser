/**
 * Custom error to support what status code caused the error
 */
export class APIError extends Error {
    public readonly statusCode: number;
    public readonly name: string;
    public readonly data: string;

    constructor(message: string, statusCode = 500, data = '') {
        super(message); // Pass the message to the parent Error constructor

        Object.setPrototypeOf(this, APIError.prototype);

        this.name = 'APIError';
        this.statusCode = statusCode;
        this.data = data;
    }
}
