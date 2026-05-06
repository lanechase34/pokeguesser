import { z } from 'zod';

export const QuestionResponseSchema = z.object({
    id: z.number().nonnegative(),
    date: z.iso.datetime({ local: true }),
});

export type Question = z.infer<typeof QuestionResponseSchema>;
