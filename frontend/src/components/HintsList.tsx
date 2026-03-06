interface HintsListProps {
    hints: string[];
}

/**
 * Renders an unordered list where each hint is prefixed with a "Hint N:" label.
 * Returns `null` if the hints array is empty.
 *
 * @param hints - Array of hint strings to display.
 * @returns A `<ul>` of labeled hint items, or `null` if there are no hints.
 */
export default function HintsList({ hints }: HintsListProps) {
    if (!hints.length) return null;
    return (
        <ul className="hints-list">
            {hints.map((hint, i) => (
                <li key={hint} className="hint-item">
                    <span className="hint-label">Hint {i + 1}:</span> {hint}
                </li>
            ))}
        </ul>
    );
}
