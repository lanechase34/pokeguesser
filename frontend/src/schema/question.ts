import { safeJson } from 'utils/safeJson';
import { APIError } from 'utils/apiError';
import { QuestionResponseSchema } from 'types/Question.type';
import type { Question } from 'types/Question.type';

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
    };
}
