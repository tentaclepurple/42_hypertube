export function parsedEditError(errorResponse: any): Record<string, string> | string[]{
    try {
        const errorData = typeof errorResponse === 'string' ? JSON.parse(errorResponse) : errorResponse;
        if  (typeof errorData.detail === 'string') {
            return { Error: errorData.detail };
        }
        if(errorData.detail && Array.isArray(errorData.detail)) {
            return errorData.detail.reduce((acc: Record<string, string>, error: any) => {
                const field =  error.loc[1];
                acc[field] = error.msg;
                return acc;
            }, {});
        }
        return ['Unknown validation error'];
    } catch (err) {
        console.log('Error parsing error response:', err);
        return ['Error parsing error response'];
    }
}

export function parsedError(errorResponse: any): string[] {
    try {
        const errorData = typeof errorResponse === 'string' ? JSON.parse(errorResponse) : errorResponse;
        if(errorData.detail && Array.isArray(errorData.detail)) {
            return errorData.detail.map((error: any) => error.msg);
        }
        return ['Unknown validation error message'];
    } catch (err) {
        console.log(' Error parsing error message response:', err);
        return ['Error parsing error message response'];
    }
}
