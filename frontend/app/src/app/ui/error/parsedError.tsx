type ErrorDetail = {
    loc: string[];
    msg: string;
};

type ErrorResponse = {
    detail: string | ErrorDetail[];
};

export function parsedEditError(errorResponse: ErrorResponse | string): Record<string, string> | string[]{
    try {
        const errorData = typeof errorResponse === 'string' ? JSON.parse(errorResponse) : errorResponse;
        if  (typeof errorData.detail === 'string') {
            return { Error: errorData.detail };
        }
        if(errorData.detail && Array.isArray(errorData.detail)) {
            return errorData.detail.reduce((acc: Record<string, string>, error: ErrorDetail) => {
                const field =  error.loc[1];
                acc[field] = error.msg;
                return acc;
            }, {});
        }
        return ['Unknown validation error'];
    } catch {
        return ['Error parsing error response'];
    }
}

export function parsedError(errorResponse: ErrorResponse | string): string[] {
    try {
        const errorData = typeof errorResponse === 'string' ? JSON.parse(errorResponse) : errorResponse;
        if (typeof errorData.detail === 'string') {
            return [errorData.detail];
        }
        if(errorData.detail && Array.isArray(errorData.detail)) {
            return errorData.detail.map((error: ErrorDetail) => error.msg);
        }
        return ['Unknown validation error message'];
    } catch {
        return ['Error parsing error message response'];
    }
}
