import type { UseToastReturn } from 'hooks/useToast';
import useToast from 'hooks/useToast';
import { useState } from 'react';
import type { GuessResponse } from 'types/Guess.type';
import { validateGuess } from 'validators/validateGuess';

type SubmitGuessFn = (guess: string) => Promise<GuessResponse>;

interface UseGuessFormReturn {
    guess: string;
    /** True after a failed submission, cleared when the input changes */
    hasValidationError: boolean;
    /** Used to imperatively show validation messages */
    validationToast: UseToastReturn;
    /** Validates and submits the guess, shows a toast on failure */
    handleSubmit: () => Promise<void>;
    handleChange: (value: string) => void;
}

/**
 * Manages form state and submission logic for the Pokémon guess input.
 *
 * Validates the current guess against the schema before submission.
 * On failure, shows a validation toast and flags the input as errored.
 * On success, delegates to the provided `submitGuess` callback and resets the input.
 * Input changes clear the validation error state regardless of outcome.
 *
 * @param submitGuess - Async callback that submits a validated guess string to the API.
 * @returns Form state and handlers for the guess input.
 */
export default function useGuessForm(submitGuess: SubmitGuessFn): UseGuessFormReturn {
    const [guess, setGuess] = useState<string>('');
    const validationToast = useToast();
    const [hasValidationError, setHasValidationError] = useState<boolean>(false);

    async function handleSubmit(): Promise<void> {
        const result = validateGuess.safeParse({ guess });
        if (!result.success) {
            const msg = result.error.issues[0].message ?? 'Invalid input.';
            validationToast.show(msg);
            setHasValidationError(true);
            return;
        }
        await submitGuess(guess);
        setGuess('');
    }

    function handleChange(value: string): void {
        setGuess(value);
        validationToast.dismiss();
        setHasValidationError(false);
    }

    return { guess, hasValidationError, validationToast, handleSubmit, handleChange };
}
