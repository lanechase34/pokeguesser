type ToastType = 'warning' | 'error' | 'success';

interface ToastProps {
    /** Controls the color and styling of the toast */
    type: ToastType;
    /** The main heading shown in bold at the top of the toast */
    title: string;
    /** The descriptive message body shown below the title */
    body: string;
    /** Callback fired when the user clicks the dismiss button */
    onDismiss: () => void;
}

/**
 * Displays a dismissible notification toast.
 *
 * @param type - Visual style variant: 'warning' (yellow), 'error' (red), 'success' (green)
 * @param title - Bold heading text
 * @param body - Descriptive message text
 * @param onDismiss - Called when the user clicks X to dismiss
 */
export default function Toast({ type, title, body, onDismiss }: ToastProps) {
    return (
        <div className={`toast toast-${type}`}>
            <div className="toast-message">
                <span className="toast-title">{title}</span>
                <span className="toast-body">{body}</span>
            </div>
            <button className="toast-dismiss" onClick={onDismiss}>
                X
            </button>
        </div>
    );
}
