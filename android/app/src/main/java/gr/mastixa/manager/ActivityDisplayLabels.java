package gr.mastixa.manager;

/** Presentation labels only; canonical activity values remain unchanged in storage. */
final class ActivityDisplayLabels {
    private ActivityDisplayLabels() {}

    static String label(String value, boolean english) {
        if (!english || value == null) return value;
        return switch (value) {
            case "Πότισμα" -> "Irrigation";
            case "Λίπανση" -> "Fertilization";
            case "Προγραμματισμένη" -> "Planned";
            case "Ολοκληρώθηκε" -> "Completed";
            case "Ακυρώθηκε" -> "Cancelled";
            default -> value;
        };
    }
}
