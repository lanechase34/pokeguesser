import type { GuessResponse } from 'types/Guess.type';

type Hint = Extract<GuessResponse, { hint: unknown }>['hint'];

/**
 * Formats the incoming hint array to text
 * @param hint Hint array returned from API
 * @returns Text corresponding to the hint
 */
export function formatHint(hint: Hint): string {
    if ('Type1' in hint) {
        return hint.Type2
            ? `This Pokémon is ${hint.Type1} / ${hint.Type2} type.`
            : `This Pokémon is ${hint.Type1} type.`;
    }
    if ('Generation' in hint) {
        return `This Pokémon is from Generation ${hint.Generation}.`;
    }
    return 'No hint available.';
}
