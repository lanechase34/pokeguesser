import { z } from 'zod';

/**
 * Hints are given on incorrect guesses
 */
const Hint1Schema = z.object({
    Type1: z.string(),
    Type2: z.string(),
});

const Hint2Schema = z.object({
    Generation: z.number(),
});

const HintSchema = z.union([Hint1Schema, Hint2Schema]);

/**
 * Correct answer pokemon details
 */
const AnswerSchema = z.object({
    id: z.number(),
    name: z.string(),
    number: z.number(),
    sprite: z.string(),
    type1: z.string(),
    type2: z.string(),
});

/**
 * Correct t/f with answer
 * Happens when guess is correct, or user out of attempts
 */
const GameOverResponseSchema = z.object({
    correct: z.boolean(),
    answer: AnswerSchema,
    attempt: z.number(),
});

const IncorrectResponseSchema = z.object({
    correct: z.literal(false),
    attempt: z.number(),
    attempts_remaining: z.number(),
    hint: HintSchema,
});

export const GuessResponseSchema = z.union([GameOverResponseSchema, IncorrectResponseSchema]);
export type GuessResponse = z.infer<typeof GuessResponseSchema>;
export type GameOverResponse = z.infer<typeof GameOverResponseSchema>;
