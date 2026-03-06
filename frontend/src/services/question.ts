import type { GuessResponse } from 'types/Guess.type';
import { GuessResponseSchema } from 'types/Guess.type';
import type { Question } from 'types/Question.type';
import { QuestionResponseSchema } from 'types/Question.type';
import { APIError } from 'utils/apiError';
import { safeJson } from 'utils/safeJson';

export function questionService() {
    return {
        /**
         * GET /question
         * Get the daily question
         *
         * @returns {id: daily pokemon id, date: today's date}
         */
        async fetchTodaysQuestion(): Promise<Question> {
            const response = await fetch('/pokeguesser/api/v1/question', {
                method: 'GET',
            });

            if (response.status === 429) {
                throw new APIError('Too many requests. Please wait.', 429);
            }

            // Validate the response data
            const json = await safeJson(response);
            const parsed = QuestionResponseSchema.safeParse(json);

            if (!parsed.success) {
                throw new APIError('Invalid response format', response.status);
            }

            const result = parsed.data;
            return result;
        },

        /**
         * POST /guess
         * Submit an answer to the daily question
         *
         * @guess (string) the user's guess
         * @returns parsed and validated guess response
         */
        async submitGuess(guess: string): Promise<GuessResponse> {
            const formBody = new URLSearchParams();
            formBody.append('guess', guess);

            const response = await fetch('/pokeguesser/api/v1/guess', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formBody.toString(),
            });

            // Validate the response
            const json = await safeJson(response);
            const parsed = GuessResponseSchema.safeParse(json);

            if (!parsed.success) {
                throw new Error(`Unexpected response format: ${parsed.error.message}`);
            }

            return parsed.data;
        },
    };
}
