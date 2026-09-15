package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.text.InputType;
import android.view.*;
import android.widget.*;
import java.util.*;

/** Always-visible local sign-in and initial profile setup. */
public final class WelcomeActivity extends Activity {
    private LinearLayout body;
    private String language="el", selectedId;
    private boolean creating, busy;
    private EditText profileName,username,password,confirmation;
    private TextView error;
    private java.util.List<ProfileStore.Profile> profiles;
    private String t(String el,String en) { return language.equals("en") ? en : el; }
    private int dp(int n) { return (int)(getResources().getDisplayMetrics().density*n); }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        if(UserSession.valid(this)) {
            startActivity(new Intent(this,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP));finish();return;
        }
        UserSession.clear();
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        try(var registry=new ProfileStore(this)) { profiles=registry.profiles(); }
        selectedId=getPreferences(MODE_PRIVATE).getString("lastProfile",profiles.isEmpty()?"":profiles.get(0).id());
        for(var profile:profiles) if(profile.id().equals(selectedId)) language=profile.language();
        if(state!=null) { language=state.getString("language",language); selectedId=state.getString("profile",selectedId); creating=state.getBoolean("creating"); }
        creating=creating || profiles.isEmpty(); render();
        if(android.os.Build.VERSION.SDK_INT>=33)
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT,this::goBack);
    }
    @Override protected void onSaveInstanceState(Bundle state) {
        state.putString("language",language); state.putString("profile",selectedId); state.putBoolean("creating",creating); super.onSaveInstanceState(state);
    }
    private void label(String value,int size) {
        TextView text=new TextView(this); text.setText(value); text.setTextSize(size); text.setTextColor(Color.rgb(30,62,49));
        text.setPadding(0,dp(10),0,dp(8)); body.addView(text);
    }
    private EditText input(String caption,boolean secret) {
        label(caption,15); EditText edit=new EditText(this); edit.setSingleLine(true); edit.setTextSize(18); edit.setContentDescription(caption);
        edit.setInputType(InputType.TYPE_CLASS_TEXT | (secret?InputType.TYPE_TEXT_VARIATION_PASSWORD:InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS));
        edit.setSaveEnabled(false); edit.setImportantForAutofill(View.IMPORTANT_FOR_AUTOFILL_NO);
        edit.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(secret?128:60)});
        edit.setMinimumHeight(dp(54)); body.addView(edit,new LinearLayout.LayoutParams(-1,-2)); return edit;
    }
    private void button(String title,Runnable callback) {
        Button button=new Button(this); button.setText(title); button.setAllCaps(false); button.setTextSize(17); button.setMinHeight(dp(54));
        var params=new LinearLayout.LayoutParams(-1,-2); params.topMargin=dp(14); body.addView(button,params); button.setOnClickListener(v->{if(!busy) callback.run();});
    }
    private void render() {
        ScrollView scroll=new ScrollView(this); scroll.setFillViewport(true); scroll.setBackgroundColor(Color.rgb(245,247,240));
        body=new LinearLayout(this); body.setOrientation(LinearLayout.VERTICAL); body.setPadding(dp(24),dp(24),dp(24),dp(24)); scroll.addView(body);
        scroll.setOnApplyWindowInsetsListener((v,insets)-> {
            if(android.os.Build.VERSION.SDK_INT>=30) {
                var bars=insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.ime()); v.setPadding(bars.left,bars.top,bars.right,bars.bottom);
            } else v.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
            return insets;
        });
        setContentView(scroll); label("MASTIXA",28);
        label(t("Επιλογή γλώσσας","Language"),15);
        Spinner languages=new Spinner(this); languages.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{"Ελληνικά","English"}));
        languages.setMinimumHeight(dp(52)); languages.setSelection(language.equals("en")?1:0); body.addView(languages,new LinearLayout.LayoutParams(-1,-2));
        languages.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            public void onNothingSelected(AdapterView<?> parent) {}
            public void onItemSelected(AdapterView<?> parent,View view,int position,long id) {
                String next=position==1?"en":"el";
                if(!next.equals(language) && !busy) { language=next; render(); }
            }
        });
        label(creating?t("Δημιουργία προφίλ","Create profile"):t("Καλώς ήρθες","Welcome back"),26);
        if(creating) {
            label(profiles.isEmpty()?t("Το πρώτο προφίλ θα κρατήσει τα υπάρχοντα δεδομένα αυτής της συσκευής.","The first profile will keep this device’s existing data."):t("Κάθε νέο προφίλ ξεκινά με ξεχωριστά, κενά δεδομένα.","Each new profile starts with its own empty data."),16);
            profileName=input(t("Όνομα προφίλ","Profile name"),false);
        } else {
            label(t("Επιλογή προφίλ","Choose profile"),15);
            Spinner chooser=new Spinner(this); chooser.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,profiles));
            int index=0; for(int i=0;i<profiles.size();i++) if(profiles.get(i).id().equals(selectedId)) index=i;
            selectedId=profiles.get(index).id(); chooser.setMinimumHeight(dp(52)); chooser.setSelection(index); body.addView(chooser,new LinearLayout.LayoutParams(-1,-2));
            chooser.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
                public void onNothingSelected(AdapterView<?> parent) {}
                public void onItemSelected(AdapterView<?> parent,View view,int position,long id) {
                    var selected=profiles.get(position);
                    if(!selected.id().equals(selectedId) && !busy) { selectedId=selected.id(); language=selected.language(); render(); }
                }
            });
        }
        username=input(t("Όνομα χρήστη","Username"),false);
        password=input(t("Κωδικός","Password"),true);
        if(creating) {
            label(t("Όνομα χρήστη: 3–40 λατινικοί χαρακτήρες, αριθμοί ή . _ -\nΚωδικός: 8–128 χαρακτήρες.","Username: 3–40 Latin letters, numbers or . _ -\nPassword: 8–128 characters."),14);
            confirmation=input(t("Επιβεβαίωση κωδικού","Confirm password"),true);
        }
        error=new TextView(this); error.setTextColor(Color.rgb(160,35,35)); body.addView(error);
        button(creating?t("Δημιουργία και είσοδος","Create and sign in"):t("Είσοδος","Sign in"),this::submit);
        if(!profiles.isEmpty()) button(creating?t("Πίσω στην είσοδο","Back to sign in"):t("Νέο προφίλ","New profile"),()->{creating=!creating;render();});
        label(t("Τοπικοί λογαριασμοί σε αυτή τη συσκευή. Τα στοιχεία σύνδεσης PC δεν μεταφέρονται με το ZIP αγροτεμαχίων.","Local accounts on this device. PC credentials are not included in field export ZIPs."),14);
    }
    private void setEnabled(View view,boolean enabled) { view.setEnabled(enabled); if(view instanceof ViewGroup group) for(int i=0;i<group.getChildCount();i++) setEnabled(group.getChildAt(i),enabled); }
    private void submit() {
        String user=username.getText().toString(),name=creating?profileName.getText().toString():"",lang=language,id=selectedId;
        char[] secret=password.getText().toString().toCharArray();
        if(creating && !password.getText().toString().equals(confirmation.getText().toString())) { Arrays.fill(secret,'\0'); error.setText(t("Οι κωδικοί δεν ταιριάζουν.","Passwords do not match.")); return; }
        if(secret.length==0 || user.trim().isEmpty()) { Arrays.fill(secret,'\0'); error.setText(t("Συμπλήρωσε όνομα χρήστη και κωδικό.","Enter your username and password.")); return; }
        boolean create=creating; busy=true; setRequestedOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_LOCKED); setEnabled(body,false); error.setText(t("Παρακαλώ περίμενε…","Please wait…"));
        new Thread(()-> {
            ProfileStore.Profile result=null; String problem=null;
            try(var registry=new ProfileStore(this)) {
                result=create?registry.create(name,user,secret,lang):registry.authenticate(id,user,secret,lang);
                if(result==null) problem=t("Λάθος όνομα χρήστη ή κωδικός.","Incorrect username or password.");
            } catch(android.database.sqlite.SQLiteConstraintException ex) { problem=t("Υπάρχει ήδη αυτό το όνομα προφίλ ή χρήστη.","That profile name or username already exists."); }
            catch(IllegalArgumentException ex) { problem=new AppLanguage(this,lang).t(ex.getMessage()); }
            catch(Exception ex) { problem=t("Η ενέργεια απέτυχε. Δοκίμασε ξανά.","The action failed. Please try again."); }
            finally { Arrays.fill(secret,'\0'); }
            var authenticated=result; var message=problem;
            runOnUiThread(()-> {
                if(isFinishing() || isDestroyed()) return;
                busy=false; setEnabled(body,true); password.setText(""); if(create) confirmation.setText("");
                setRequestedOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED);
                if(authenticated==null) { error.setText(message); return; }
                UserSession.signIn(authenticated); getPreferences(MODE_PRIVATE).edit().putString("lastProfile",authenticated.id()).apply();
                startActivity(new Intent(this,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK)); finish();
            });
        },"profile-auth").start();
    }
    private void goBack() { if(busy) return; if(creating && !profiles.isEmpty()) { creating=false; render(); } else finish(); }
    // API 33+ uses the platform callback; this is the API 26–32 fallback.
    @android.annotation.SuppressLint("GestureBackNavigation")
    @Override public void onBackPressed() { goBack(); }
}
