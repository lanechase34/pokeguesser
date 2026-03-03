export default function HintsList({ hints }: { hints: string[] }) {
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
