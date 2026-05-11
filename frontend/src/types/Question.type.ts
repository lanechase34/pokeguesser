import { z } from 'zod';

export const QuestionResponseSchema = z.object({
    id: z.number().nonnegative(),
    date: z.iso.date(),
});

export type Question = z.infer<typeof QuestionResponseSchema>;
