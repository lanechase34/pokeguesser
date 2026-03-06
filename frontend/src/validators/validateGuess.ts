import { z } from 'zod';

export const validateGuess = z.object({
    guess: z
        .string()
        .min(3, 'Please enter a Pokémon name.')
        .max(50, 'That name is too long.')
        .regex(/^[a-zA-Z0-9\s\-.]+$/, 'Only letters, numbers, hyphens, and spaces are allowed.'),
});
