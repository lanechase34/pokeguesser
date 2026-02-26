import { z } from 'zod';

import { ThrottledResponseSchema } from './Throttled.type';

/**
 * Hints are given on incorrect guesses
 */
const Hint1Schema = z.object({
    Type1: z.string(),
    Type2: z.string(),
});

const Hint2Schema = z.object({
    Generation: z.string(),
});

const HintSchema = z.union([Hint1Schema, Hint2Schema]);

const IncorrectResponseSchema = z.object({
    correct: z.literal(false),
    attempt: z.number(),
    attempts_remaining: z.number(),
    hint: HintSchema,
});

/**
 * Correct response will contain the pokemon's true information
 */
const CorrectResponseSchema = z.object({
    correct: z.literal(true),
    answer: z.object({
        id: z.number(),
        name: z.string(),
        number: z.number(),
        sprite: z.string(),
        type1: z.string(),
        type2: z.string(),
    }),
    attempt: z.number(),
});

export const GuessResponseSchema = z.union([CorrectResponseSchema, IncorrectResponseSchema, ThrottledResponseSchema]);

export type GuessResponse = z.infer<typeof GuessResponseSchema>;
