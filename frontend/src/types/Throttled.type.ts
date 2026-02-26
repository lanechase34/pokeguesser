import { z } from 'zod';

export const ThrottledResponseSchema = z.object({
    detail: z.string(),
});
