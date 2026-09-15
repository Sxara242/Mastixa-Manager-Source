package gr.mastixa.manager;

/** Marks validation text that was deliberately localized at the Android UI boundary. */
final class UiValidationException extends IllegalArgumentException {
    UiValidationException(String message) {
        super(message);
    }
}
