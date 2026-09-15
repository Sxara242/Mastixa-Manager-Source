package gr.mastixa.manager;

import android.content.Context;
import org.json.JSONObject;
import java.nio.charset.StandardCharsets;
import java.util.Iterator;

/** UI text only. User-entered farm values must never be passed to this translator. */
final class AppLanguage {
    private final JSONObject translations=new JSONObject();
    final String code;

    AppLanguage(Context context,String language) {
        code=language;
        try {
            if(code.equals("en")) {
                merge(context,"en.json");
                merge(context,"en_phase16j.json");
            } else {
                merge(context,"el_phase16j.json");
            }
        } catch(Exception error) { throw new IllegalStateException("Missing language pack for "+code,error); }
    }

    private void merge(Context context,String asset) throws Exception {
        JSONObject source;
        try(var input=context.getAssets().open(asset)) {
            source=new JSONObject(new String(LocalBackup.read(input),StandardCharsets.UTF_8));
        }
        for(Iterator<String> keys=source.keys();keys.hasNext();) {
            String key=keys.next(); translations.put(key,source.get(key));
        }
    }

    String t(String value) {
        if(value==null) return null;
        if(translations.has(value)) return translations.optString(value,value);
        for(String suffix:new String[]{"  ›","\nΥπό κατασκευή"," · Υπό κατασκευή"}) {
            if(value.endsWith(suffix)) {
                String tail=suffix.equals("  ›") ? suffix : code.equals("en") ? (suffix.startsWith("\n")?"\nUnder construction":" · Under construction") : suffix;
                return t(value.substring(0,value.length()-suffix.length()))+tail;
            }
        }
        if(value.startsWith("Κατηγορία: ")) return (code.equals("en")?"Category: ":"Κατηγορία: ")+t(value.substring(11));
        return value;
    }
}
