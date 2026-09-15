package gr.mastixa.manager;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.graphics.Color;
import android.graphics.Typeface;
import android.view.View;
import android.view.WindowInsets;
import android.widget.*;
import android.text.InputType;
import java.util.Locale;

public final class MainActivity extends Activity {
    private FarmStore store;
    private LinearLayout content;
    private String currentPage = "Αρχική";
    private ProfileStore.Profile profile;
    private AppLanguage language;
    private String productQuery="";
    private int productFilter=0;
    private String partnerQuery="";
    private int partnerFilter=0;
    private String inventoryQuery="",inventoryItemId=null;
    private boolean inventoryLowOnly=false;
    private String moneyQuery="",moneyYear="";
    private String productionQuery="",productionYear="";
    private String equipmentFilter="",equipmentReminder="";
    private String workQuery="",workYear="",workField="",workWorker="";
    private String activityQuery="",activityYear="",activityCategory="",activityStatus="";
    private final java.util.ArrayList<Bundle> backStack=new java.util.ArrayList<>();
    private ScrollView pageScroll;
    private int pendingScroll=-1;
    private String t(String value) { return language.t(value); }
    private String words(String greek,String english) { return profile.language().equals("en")?english:greek; }
    private void logout() {
        UserSession.clear();
        startActivity(new android.content.Intent(this,WelcomeActivity.class).addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK | android.content.Intent.FLAG_ACTIVITY_CLEAR_TASK)); finish();
    }
    private java.util.LinkedHashSet<String> shortcutOptions() {
        var options=new java.util.LinkedHashSet<String>();
        for(String[] group:PageCatalog.GROUPS) {
            options.add("Κατηγορία: " + group[0]);
            for(int i=1;i<group.length;i++) options.add(group[i]);
        }
        return options;
    }
    private java.util.Set<String> shortcuts() {
        return getSharedPreferences(profile.preferences(),MODE_PRIVATE).getStringSet("shortcuts",java.util.Set.of("Σάρωση OCR","Τοπικό backup"));
    }
    private void customizeShortcuts() {
        String[] options=shortcutOptions().toArray(new String[0]);
        boolean[] checked=new boolean[options.length]; var selected=new java.util.HashSet<>(shortcuts());
        for(int i=0;i<options.length;i++) checked[i]=selected.contains(options[i]);
        new AlertDialog.Builder(this).setTitle(t("Η γρήγορη πρόσβασή μου"))
            .setMultiChoiceItems(java.util.Arrays.stream(options).map(this::t).toArray(String[]::new),checked,(dialog,index,value)-> { if(value) selected.add(options[index]); else selected.remove(options[index]); })
            .setNegativeButton(t("Ακύρωση"),null)
            .setPositiveButton(t("Αποθήκευση"),(dialog,which)-> {
                getSharedPreferences(profile.preferences(),MODE_PRIVATE).edit().putStringSet("shortcuts",selected).apply(); showHome();
            }).show();
    }
    private byte[] pendingRestore;
    private java.io.File recoveryFile() { return new java.io.File(getFilesDir(),profile.recovery()); }
    private void backupMessage(String message) { new AlertDialog.Builder(this).setMessage(t(message)).setPositiveButton(t("Εντάξει"),null).show(); }
    @Override protected void onActivityResult(int request, int result, android.content.Intent data) {
        super.onActivityResult(request,result,data);
        if(store==null || !UserSession.valid(this) || profile==null || !UserSession.profile.id().equals(profile.id())) { if(store!=null) logout(); return; }
        if(result!=RESULT_OK || data==null || data.getData()==null) return;
        try {
            if(request>=110&&request<=118){documentResult(request,data.getData());return;}
            if(request==101) {
                byte[] bytes=LocalBackup.snapshot(store);
                try(java.io.OutputStream out=getContentResolver().openOutputStream(data.getData(),"wt")) {
                    if(out==null) throw new java.io.IOException(); out.write(bytes);
                }
                getSharedPreferences(profile.preferences(),MODE_PRIVATE).edit().putLong("last_exported_backup_at",System.currentTimeMillis()).apply();
                if(currentPage.equals("Dashboard"))showHome();
                backupMessage("Το αντίγραφο αποθηκεύτηκε.");
            } else if(request==102) {
                try(java.io.InputStream in=getContentResolver().openInputStream(data.getData())) { confirmRestore(LocalBackup.read(in)); }
            } else if(request==103) {
                try(java.io.InputStream in=getContentResolver().openInputStream(data.getData())) { confirmCatalogImport(CatalogImport.read(in)); }
            }
        } catch(Exception error) {
            if(request>=110) backupMessage(words("Η ενέργεια εγγράφου δεν ολοκληρώθηκε. Έλεγξε το αρχείο και τον διαθέσιμο χώρο.","Document action failed. Check the file and available storage."));
            else if(request==103) backupMessage(words("Η εισαγωγή δεν ολοκληρώθηκε. Έλεγξε τα δεδομένα ZIP, τις συγκρούσεις και τις συνδεδεμένες εγγραφές.","Import failed. Check ZIP data, conflicting records and linked fields/partners."));
            else backupMessage(words("Η ενέργεια δεν ολοκληρώθηκε. Έλεγξε το αρχείο και τον διαθέσιμο χώρο.","The action did not complete. Check the file and available storage."));
        }
    }
    private boolean readyPage(String page) {
        return ReportStore.PAGES.contains(page) || java.util.Set.of("Dashboard","Ειδοποιήσεις","Έγγραφα Τιμολογίων","Σάρωση OCR","Κλείδωμα Έτους","Μηχανήματα & Συντήρηση","Συντηρήσεις μηχανημάτων","Φυτεύσεις & Δέντρα","Φυτοπροστασία","Εργατικά & Προσωπικό","Προσωπικό","Άρδευση & Λίπανση","Παραγωγή","Πωλήσεις Παραγωγής","Έσοδα","Έξοδα","Αποθήκη & Εφόδια","Προμηθευτές & Αγοραστές","Παραγωγός","Προϊόντα","Αγροτεμάχια","Τοπικό backup","Εισαγωγή από Windows","Διαχείριση δεδομένων","Προφίλ χρηστών","Εμφάνιση & Γλώσσα","Γενικές Ρυθμίσεις","Πρόγραμμα Καλλιέργειας","Ενιαίο Ημερολόγιο").contains(page);
    }
    private void confirmRestore(byte[] bytes) throws Exception {
        int count=LocalBackup.inspect(store,bytes); pendingRestore=bytes;
        new AlertDialog.Builder(this).setTitle(t("Επαναφορά αντιγράφου;"))
            .setMessage(words("Το αρχείο περιέχει " + count + " αγροτεμάχια. Θα αντικαταστήσει ΟΛΑ τα δεδομένα αγροτεμαχίων, παραγωγού, προϊόντων, καλλιεργειών, συνεργατών, αποθήκης, οικονομικών, παραγωγής, πωλήσεων άρδευσης/λίπανσης, φυτοπροστασίας και εργατικών/προσωπικού φυτεύσεων και μηχανημάτων/συντήρησης, τιμολογίων/συνημμένων και κλειδωμάτων έτους του προφίλ. Τα παλιά αντίγραφα ασφαλείας αδειάζουν όσα νεότερα μητρώα δεν περιλαμβάνουν. Θα κρατηθεί εσωτερικό αντίγραφο.","This file contains " + count + " field(s). It replaces ALL field, producer, product, cultivation, partner, inventory, financial, production, sales irrigation/fertilization, plant protection and labor/workers planting and equipment/maintenance, invoice/attachment and year-lock data in this profile. Older backups clear any newer registries they do not contain. An internal backup will be kept."))
            .setNegativeButton(t("Ακύρωση"),(d,w)->pendingRestore=null)
            .setPositiveButton(t("Επαναφορά"),(d,w)-> {
                try { LocalBackup.restore(store,bytes,recoveryFile()); showHome(); backupMessage("Η επαναφορά ολοκληρώθηκε."); }
                catch(Exception error) { backupMessage("Η επαναφορά απέτυχε. Οι τρέχουσες καταχωρίσεις δεν αντικαταστάθηκαν."); }
                finally { pendingRestore=null; }
            }).show();
    }
    private int dp(int value) { return (int)(getResources().getDisplayMetrics().density * value); }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        profile=UserSession.valid(this)?UserSession.profile:null;
        if(profile==null) { logout(); return; }
        language=new AppLanguage(this,profile.language());
        store = new FarmStore(this,profile.database());
        if(state!=null) {
            restorePage(state.getBundle("current"));
            var history=state.getParcelableArrayList("history");if(history!=null)for(var value:history)if(value instanceof Bundle b)backStack.add(b);
        }
        showHome();
        if(android.os.Build.VERSION.SDK_INT>=33)getOnBackInvokedDispatcher().registerOnBackInvokedCallback(android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT,this::goBack);
    }
    private Bundle pageState(){
        var state=new Bundle();state.putString("page",currentPage);state.putString("inventoryItem",inventoryItemId);state.putInt("scroll",pageScroll==null?0:pageScroll.getScrollY());state.putString("productQuery",productQuery);state.putInt("productFilter",productFilter);state.putString("partnerQuery",partnerQuery);state.putInt("partnerFilter",partnerFilter);state.putString("inventoryQuery",inventoryQuery);state.putBoolean("inventoryLow",inventoryLowOnly);state.putString("moneyQuery",moneyQuery);state.putString("moneyYear",moneyYear);state.putString("productionQuery",productionQuery);state.putString("productionYear",productionYear);state.putString("activityQuery",activityQuery);state.putString("activityYear",activityYear);state.putString("activityCategory",activityCategory);state.putString("activityStatus",activityStatus);state.putString("workQuery",workQuery);state.putString("workYear",workYear);state.putString("workField",workField);state.putString("workWorker",workWorker);state.putString("equipmentFilter",equipmentFilter);state.putString("equipmentReminder",equipmentReminder);state.putString("dashboardYear",dashboardYear);state.putString("alertKind",alertKind);state.putString("alertQuery",alertQuery);state.putInt("alertSeverity",alertSeverity);state.putString("documentQuery",documentQuery);state.putString("documentYear",documentYear);state.putString("pendingDocument",pendingDocument);state.putString("reportFrom",reportFrom);state.putString("reportTo",reportTo);state.putString("reportField",reportField);state.putString("reportProduct",reportProduct);state.putString("reportBuyer",reportBuyer);return state;
    }
    private void restorePage(Bundle state){
        if(state==null)return;currentPage=state.getString("page","Αρχική");inventoryItemId=state.getString("inventoryItem");pendingScroll=state.getInt("scroll",0);productQuery=state.getString("productQuery","");productFilter=state.getInt("productFilter",0);partnerQuery=state.getString("partnerQuery","");partnerFilter=state.getInt("partnerFilter",0);inventoryQuery=state.getString("inventoryQuery","");inventoryLowOnly=state.getBoolean("inventoryLow",false);moneyQuery=state.getString("moneyQuery","");moneyYear=state.getString("moneyYear","");productionQuery=state.getString("productionQuery","");productionYear=state.getString("productionYear","");activityQuery=state.getString("activityQuery","");activityYear=state.getString("activityYear","");activityCategory=state.getString("activityCategory","");activityStatus=state.getString("activityStatus","");workQuery=state.getString("workQuery","");workYear=state.getString("workYear","");workField=state.getString("workField","");workWorker=state.getString("workWorker","");equipmentFilter=state.getString("equipmentFilter","");equipmentReminder=state.getString("equipmentReminder","");dashboardYear=state.getString("dashboardYear","");alertKind=state.getString("alertKind","");alertQuery=state.getString("alertQuery","");alertSeverity=state.getInt("alertSeverity",-1);documentQuery=state.getString("documentQuery","");documentYear=state.getString("documentYear","");pendingDocument=state.getString("pendingDocument","");reportFrom=state.getString("reportFrom","");reportTo=state.getString("reportTo","");reportField=state.getString("reportField","");reportProduct=state.getString("reportProduct","");reportBuyer=state.getString("reportBuyer","");
    }
    @Override protected void onSaveInstanceState(Bundle state){state.putBundle("current",pageState());state.putParcelableArrayList("history",new java.util.ArrayList<>(backStack));super.onSaveInstanceState(state);}
    // API 33+ uses the platform callback registered in onCreate; legacy devices use this.
    @android.annotation.SuppressLint("GestureBackNavigation")
    @Override public void onBackPressed(){goBack();}
    private void goBack(){
        if(!backStack.isEmpty()){restorePage(backStack.remove(backStack.size()-1));showHome();}
        else if(!currentPage.equals("Αρχική")){currentPage="Αρχική";inventoryItemId=null;pendingScroll=0;showHome();}
        else moveTaskToBack(true);
    }
    private void rememberPage(){backStack.add(pageState());if(backStack.size()>100)backStack.remove(0);}
    private void navigate(String page){
        if(page.equals("Πρόγραμμα Καλλιέργειας")){
            startActivity(new android.content.Intent(this,CropProgramActivity.class));
            return;
        }
        if(page.equals("Ενιαίο Ημερολόγιο")){
            startActivity(new android.content.Intent(this,UnifiedCalendarActivity.class));
            return;
        }
        if(page.equals(currentPage)&&inventoryItemId==null)return;
        if(page.equals("Αρχική"))backStack.clear();else rememberPage();
        currentPage=page;inventoryItemId=null;pendingScroll=0;showHome();
    }
    private void openInventoryItem(String item){
        if(currentPage.equals("Αποθήκη & Εφόδια")&&java.util.Objects.equals(inventoryItemId,item))return;
        rememberPage();currentPage="Αποθήκη & Εφόδια";inventoryItemId=item;pendingScroll=0;showHome();
    }
    private android.graphics.drawable.GradientDrawable surface(int color, int radius) {
        var shape=new android.graphics.drawable.GradientDrawable(); shape.setColor(color); shape.setCornerRadius(dp(radius)); return shape;
    }
    private Button action(String title, Runnable run, boolean primary) {
        Button button=new Button(this); button.setText(t(title)); button.setAllCaps(false); button.setTextSize(16);
        button.setTextColor(primary ? Color.WHITE : Color.rgb(30,62,49));
        button.setBackground(surface(primary ? Color.rgb(35,83,62) : Color.WHITE,14));
        LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,-2); params.topMargin=dp(10); params.bottomMargin=dp(4);
        button.setMinHeight(dp(52)); content.addView(button,params); button.setOnClickListener(v->run.run()); return button;
    }
    private TextView text(String value, int size, boolean bold) {
        return textValue(t(value),size,bold);
    }
    private TextView textValue(String value, int size, boolean bold) {
        TextView view = new TextView(this); view.setText(value); view.setTextSize(size);
        view.setTextColor(Color.rgb(30, 62, 49));
        if (bold) view.setTypeface(null, Typeface.BOLD);
        view.setPadding(0, dp(8), 0, dp(8)); content.addView(view); return view;
    }
    private void showHome() {
        LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(245,247,240));
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        int restoreScroll=pendingScroll>=0?pendingScroll:pageScroll==null?0:pageScroll.getScrollY();pendingScroll=-1;
        ScrollView scroll = new ScrollView(this);pageScroll=scroll;scroll.setFillViewport(true);
        scroll.post(()->scroll.scrollTo(0,restoreScroll));
        scroll.setBackgroundColor(Color.rgb(245,247,240));
        content = new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(24),dp(20),dp(24),dp(24)); scroll.addView(content);
        root.setOnApplyWindowInsetsListener((v, insets) -> {
            if (android.os.Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars());
                v.setPadding(bars.left,bars.top,bars.right,bars.bottom);
            } else {
                v.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
            }
            return insets;
        });
        var toolbar=new LinearLayout(this);toolbar.setGravity(android.view.Gravity.CENTER_VERTICAL);toolbar.setPadding(dp(16),dp(6),dp(16),dp(6));
        if(!currentPage.equals("Αρχική")){
            var back=new Button(this);back.setText(words("‹ Πίσω","‹ Back"));back.setContentDescription(words("Πίσω στο προηγούμενο μενού","Back to previous menu"));back.setAllCaps(false);back.setTextColor(Color.rgb(35,83,62));back.setBackground(surface(Color.WHITE,12));back.setMinHeight(dp(48));toolbar.addView(back,new LinearLayout.LayoutParams(-2,-2));back.setOnClickListener(v->goBack());
        }
        var brand=new TextView(this);brand.setText("MASTIXA");brand.setTextSize(16);brand.setTypeface(null,Typeface.BOLD);brand.setTextColor(Color.rgb(30,62,49));brand.setPadding(dp(12),0,0,0);toolbar.addView(brand);root.addView(toolbar);
        root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        LinearLayout nav=new LinearLayout(this); nav.setPadding(dp(8),dp(8),dp(8),dp(8)); nav.setBackgroundColor(Color.WHITE);
        for(String item:new String[]{"Αρχική","Αγροτεμάχια","Ενότητες","Backup"}) {
            String destination=item.equals("Backup") ? "Τοπικό backup" : item;
            Button tab=new Button(this); tab.setText(t(item)); tab.setAllCaps(false); tab.setTextSize(12); tab.setMinWidth(0); tab.setPadding(0,0,0,0); tab.setMinHeight(dp(52));
            tab.setTextColor(currentPage.equals(destination) ? Color.WHITE : Color.rgb(35,83,62));
            tab.setBackground(surface(currentPage.equals(destination) ? Color.rgb(35,83,62) : Color.WHITE,12));
            nav.addView(tab,new LinearLayout.LayoutParams(0,-2,1)); tab.setOnClickListener(v->navigate(destination));
        }
        root.addView(nav); setContentView(root);

        if(currentPage.equals("Dashboard")){showDashboard();return;}
        if(currentPage.equals("Ειδοποιήσεις")){showAlerts();return;}
        if(currentPage.equals("Έγγραφα Τιμολογίων")||currentPage.equals("Σάρωση OCR")){showDocuments();return;}
        if(currentPage.equals("Κλείδωμα Έτους")){showYearLocks();return;}
        if(ReportStore.PAGES.contains(currentPage)){showReports();return;}
        if(currentPage.equals("Μηχανήματα & Συντήρηση")||currentPage.equals("Συντηρήσεις μηχανημάτων")){showEquipment();return;}
        if(currentPage.equals("Φυτεύσεις & Δέντρα")){showPlantings();return;}
        if(currentPage.equals("Φυτοπροστασία")||currentPage.equals("Εργατικά & Προσωπικό")||currentPage.equals("Προσωπικό")){showWork();return;}
        if(currentPage.equals("Άρδευση & Λίπανση")){showActivities();return;}
        if(currentPage.equals("Παραγωγή")||currentPage.equals("Πωλήσεις Παραγωγής")){showProduction(currentPage.equals("Πωλήσεις Παραγωγής"));return;}
        if(currentPage.equals("Έσοδα")||currentPage.equals("Έξοδα")) { showMoney(currentPage.equals("Έσοδα")?"income":"expense"); return; }
        if(currentPage.equals("Αποθήκη & Εφόδια")) { showInventory(); return; }
        if(currentPage.equals("Προμηθευτές & Αγοραστές")) { showPartners(); return; }
        if(currentPage.equals("Παραγωγός")) { showProducer(); return; }
        if(currentPage.equals("Προϊόντα")) { showProducts(); return; }
        if(currentPage.equals("Γενικές Ρυθμίσεις")) {
            text("Γενικές Ρυθμίσεις",28,true);
            action("Προφίλ και γλώσσα",()->navigate("Προφίλ χρηστών"),false);
            action(words("Επανασύνδεση μετά από: ","Sign in again after: ")+UserSession.timeoutMinutes(this)+words(" λεπτά στο παρασκήνιο"," minutes in the background"),this::sessionTimeout,false);
            action(words("Διαχείριση δεδομένων","Data management"),()->navigate("Διαχείριση δεδομένων"),false); return;
        }
        if(currentPage.equals("Διαχείριση δεδομένων")) {
            text(words("Διαχείριση δεδομένων","Data management"),28,true);
            action("Εισαγωγή από Windows",()->navigate("Εισαγωγή από Windows"),true);
            action("Τοπικό backup",()->navigate("Τοπικό backup"),false); return;
        }
        if(currentPage.equals("Προφίλ χρηστών") || currentPage.equals("Εμφάνιση & Γλώσσα")) {
            text("Προφίλ χρηστών",28,true);
            textValue(profile.name(),22,true); textValue(profile.username(),16,false);
            text(words("Γλώσσα: Ελληνικά","Language: English"),16,false);
            action("Αλλαγή κωδικού",this::changePassword,true);
            action("Αλλαγή προφίλ / γλώσσας",this::logout,false);
            action("Αποσύνδεση",this::logout,false); return;
        }
        if(currentPage.equals("Ενότητες") || currentPage.startsWith("Κατηγορία: ")) {
            text(currentPage.equals("Ενότητες") ? "Όλες οι ενότητες" : currentPage.substring(11),29,true); text("Η εκμετάλλευσή σου, οργανωμένη σε ένα μέρος.",16,false);
            for(String[] group:PageCatalog.GROUPS) {
                if(currentPage.startsWith("Κατηγορία: ") && !currentPage.equals("Κατηγορία: " + group[0])) continue;
                text(group[0],19,true);
                for(int i=1;i<group.length;i++) {
                    String page=group[i]; boolean ready=readyPage(page);
                    action(page + (ready ? "  ›" : "\nΥπό κατασκευή"),()->navigate(page),false);
                }
            }
            return;
        }
        if(currentPage.equals("Εισαγωγή από Windows")) {
            text(currentPage,28,true);
            text(words("Μεταφορά βασικών μητρώων","Transfer base registries"),21,true);
            text(words("Στα Windows άνοιξε «Εξαγωγή Δεδομένων» και επίλεξε παραγωγό, αγροτεμάχια, «Προϊόντα και καλλιέργειες» «Προμηθευτές & Αγοραστές» «Αποθήκη & Εφόδια» «Έσοδα / Έξοδα», «Παραγωγή» «Πωλήσεις Παραγωγής» «Άρδευση & Λίπανση», «Φυτοπροστασία» «Εργατικά & Προσωπικό» «Φυτεύσεις & Δέντρα» και «Μηχανήματα & Συντήρηση». Δημιούργησε ZIP, μετέφερέ το στο κινητό και έλεγξε την προεπισκόπηση. Για προϊόντα χρειάζεται νέα εξαγωγή από την ενημερωμένη έκδοση Windows.","On Windows open Data Export and select producer, fields, Products and cultivations, Suppliers & Buyers, Inventory & Supplies, Income / Expenses, Production, Production Sales, Irrigation & Fertilization, Plant Protection, Labor & Personnel, Plantings & Trees, and Equipment & Maintenance. Create a ZIP, transfer it to your phone and review the preview. Products require a new export from the updated Windows version."),17,false);
            action("Επιλογή ZIP από Windows",()->startActivityForResult(new android.content.Intent(android.content.Intent.ACTION_OPEN_DOCUMENT).addCategory(android.content.Intent.CATEGORY_OPENABLE).setType("*/*"),103),true);
            text(words("Υποστηρίζονται αγροτεμάχια, παραγωγός, προϊόντα, καλλιέργειες συνεργάτες είδη/κινήσεις αποθήκης έσοδα/έξοδα και παραγωγή/πωλήσεις, άρδευση/λίπανση, φυτοπροστασία εργατικά/προσωπικό φυτεύσεις και μηχανήματα/συντήρηση, τιμολόγια και κλειδώματα έτους. Νέο ZIP Windows περιλαμβάνει συνημμένα, παλαιότερο μπορεί να έχει μόνο μεταδεδομένα. Για service με κόστος εξήγαγε μαζί τα οικονομικά. Για φυτοπροστασία ή λίπανση με κατανάλωση εξήγαγε μαζί την αποθήκη. Για πωλήσεις χρειάζονται μαζί η σχετική παραγωγή, τα προϊόντα και τα συνδεδεμένα έσοδα. Για συνδεδεμένες παραλαβές επίλεξε μαζί αποθήκη και οικονομικά. Έως 5.000 εγγραφές ανά πίνακα και 10 MB πριν και μετά την αποσυμπίεση.","Supports fields, producer, products, cultivations partners inventory items/movements income/expenses and production/sales, irrigation/fertilization, plant protection labor/workers plantings and equipment/maintenance. Include finances for services with costs. Include inventory for plant protection or fertilization with consumption. Include related production, products and linked income with sales. Export inventory and finances together for linked receipts. Up to 5,000 rows per table and 10 MB before and after decompression."),14,false);
            text(words("Προστίθενται νέες εγγραφές χωρίς αντικατάσταση υπαρχόντων. Συνεργάτες με ίδια επωνυμία ή ίδιο μη κενό ΑΦΜ παραλείπονται. Πριν την εισαγωγή κρατιέται εσωτερικό αντίγραφο, διαθέσιμο στο Backup.","New records are added without replacing existing ones. Partners with the same name or nonempty tax ID are skipped. An internal backup is kept before import."),14,false);
            return;
        }
        if(!currentPage.equals("Αρχική") && !readyPage(currentPage)) {
            text(currentPage,28,true); text(words("ΥΠΟ ΚΑΤΑΣΚΕΥΗ","UNDER CONSTRUCTION"),14,true);
            text("Ετοιμάζουμε αυτή την ενότητα",23,true);
            text("Η σελίδα έχει προστεθεί στον σχεδιασμό. Οι λειτουργίες της δεν είναι ακόμη διαθέσιμες.",17,false);
            action("Πίσω στις ενότητες",()->navigate("Ενότητες"),true); return;
        }
        text(currentPage.equals("Αρχική") ? "Η εκμετάλλευσή μου" : currentPage,29,true);
        if(currentPage.equals("Αρχική")) {
            textValue(profile.name(),18,true);
            action(words("Dashboard · Συνολική εικόνα","Dashboard · Farm overview"),()->navigate("Dashboard"),true);
            action(words("Ειδοποιήσεις & Εκκρεμότητες","Alerts & Pending Items"),()->navigate("Ειδοποιήσεις"),false);
            action("Προφίλ και γλώσσα",()->navigate("Προφίλ χρηστών"),false);
            text("Το χωράφι σου, πάντα μαζί σου.",18,false);
            TextView badge=text("●  Λειτουργία εκτός σύνδεσης",14,true); badge.setPadding(dp(14),dp(12),dp(14),dp(12)); badge.setBackground(surface(Color.rgb(222,235,220),12));
            var overview=store.fields(); double total=0; for(var field:overview) total+=field.area();
            text(overview.size() + (overview.size() == 1 ? words(" αγροτεμάχιο"," field") : words(" αγροτεμάχια"," fields")),28,true);
            text(String.format(Locale.forLanguageTag(profile.language()),words("%.2f στρέμματα συνολικής έκτασης","%.2f stremma total area"),total),17,false);
            action("Τα αγροτεμάχιά μου  ›",()->navigate("Αγροτεμάχια"),true);
            LinearLayout quickHeader=new LinearLayout(this);
            quickHeader.setGravity(android.view.Gravity.CENTER_VERTICAL);
            TextView quickTitle=new TextView(this);
            quickTitle.setText(t("Γρήγορη πρόσβαση")); quickTitle.setTextSize(21);
            quickTitle.setTypeface(null,Typeface.BOLD); quickTitle.setTextColor(Color.rgb(30,62,49));
            quickTitle.setPadding(0,dp(8),0,dp(8));
            quickHeader.addView(quickTitle,new LinearLayout.LayoutParams(0,-2,1));
            Button customize=new Button(this); customize.setText("✎"); customize.setTextSize(25);
            customize.setTextColor(Color.rgb(35,83,62)); customize.setPadding(0,0,0,0);
            customize.setMinWidth(0); customize.setMinimumWidth(0);
            customize.setBackground(surface(Color.TRANSPARENT,12)); customize.setElevation(0);
            customize.setContentDescription(t("Προσαρμογή γρήγορης πρόσβασης"));
            customize.setTooltipText(t("Προσαρμογή γρήγορης πρόσβασης"));
            customize.setOnClickListener(v->customizeShortcuts());
            quickHeader.addView(customize,new LinearLayout.LayoutParams(dp(48),dp(48)));
            content.addView(quickHeader);
            var favorites=shortcuts();
            if(favorites.isEmpty()) text("Επίλεξε τις κατηγορίες ή τις σελίδες που χρησιμοποιείς συχνότερα.",16,false);
            for(String page:shortcutOptions()) {
                if(!favorites.contains(page)) continue;
                boolean ready=page.startsWith("Κατηγορία: ") || readyPage(page);
                action(page + (ready ? "  ›" : " · Υπό κατασκευή"),()->navigate(page),false);
            }
            return;
        }
        if(currentPage.equals("Αγροτεμάχια")) {
        text("Τα στοιχεία σου αποθηκεύονται στη συσκευή.",16,false);
        var fields = store.fields();
        text(fields.size() + (fields.size() == 1 ? words(" αγροτεμάχιο"," field") : words(" αγροτεμάχια"," fields")), 24, true);
        action("+ Νέο αγροτεμάχιο",()->editField(null),true);
        action(words("Εξαγωγή κορυφών / συντεταγμένων","Export vertices / coordinates"),()->startActivity(new android.content.Intent(this,CoordinateExportActivity.class)),false);
        if (fields.isEmpty()) text("Πρόσθεσε το πρώτο σου αγροτεμάχιο για να ξεκινήσεις.",16,false);
        for (FarmStore.Field field : fields) {
            LinearLayout parent=content; LinearLayout card=new LinearLayout(this); card.setOrientation(LinearLayout.VERTICAL); card.setPadding(dp(18),dp(12),dp(18),dp(16)); card.setBackground(surface(Color.WHITE,18));
            LinearLayout.LayoutParams spacing=new LinearLayout.LayoutParams(-1,-2); spacing.topMargin=dp(16); parent.addView(card,spacing); content=card;
            textValue(field.name(), 20, true);
            text(String.format(Locale.forLanguageTag(profile.language()), words("%.2f στρέμματα","%.2f stremma"), field.area()), 16, false);
            if (!field.location().isEmpty()) textValue(field.location(),16,false);
            if (!field.kaek().isEmpty()) textValue(words("ΚΑΕΚ: ","KAEK: ") + field.kaek(),16,false);
            text(field.trees() + words(" παραγωγικά δέντρα"," productive trees"),16,false);
            if (!field.notes().isEmpty()) textValue(field.notes(),16,false);
            action("Επεξεργασία",()->editField(field),false);
            action(words("Χάρτης / GPS","Map / GPS"),()->startActivity(new android.content.Intent(this,ParcelMapActivity.class).putExtra("field_id",field.id())),false); content=parent;
        }
        return;
        }
        text("Αντίγραφα ασφαλείας",20,true);
        Button export = new Button(this); export.setText(t("Αποθήκευση backup")); content.addView(export);
        export.setOnClickListener(v -> startActivityForResult(new android.content.Intent(android.content.Intent.ACTION_CREATE_DOCUMENT).addCategory(android.content.Intent.CATEGORY_OPENABLE).setType("application/json").putExtra(android.content.Intent.EXTRA_TITLE,"mastixa-"+System.currentTimeMillis()+".json"),101));
        Button restore = new Button(this); restore.setText(t("Επαναφορά από αρχείο")); content.addView(restore);
        restore.setOnClickListener(v -> startActivityForResult(new android.content.Intent(android.content.Intent.ACTION_OPEN_DOCUMENT).addCategory(android.content.Intent.CATEGORY_OPENABLE).setType("*/*"),102));
        if(recoveryFile().exists()) {
            Button undo = new Button(this); undo.setText(t("Επαναφορά πριν την τελευταία αλλαγή βάσης")); content.addView(undo);
            undo.setOnClickListener(v -> { try(java.io.InputStream in=new android.util.AtomicFile(recoveryFile()).openRead()) { confirmRestore(LocalBackup.read(in)); } catch(Exception error) { backupMessage("Δεν διαβάζεται το εσωτερικό αντίγραφο."); } });
        }
        text(words("Το backup περιλαμβάνει αγροτεμάχια, παραγωγό, προϊόντα, καλλιέργειες, συνεργάτες, είδη/κινήσεις αποθήκης, έσοδα/έξοδα, παραγωγή/πωλήσεις, άρδευση/λίπανση, φυτοπροστασία, εργατικά/προσωπικό, φυτεύσεις, μηχανήματα/συντήρηση και εκκρεμείς αλλαγές του ενεργού προφίλ. Δεν περιλαμβάνει κωδικούς. Το αρχείο δεν είναι κρυπτογραφημένο.","Backup includes this profile’s fields, producer, products, cultivations, partners, inventory items/movements, income/expenses, production/sales, irrigation/fertilization, plant protection, labor/workers, plantings, equipment/maintenance and pending changes. It excludes passwords. The file is not encrypted."),14,false);
    }
    private void confirmCatalogImport(CatalogImport.Package data) {
        var plan=CatalogImport.preview(store,data);
        String message=words("Νέες καταχωρίσεις:\nΑγροτεμάχια: ","New records:\nFields: ")+plan.fields()+words("\nΠαραγωγός: ","\nProducer: ")+plan.producer()+words("\nΠροϊόντα: ","\nProducts: ")+plan.products()+words("\nΣυνδέσεις καλλιέργειας: ","\nCultivation links: ")+plan.links()+words("\nΣυνεργάτες: ","\nPartners: ")+plan.partners()+words("\nΕίδη αποθήκης: ","\nInventory items: ")+plan.inventoryItems()+words("\nΚινήσεις αποθήκης: ","\nInventory movements: ")+plan.inventoryMovements()+words("\nΈσοδα: ","\nIncome: ")+plan.income()+words("\nΈξοδα: ","\nExpenses: ")+plan.expenses()+words("\nΠαραγωγή: ","\nProduction: ")+plan.harvests()+words("\nΠωλήσεις: ","\nSales: ")+plan.sales()+words("\nΆρδευση / Λίπανση: ","\nIrrigation / Fertilization: ")+plan.activities()+words("\nΦυτοπροστασία: ","\nPlant protection: ")+plan.protections()+words("\nΕργαζόμενοι: ","\nWorkers: ")+plan.workers()+words("\nΕργατικά: ","\nLabor: ")+plan.labor()+words("\nΦυτεύσεις: ","\nPlantings: ")+plan.plantings()+words("\nΜηχανήματα: ","\nEquipment: ")+plan.equipment()+words("\nΣυντηρήσεις: ","\nMaintenance: ")+plan.services()+words("\nΤιμολόγια: ","\nDocuments: ")+plan.documents()+words("\nΚλειδώματα έτους: ","\nYear locks: ")+plan.yearLocks()+words("\nΠαραλείψεις (υπάρχοντα ή συγκρούσεις): ","\nSkipped (existing or conflicting): ")+plan.skipped();
        if(data.producer()!=null) message+="\n\n"+t("Παραγωγός")+": "+data.producer().name();
        for(int i=0;i<Math.min(8,data.products().size());i++) message+="\n• "+data.products().get(i);
        for(int i=0;i<Math.min(8,data.partners().size());i++) message+="\n• "+data.partners().get(i).name();
        if(!plan.ignored().isEmpty()) message+=words("\n\nΆλλες ενότητες στο ZIP που δεν εισάγονται ακόμη: ","\n\nOther ZIP sections not yet imported: ")+plan.ignored().size();
        message+=words("\n\nΟι υπάρχουσες εγγραφές δεν αντικαθίστανται. Οι σχέσεις απαιτούν αντιστοίχιση χωρίς σύγκρουση. Οι εισαγόμενες κινήσεις αποθήκης διατηρούνται ως ιστορικό και αλλάζουν μέσω διορθωτικών κινήσεων. Θα κρατηθεί αντίγραφο ασφαλείας πριν τις προσθήκες.","\n\nExisting records are not replaced. Relationships require matching without conflicts. Imported inventory movements are kept as history; use corrections for adjustments. A backup is kept before additions.");
        var dialog=new AlertDialog.Builder(this).setTitle(t("Προεπισκόπηση εισαγωγής")).setMessage(message).setNegativeButton(t("Κλείσιμο"),null);
        if(plan.fields()+plan.producer()+plan.products()+plan.links()+plan.partners()+plan.inventoryItems()+plan.inventoryMovements()+plan.income()+plan.expenses()+plan.harvests()+plan.sales()+plan.activities()+plan.protections()+plan.workers()+plan.labor()+plan.plantings()+plan.equipment()+plan.services()+plan.documents()+plan.yearLocks()>0) dialog.setPositiveButton(t("Εισαγωγή"),(d,w)-> {
            try { CatalogImport.apply(store,data,recoveryFile());showHome();backupMessage(words("Η εισαγωγή ολοκληρώθηκε.","Import completed.")); }
            catch(Exception error) { backupMessage(t("Η εισαγωγή απέτυχε. Δεν προστέθηκε καμία εγγραφή.")); }
        }); dialog.show();
    }
    private CatalogStore catalog() { return new CatalogStore(store); }
    private void showProducer() {
        text("Παραγωγός",28,true); var p=catalog().producer();
        textValue(p.empty()?words("Δεν έχουν καταχωριστεί στοιχεία παραγωγού.","No producer details yet."):p.name(),21,true);
        textValue(words("ΑΦΜ: ","Tax ID: ")+p.taxId(),16,false);
        textValue(words("Τηλέφωνο: ","Phone: ")+p.phone(),16,false);
        textValue(words("Ηλεκτρονικό ταχυδρομείο: ","Email: ")+p.email(),16,false); textValue(p.notes(),16,false);
        action("Επεξεργασία",()-> {
            var form=new LinearLayout(this); form.setOrientation(LinearLayout.VERTICAL); form.setPadding(dp(20),dp(8),dp(20),0);
            var name=input(form,words("Ονοματεπώνυμο / Επωνυμία","Full name / Business name"),p.name(),InputType.TYPE_CLASS_TEXT);
            var tax=input(form,words("ΑΦΜ","Tax ID"),p.taxId(),InputType.TYPE_CLASS_TEXT);
            var phone=input(form,words("Τηλέφωνο","Phone"),p.phone(),InputType.TYPE_CLASS_PHONE);
            var email=input(form,words("Ηλεκτρονικό ταχυδρομείο","Email"),p.email(),InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS);
            var notes=input(form,words("Σημειώσεις","Notes"),p.notes(),InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE);
            saveForm(t("Παραγωγός"),form,()->catalog().saveProducer(new CatalogStore.Producer(name.getText().toString(),tax.getText().toString(),phone.getText().toString(),email.getText().toString(),notes.getText().toString())));
        },true);
    }
    private void saveForm(String title,LinearLayout form,Runnable save) {
        var scroll=new ScrollView(this); scroll.addView(form);
        var dialog=new AlertDialog.Builder(this).setTitle(title).setView(scroll).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Αποθήκευση"),null).create();
        dialog.setOnShowListener(v->dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(w->{
            try { save.run(); dialog.dismiss(); showHome(); }
            catch(UiValidationException error) { backupMessage(error.getMessage()); }
            catch(IllegalArgumentException error) { backupMessage(words("Έλεγξε τα υποχρεωτικά πεδία, τα μοναδικά ονόματα, τις επιλογές και τις ημερομηνίες (YYYY-MM-DD).","Check required fields, unique names, selections and dates (YYYY-MM-DD).")); }
            catch(Exception error) { backupMessage(error.getMessage()!=null&&error.getMessage().contains("Year is locked")?words("Το έτος είναι κλειδωμένο. Διαχείριση από Κλείδωμα Έτους.","This year is locked. Manage it in Year Lock."):words("Δεν αποθηκεύτηκε. Δοκίμασε ξανά.","Not saved. Please try again.")); }
        })); dialog.show();
    }
    private PartnerStore partners() { return new PartnerStore(store); }
    private String partnerType(String type) {
        return switch(type) { case "supplier" -> words("Προμηθευτής","Supplier"); case "buyer" -> words("Αγοραστής","Buyer"); default -> words("Προμηθευτής & Αγοραστής","Supplier & Buyer"); };
    }
    private void showPartners() {
        text("Προμηθευτές & Αγοραστές",28,true);
        var all=partners().partners();
        text(words("Σύνολο: ","Total: ")+all.size()+words(" · Προμηθευτές: "," · Suppliers: ")+all.stream().filter(p->!p.type().equals("buyer")).count()+words(" · Αγοραστές: "," · Buyers: ")+all.stream().filter(p->!p.type().equals("supplier")).count(),15,false);
        action(words("+ Νέος συνεργάτης","+ New partner"),()->editPartner(null),true);
        action(words("Αναζήτηση: ","Search: ")+partnerQuery,()-> {
            var query=new EditText(this); query.setText(partnerQuery);
            new AlertDialog.Builder(this).setTitle(words("Επωνυμία, ΑΦΜ, τηλέφωνο ή προϊόντα","Name, tax ID, phone or products")).setView(query).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Εντάξει"),(d,w)->{partnerQuery=query.getText().toString().trim();showHome();}).show();
        },false);
        String[] types={"all","supplier","buyer","both"};
        action(words("Τύπος: ","Type: ")+(partnerFilter==0?words("Όλοι","All"):partnerType(types[partnerFilter])),()->{partnerFilter=(partnerFilter+1)%4;showHome();},false);
        int visible=0;
        for(var p:all) {
            if(!PartnerStore.matches(p,partnerQuery,types[partnerFilter])) continue;
            visible++; textValue(p.name(),21,true); textValue(partnerType(p.type()),15,false);
            if(!p.taxId().isBlank()) textValue(words("ΑΦΜ: ","Tax ID: ")+p.taxId(),16,false);
            if(!p.phone().isBlank()) textValue(p.phone(),16,false);
            action(words("Στοιχεία συνεργάτη","Partner details"),()->partnerDetails(p),false);
            action(words("Οικονομικό ιστορικό","Financial history"),()->partnerMoney(p),false);
            action("Επεξεργασία",()->editPartner(p),false);
        }
        if(visible==0) text(words("Δεν βρέθηκαν συνεργάτες.","No partners found."),16,false);
        text(words("Το οικονομικό ιστορικό εμφανίζει τα συνδεδεμένα έσοδα και έξοδα που έχουν καταχωριστεί ή εισαχθεί στο Android.","Financial history shows linked income and expenses recorded or imported into Android."),14,false);
    }
    private String[] partnerLabels() { return new String[]{words("Επωνυμία *","Name *"),words("Τύπος","Type"),words("ΑΦΜ","Tax ID"),words("Υπεύθυνος επικοινωνίας","Contact person"),words("Τηλέφωνο","Phone"),words("Ηλεκτρονικό ταχυδρομείο","Email"),words("Διεύθυνση","Address"),words("Προϊόντα / Υπηρεσίες","Products / Services"),words("Όροι πληρωμής","Payment terms"),words("Σημειώσεις","Notes")}; }
    private void partnerDetails(PartnerStore.Partner p) {
        var details=new StringBuilder(); var labels=partnerLabels(); var values=p.values();
        for(int i=1;i<labels.length;i++) details.append(labels[i]).append(": ").append(i==1?partnerType(p.type()):values[i]).append("\n\n");
        new AlertDialog.Builder(this).setTitle(p.name()).setMessage(details.toString()).setNegativeButton(t("Κλείσιμο"),null).setPositiveButton(t("Επεξεργασία"),(d,w)->editPartner(p)).setNeutralButton(t("Διαγραφή"),(d,w)-> {
            new AlertDialog.Builder(this).setTitle(words("Διαγραφή συνεργάτη;","Delete partner?")).setMessage(p.name()).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Διαγραφή"),(a,b)-> {
                try { partners().delete(p.id()); showHome(); } catch(Exception error) { backupMessage(words("Δεν διαγράφηκε. Δοκίμασε ξανά.","Not deleted. Please try again.")); }
            }).show();
        }).show();
    }
    private void editPartner(PartnerStore.Partner p) {
        var form=new LinearLayout(this); form.setOrientation(LinearLayout.VERTICAL); form.setPadding(dp(20),dp(8),dp(20),0);
        var labels=partnerLabels(); var values=p==null?new String[]{"","supplier","","","","","","","",""}:p.values(); var edits=new EditText[10];
        edits[0]=input(form,labels[0],values[0],InputType.TYPE_CLASS_TEXT);
        var caption=new TextView(this); caption.setText(labels[1]); form.addView(caption);
        String[] types={"supplier","buyer","both"}; var chooser=new Spinner(this); chooser.setContentDescription(labels[1]); chooser.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,java.util.Arrays.stream(types).map(this::partnerType).toArray(String[]::new))); chooser.setSelection(java.util.Arrays.asList(types).indexOf(values[1])); form.addView(chooser);
        for(int i=2;i<10;i++) edits[i]=input(form,labels[i],values[i],i==4?InputType.TYPE_CLASS_PHONE:InputType.TYPE_CLASS_TEXT | (i>=6?InputType.TYPE_TEXT_FLAG_MULTI_LINE:i==5?InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS:0));
        saveForm(words(p==null?"Νέος συνεργάτης":"Επεξεργασία συνεργάτη",p==null?"New partner":"Edit partner"),form,()-> {
            String[] v=new String[10]; for(int i=0;i<10;i++) v[i]=i==1?types[chooser.getSelectedItemPosition()]:edits[i].getText().toString();
            partners().save(new PartnerStore.Partner(p==null?null:p.id(),v[0],v[1],v[2],v[3],v[4],v[5],v[6],v[7],v[8],v[9]));
        });
    }
    private InventoryStore inventory() { return new InventoryStore(store); }
    private String quantity(double n) { return java.math.BigDecimal.valueOf(n).stripTrailingZeros().toPlainString(); }
    private double decimal(EditText edit) {
        try { double n=Double.parseDouble(edit.getText().toString().trim().replace(',','.'));if(!Double.isFinite(n)||n<0)throw new NumberFormatException();return n; }
        catch(NumberFormatException e){throw new UiValidationException(words("Συμπλήρωσε έγκυρο μη αρνητικό αριθμό.","Enter a valid nonnegative number."));}
    }
    private String movementType(String type) { int index=java.util.Arrays.asList(InventoryStore.TYPES).indexOf(type);return words(type,new String[]{"Receipt","Consumption","Correction +","Correction -"}[index]); }
    private void inventoryAction(Runnable run){try{run.run();showHome();}catch(IllegalArgumentException e){backupMessage(words("Έλεγξε το διαθέσιμο απόθεμα και τις συνδεδεμένες εγγραφές. Το εισαγόμενο ιστορικό δεν αλλάζει.","Check available stock and linked records. Imported history cannot be changed."));}catch(Exception e){backupMessage(words("Η ενέργεια απέτυχε.","The action failed."));}}
    private void showInventory() {
        var registry=inventory();var items=registry.items();
        var selected=items.stream().filter(i->i.id().equals(inventoryItemId)).findFirst().orElse(null);
        if(selected!=null){showInventoryItem(selected);return;}inventoryItemId=null;
        text("Αποθήκη & Εφόδια",28,true);
        action(words("+ Νέο είδος","+ New item"),()->editInventoryItem(null),true);
        action(words("Αναζήτηση: ","Search: ")+inventoryQuery,()->{var q=new EditText(this);q.setText(inventoryQuery);new AlertDialog.Builder(this).setTitle(words("Όνομα ή κατηγορία είδους","Item name or category")).setView(q).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Εντάξει"),(d,w)->{inventoryQuery=q.getText().toString().trim();showHome();}).show();},false);
        action(inventoryLowOnly?words("Φίλτρο: Χαμηλό / μηδενικό απόθεμα","Filter: Low / zero stock"):words("Φίλτρο: Όλα τα είδη","Filter: All items"),()->{inventoryLowOnly=!inventoryLowOnly;showHome();},false);
        int visible=0;
        for(var i:items){double balance=registry.stock(i.id());boolean low=balance<=i.minimum();if(!(i.name()+" "+i.category()).toLowerCase(Locale.ROOT).contains(inventoryQuery.toLowerCase(Locale.ROOT))||(inventoryLowOnly&&!low))continue;visible++;textValue(i.name(),21,true);textValue(i.category(),15,false);textValue(quantity(balance)+" "+i.unit()+words(" · Ελάχιστο: "," · Minimum: ")+quantity(i.minimum()),18,true);if(low)text(words("Χαμηλό / μηδενικό απόθεμα","Low / zero stock"),15,false);action(words("Στοιχεία και κινήσεις","Details and movements"),()->openInventoryItem(i.id()),false);}
        if(visible==0)text(words("Δεν βρέθηκαν είδη.","No items found."),16,false);
        text(words("Οι νέες τοπικές παραλαβές με κόστος δημιουργούν αυτόματα έξοδο. Για παραλαβές Windows εισάγονται τα συνδεδεμένα έξοδα από το ZIP. Η αναφορά αξίας αποθήκης παραμένει επόμενο στάδιο.","New local receipts with a cost create an expense automatically. Windows receipt expenses are imported from the ZIP. Stock valuation reports are still pending."),14,false);
    }
    private void showInventoryItem(InventoryStore.Item item){
        action(words("Πίσω στα είδη","Back to items"),()->navigate("Αποθήκη & Εφόδια"),false);textValue(item.name(),28,true);textValue(item.category()+" · "+quantity(inventory().stock(item.id()))+" "+item.unit(),19,true);textValue(words("Ελάχιστο απόθεμα: ","Minimum stock: ")+quantity(item.minimum()),16,false);textValue(item.notes(),16,false);
        action("Επεξεργασία",()->editInventoryItem(item),false);
        action(words("+ Νέα κίνηση","+ New movement"),()->editInventoryMovement(item,null),true);
        action(words("Διαγραφή είδους","Delete item"),()->new AlertDialog.Builder(this).setMessage(words("Να διαγραφεί το είδος; Επιτρέπεται μόνο χωρίς κινήσεις.","Delete item? Only items without movements can be deleted.")).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Διαγραφή"),(d,w)->inventoryAction(()->inventory().deleteItem(item.id()))).show(),false);
        text(words("Κινήσεις αποθήκης","Inventory movements"),22,true);
        var moves=inventory().movements(item.id());if(moves.isEmpty())text(words("Δεν υπάρχουν κινήσεις.","No movements yet."),16,false);
        for(var m:moves){textValue(m.date()+" · "+movementType(m.type()),18,true);textValue(quantity(m.quantity())+" "+item.unit(),18,false);
            String field=store.fields().stream().filter(f->f.id().equals(m.fieldId())).map(FarmStore.Field::name).findFirst().orElse(m.fieldId().isEmpty()?"":words("Διαγραμμένο αγροτεμάχιο","Deleted field"));
            String partner=new PartnerStore(store).partners().stream().filter(p->p.id().equals(m.partnerId())).map(PartnerStore.Partner::name).findFirst().orElse(m.supplier());
            if(!field.isEmpty())textValue(words("Αγροτεμάχιο: ","Field: ")+field,15,false);if(!partner.isEmpty())textValue(words("Συνεργάτης: ","Partner: ")+partner,15,false);
            if(m.type().equals(InventoryStore.TYPES[0]))textValue(words("Τιμή μονάδας: ","Unit price: ")+quantity(m.price())+" € · "+words("Κόστος: ","Cost: ")+quantity(m.cost())+" €",16,false);textValue(m.notes(),15,false);
            if(m.sourceType().equals("android_plant_protection")){action(words("Συνδεδεμένη φυτοπροστασία","Linked plant protection"),()->{var a=work().protections().stream().filter(x->x.id().equals(m.sourceId())).findFirst().orElse(null);if(a!=null){navigate("Φυτοπροστασία");protectionDetails(a);}},false);}
            else if(m.sourceType().equals("android_farm_activity")){action(words("Συνδεδεμένη εργασία","Linked activity"),()->{var a=activities().activities().stream().filter(x->x.id().equals(m.sourceId())).findFirst().orElse(null);if(a!=null){navigate("Άρδευση & Λίπανση");activityDetails(a);}},false);}
            else if(!m.windowsId().isEmpty()||!m.sourceType().isEmpty()){text(words("Ιστορικό από Windows — για αλλαγές πρόσθεσε διορθωτική κίνηση.","Windows history — add a correction to make adjustments."),14,false);}
            else {action(words("Επεξεργασία κίνησης","Edit movement"),()->editInventoryMovement(item,m),false);action(words("Διαγραφή κίνησης","Delete movement"),()->new AlertDialog.Builder(this).setMessage(words("Να διαγραφεί η κίνηση;","Delete movement?")).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Διαγραφή"),(d,w)->inventoryAction(()->inventory().deleteMovement(m.id()))).show(),false);}
        }
    }
    private void editInventoryItem(InventoryStore.Item item){
        var form=new LinearLayout(this);form.setOrientation(LinearLayout.VERTICAL);form.setPadding(dp(20),dp(8),dp(20),0);
        var name=input(form,words("Όνομα είδους *","Item name *"),item==null?"":item.name(),InputType.TYPE_CLASS_TEXT);
        var category=input(form,words("Κατηγορία","Category"),item==null?"":item.category(),InputType.TYPE_CLASS_TEXT);
        var unit=input(form,words("Μονάδα *","Unit *"),item==null?"kg":item.unit(),InputType.TYPE_CLASS_TEXT);
        var minimum=input(form,words("Ελάχιστο απόθεμα","Minimum stock"),item==null?"0":quantity(item.minimum()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var initial=item==null?input(form,words("Αρχικό απόθεμα","Initial stock"),"0",InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL):null;
        var notes=input(form,words("Σημειώσεις","Notes"),item==null?"":item.notes(),InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        saveForm(words(item==null?"Νέο είδος":"Επεξεργασία είδους",item==null?"New item":"Edit item"),form,()->{
            double starting=initial==null?0:decimal(initial);var db=store.getWritableDatabase();db.beginTransaction();try{String id=inventory().saveItem(new InventoryStore.Item(item==null?null:item.id(),name.getText().toString(),category.getText().toString(),unit.getText().toString(),decimal(minimum),notes.getText().toString()));if(starting>0)inventory().saveMovement(new InventoryStore.Movement(null,id,java.time.LocalDate.now().toString(),InventoryStore.TYPES[2],starting,"","","",0,0,words("Αρχικό απόθεμα","Initial stock"),"","","",""));db.setTransactionSuccessful();}finally{db.endTransaction();}
        });
    }
    private Spinner choice(LinearLayout form,String label,java.util.List<String> labels,int selected){var caption=new TextView(this);caption.setText(label);form.addView(caption);var spinner=new Spinner(this);spinner.setContentDescription(label);spinner.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,labels));spinner.setSelection(Math.max(0,selected));form.addView(spinner);return spinner;}
    private void editInventoryMovement(InventoryStore.Item item,InventoryStore.Movement m){
        var form=new LinearLayout(this);form.setOrientation(LinearLayout.VERTICAL);form.setPadding(dp(20),dp(8),dp(20),0);
        var date=input(form,words("Ημερομηνία (YYYY-MM-DD) *","Date (YYYY-MM-DD) *"),m==null?java.time.LocalDate.now().toString():m.date(),InputType.TYPE_CLASS_TEXT);
        var type=choice(form,words("Τύπος κίνησης","Movement type"),java.util.Arrays.stream(InventoryStore.TYPES).map(this::movementType).toList(),m==null?0:java.util.Arrays.asList(InventoryStore.TYPES).indexOf(m.type()));
        var amount=input(form,words("Ποσότητα *","Quantity *"),m==null?"":quantity(m.quantity()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var fieldIds=new java.util.ArrayList<String>();var fieldNames=new java.util.ArrayList<String>();fieldIds.add("");fieldNames.add(words("Χωρίς αγροτεμάχιο","No field"));for(var f:store.fields()){fieldIds.add(f.id());fieldNames.add(f.name());}if(m!=null&&!fieldIds.contains(m.fieldId())){fieldIds.add(m.fieldId());fieldNames.add(words("Διαγραμμένο αγροτεμάχιο — επίλεξε άλλο","Deleted field — choose another"));}
        var field=choice(form,t("Αγροτεμάχιο"),fieldNames,m==null?0:fieldIds.indexOf(m.fieldId()));
        var partnerIds=new java.util.ArrayList<String>();var partnerNames=new java.util.ArrayList<String>();partnerIds.add("");partnerNames.add(words("Χωρίς σύνδεση συνεργάτη","No linked partner"));for(var p:new PartnerStore(store).partners()){partnerIds.add(p.id());partnerNames.add(p.name());}if(m!=null&&!partnerIds.contains(m.partnerId())){partnerIds.add(m.partnerId());partnerNames.add(words("Διαγραμμένος συνεργάτης — επίλεξε άλλον","Deleted partner — choose another"));}
        var partner=choice(form,words("Προμηθευτής (παραλαβή)","Supplier (receipt)"),partnerNames,m==null?0:partnerIds.indexOf(m.partnerId()));
        var supplier=input(form,words("Προμηθευτής χωρίς σύνδεση (προαιρετικό)","Unlinked supplier name (optional)"),m==null?"":m.supplier(),InputType.TYPE_CLASS_TEXT);
        var price=input(form,words("Τιμή μονάδας € (μόνο παραλαβή)","Unit price € (receipt only)"),m==null?"0":quantity(m.price()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var notes=input(form,words("Σημειώσεις","Notes"),m==null?"":m.notes(),InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        saveForm(words("Κίνηση αποθήκης","Inventory movement"),form,()->{double q=decimal(amount);boolean receipt=type.getSelectedItemPosition()==0;double p=receipt?decimal(price):0;String partnerId=receipt?partnerIds.get(partner.getSelectedItemPosition()):"";String supplierName=receipt?(partnerId.isEmpty()?supplier.getText().toString():partnerNames.get(partner.getSelectedItemPosition())):"";inventory().saveMovement(new InventoryStore.Movement(m==null?null:m.id(),item.id(),date.getText().toString().trim(),InventoryStore.TYPES[type.getSelectedItemPosition()],q,fieldIds.get(field.getSelectedItemPosition()),partnerId,supplierName,p,q*p,notes.getText().toString(),"","","",""));});
    }
    private MoneyStore money() { return new MoneyStore(store); }
    private String euros(java.math.BigDecimal n){return n.setScale(2,java.math.RoundingMode.HALF_UP).toPlainString()+" €";}
    private String moneyPartner(MoneyStore.Entry e){return new PartnerStore(store).partners().stream().filter(p->p.id().equals(e.partnerId())).map(PartnerStore.Partner::name).findFirst().orElse(e.partnerName());}
    private void showMoney(String kind){
        text(kind.equals("income")?"Έσοδα":"Έξοδα",28,true);
        action(words(kind.equals("income")?"+ Νέο έσοδο":"+ Νέο έξοδο",kind.equals("income")?"+ New income":"+ New expense"),()->editMoney(kind,null),true);
        action(words("Αναζήτηση: ","Search: ")+moneyQuery,()->{var q=new EditText(this);q.setText(moneyQuery);new AlertDialog.Builder(this).setTitle(words("Περιγραφή, κατηγορία ή συνεργάτης","Description, category or partner")).setView(q).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Εντάξει"),(d,w)->{moneyQuery=q.getText().toString().trim();showHome();}).show();},false);
        var years=new java.util.TreeSet<String>(java.util.Comparator.reverseOrder());for(var e:money().entries(kind))years.add(e.date().substring(0,4));var yearOptions=new java.util.ArrayList<String>();yearOptions.add("");yearOptions.addAll(years);
        action(words("Έτος: ","Year: ")+(moneyYear.isEmpty()?words("Όλα","All"):moneyYear),()->new AlertDialog.Builder(this).setTitle(words("Επιλογή έτους","Select year")).setItems(yearOptions.stream().map(y->y.isEmpty()?words("Όλα","All"):y).toArray(String[]::new),(d,index)->{moneyYear=yearOptions.get(index);showHome();}).show(),false);
        var entries=money().entries(kind).stream().filter(e->(moneyYear.isEmpty()||e.date().startsWith(moneyYear+"-"))&&(e.description()+" "+e.category()+" "+moneyPartner(e)).toLowerCase(Locale.ROOT).contains(moneyQuery.toLowerCase(Locale.ROOT))).toList();
        textValue(words("Σύνολο αποτελεσμάτων: ","Filtered total: ")+euros(MoneyStore.total(entries)),21,true);
        if(entries.isEmpty())text(words("Δεν βρέθηκαν εγγραφές.","No records found."),16,false);
        for(var e:entries){textValue(e.date()+" · "+euros(java.math.BigDecimal.valueOf(e.amount())),20,true);textValue(e.description(),18,true);if(!e.category().isEmpty())textValue(e.category(),15,false);if(!moneyPartner(e).isEmpty())textValue(moneyPartner(e),16,false);action(words("Στοιχεία εγγραφής","Entry details"),()->moneyDetails(e),false);}
        text(words("Τα ποσά αφορούν καταχωρισμένα έσοδα/έξοδα, όχι ανεξόφλητα υπόλοιπα. Οι εισαγόμενες εγγραφές διατηρούνται ως ιστορικό.","Amounts represent recorded income/expenses, not outstanding balances. Imported entries are kept as history."),14,false);
    }
    private void moneyDetails(MoneyStore.Entry e){
        String field=store.fields().stream().filter(f->f.id().equals(e.fieldId())).map(FarmStore.Field::name).findFirst().orElse(e.fieldId().isEmpty()?"":words("Διαγραμμένο αγροτεμάχιο","Deleted field"));
        String message=e.date()+" · "+euros(java.math.BigDecimal.valueOf(e.amount()))+"\n\n"+e.category()+"\n"+e.description()+"\n"+field+"\n"+moneyPartner(e)+"\n"+words("Πληρωμή: ","Payment: ")+e.payment()+"\n\n"+e.notes();
        var dialog=new AlertDialog.Builder(this).setTitle(t(e.kind().equals("income")?"Έσοδα":"Έξοδα")).setMessage(message).setNegativeButton(t("Κλείσιμο"),null);
        if(e.sourceType().isEmpty()&&e.windowsId().isEmpty()){dialog.setPositiveButton(t("Επεξεργασία"),(d,w)->editMoney(e.kind(),e));dialog.setNeutralButton(t("Διαγραφή"),(d,w)->new AlertDialog.Builder(this).setMessage(words("Να διαγραφεί η οικονομική εγγραφή;","Delete financial entry?")).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Διαγραφή"),(a,b)->inventoryAction(()->money().delete(e.id()))).show());}
        else if(e.sourceType().equals("inventory_receipt"))dialog.setPositiveButton(words("Παραλαβή αποθήκης","Inventory receipt"),(d,w)->{var m=inventory().movements(null).stream().filter(x->x.id().equals(e.sourceId())).findFirst().orElse(null);if(m!=null){openInventoryItem(m.itemId());}else backupMessage(words("Η παραλαβή δεν είναι διαθέσιμη.","Receipt unavailable."));});
        else if(e.sourceType().equals("invoice_document"))dialog.setPositiveButton(words("Τιμολόγιο","Invoice"),(d,w)->{navigate("Έγγραφα Τιμολογίων");documentDetails(e.sourceId());});
        else if(e.sourceType().equals("equipment_maintenance"))dialog.setPositiveButton(words("Συντήρηση μηχανήματος","Equipment service"),(d,w)->{var service=work().services().stream().filter(x->x.id().equals(e.sourceId())).findFirst().orElse(null);if(service!=null){navigate("Συντηρήσεις μηχανημάτων");serviceDetails(service);}});
        else if(e.sourceType().equals("production_sale"))dialog.setPositiveButton(words("Πώληση παραγωγής","Production sale"),(d,w)->{var sale=production().sales().stream().filter(x->x.id().equals(e.sourceId())).findFirst().orElse(null);if(sale!=null){navigate("Πωλήσεις Παραγωγής");saleDetails(sale);}else backupMessage(words("Η πώληση δεν είναι διαθέσιμη.","Sale unavailable."));});
        dialog.show();
    }
    private void partnerMoney(PartnerStore.Partner p){
        var entries=money().entries(null).stream().filter(e->e.partnerId().equals(p.id())||(e.partnerId().isEmpty()&&e.partnerName().equalsIgnoreCase(p.name()))).toList();var income=MoneyStore.total(entries.stream().filter(e->e.kind().equals("income")).toList());var expense=MoneyStore.total(entries.stream().filter(e->e.kind().equals("expense")).toList());var body=new StringBuilder(words("Έσοδα: ","Income: ")+euros(income)+words("\nΈξοδα: ","Expenses: ")+euros(expense)+words("\nΔιαφορά εσόδων–εξόδων: ","\nIncome minus expenses: ")+euros(income.subtract(expense))+"\n");
        if(entries.isEmpty())body.append(words("\nΔεν υπάρχουν καταχωρισμένες συναλλαγές.","\nNo recorded transactions."));for(var e:entries)body.append("\n").append(e.date()).append(" · ").append(t(e.kind().equals("income")?"Έσοδα":"Έξοδα")).append(" · ").append(euros(java.math.BigDecimal.valueOf(e.amount()))).append("\n").append(e.description()).append("\n");
        new AlertDialog.Builder(this).setTitle(p.name()).setMessage(body.toString()).setPositiveButton(t("Κλείσιμο"),null).show();
    }
    private void editMoney(String kind,MoneyStore.Entry e){
        var form=new LinearLayout(this);form.setOrientation(LinearLayout.VERTICAL);form.setPadding(dp(20),dp(8),dp(20),0);
        var date=input(form,words("Ημερομηνία (YYYY-MM-DD) *","Date (YYYY-MM-DD) *"),e==null?java.time.LocalDate.now().toString():e.date(),InputType.TYPE_CLASS_TEXT);
        var description=input(form,words("Περιγραφή *","Description *"),e==null?"":e.description(),InputType.TYPE_CLASS_TEXT);
        var category=kind.equals("expense")?input(form,words("Κατηγορία *","Category *"),e==null?"Λοιπά έξοδα":e.category(),InputType.TYPE_CLASS_TEXT):null;
        var amount=input(form,words("Ποσό € *","Amount € *"),e==null?"":quantity(e.amount()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var fieldIds=new java.util.ArrayList<String>();var fieldNames=new java.util.ArrayList<String>();fieldIds.add("");fieldNames.add(words("Χωρίς αγροτεμάχιο","No field"));for(var f:store.fields()){fieldIds.add(f.id());fieldNames.add(f.name());}if(e!=null&&!fieldIds.contains(e.fieldId())){fieldIds.add(e.fieldId());fieldNames.add(words("Διαγραμμένο αγροτεμάχιο","Deleted field"));}var field=choice(form,words("Αγροτεμάχιο","Field"),fieldNames,e==null?0:fieldIds.indexOf(e.fieldId()));
        var partnerIds=new java.util.ArrayList<String>();var partnerNames=new java.util.ArrayList<String>();partnerIds.add("");partnerNames.add(words("Χωρίς σύνδεση συνεργάτη","No linked partner"));for(var p:new PartnerStore(store).partners()){partnerIds.add(p.id());partnerNames.add(p.name());}if(e!=null&&!partnerIds.contains(e.partnerId())){partnerIds.add(e.partnerId());partnerNames.add(e.partnerName());}var partner=choice(form,words("Συνεργάτης","Partner"),partnerNames,e==null?0:partnerIds.indexOf(e.partnerId()));
        var partnerName=input(form,words("Όνομα συνεργάτη χωρίς σύνδεση","Unlinked partner name"),e==null?"":e.partnerName(),InputType.TYPE_CLASS_TEXT);
        var payment=input(form,words("Τρόπος πληρωμής","Payment method"),e==null?"":e.payment(),InputType.TYPE_CLASS_TEXT);
        var notes=input(form,words("Σημειώσεις","Notes"),e==null?"":e.notes(),InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        saveForm(t(kind.equals("income")?"Έσοδα":"Έξοδα"),form,()->{String partnerId=partnerIds.get(partner.getSelectedItemPosition());money().save(new MoneyStore.Entry(e==null?null:e.id(),kind,date.getText().toString().trim(),fieldIds.get(field.getSelectedItemPosition()),category==null?"":category.getText().toString(),description.getText().toString(),partnerId,partnerId.isEmpty()?partnerName.getText().toString():partnerNames.get(partner.getSelectedItemPosition()),payment.getText().toString(),decimal(amount),notes.getText().toString(),"","",""));});
    }
    private String equipmentName(String id){return work().equipment().stream().filter(e->e.id().equals(id)).map(WorkStore.Equipment::name).findFirst().orElse(words("Διαγραμμένο μηχάνημα","Deleted equipment"));}
    private String meterLabel(String value){return value.equals("hours")?words("ώρες","hours"):value.equals("km")?"km":words("χωρίς μετρητή","no meter");}
    private String reminderLabel(String value){return switch(value){case "overdue"->words("Εκπρόθεσμη","Overdue");case "upcoming"->words("Επερχόμενη","Upcoming");case "planned"->words("Προγραμματισμένη","Planned");default->words("Χωρίς υπενθύμιση","No reminder");};}
    private String equipmentStatus(String value){int n=WorkStore.EQUIPMENT_STATUSES.indexOf(value);return words(value,java.util.List.of("Active","Under maintenance","Out of service","Sold").get(n));}
    private void equipmentHistory(String id){navigate("Συντηρήσεις μηχανημάτων");equipmentFilter=id;workQuery="";workYear="";showHome();}
    private void showEquipment(){boolean services=currentPage.equals("Συντηρήσεις μηχανημάτων");text(words(services?"Συντηρήσεις μηχανημάτων":"Μηχανήματα & Συντήρηση",services?"Equipment maintenance":"Equipment & Maintenance"),28,true);
        action(words(services?"+ Νέα συντήρηση":"+ Νέο μηχάνημα",services?"+ New service":"+ New equipment"),()->{if(services)editService(null);else editEquipment(null);},true);if(!services)action(words("Συντηρήσεις","Maintenance"),()->equipmentHistory(""),false);
        action(words("Αναζήτηση: ","Search: ")+workQuery,()->{var q=new EditText(this);q.setText(workQuery);new AlertDialog.Builder(this).setTitle(words("Αναζήτηση","Search")).setView(q).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Εντάξει"),(d,w)->{workQuery=q.getText().toString().trim();showHome();}).show();},false);
        if(services){var years=new java.util.TreeSet<String>(java.util.Comparator.reverseOrder());for(var a:work().services())years.add(a.service_date().substring(0,4));action(words("Έτος: ","Year: ")+(workYear.isEmpty()?words("Όλα","All"):workYear),()->activityFilter(words("Έτος","Year"),new java.util.ArrayList<>(years),x->workYear=x),false);var ids=new java.util.ArrayList<String>();var names=new java.util.ArrayList<String>();ids.add("");names.add(words("Όλα","All"));for(var e:work().equipment()){ids.add(e.id());names.add(e.name());}action(words("Μηχάνημα: ","Equipment: ")+(equipmentFilter.isEmpty()?words("Όλα","All"):equipmentName(equipmentFilter)),()->workFilter(words("Μηχάνημα","Equipment"),ids,names,x->equipmentFilter=x),false);java.math.BigDecimal cost=java.math.BigDecimal.ZERO;int count=0;for(var a:work().services()){if((!equipmentFilter.isEmpty()&&!equipmentFilter.equals(a.equipment_id()))||(!workYear.isEmpty()&&!a.service_date().startsWith(workYear+"-"))||!(equipmentName(a.equipment_id())+" "+a.service_type()+" "+a.technician()+" "+a.notes()).toLowerCase(Locale.ROOT).contains(workQuery.toLowerCase(Locale.ROOT)))continue;count++;cost=cost.add(java.math.BigDecimal.valueOf(a.cost()));textValue(a.service_date()+" · "+equipmentName(a.equipment_id()),20,true);textValue(a.service_type()+" · "+euros(java.math.BigDecimal.valueOf(a.cost())),17,false);action(words("Στοιχεία συντήρησης","Service details"),()->serviceDetails(a),false);}textValue(words("Συντηρήσεις: ","Services: ")+count+words(" · Κόστος: "," · Cost: ")+euros(cost),19,true);return;}
        action(words("Υπενθυμίσεις: ","Reminders: ")+(equipmentReminder.isEmpty()?words("Όλες","All"):reminderLabel(equipmentReminder)),()->workFilter(words("Υπενθυμίσεις","Reminders"),java.util.List.of("","upcoming","overdue"),java.util.List.of(words("Όλες","All"),reminderLabel("upcoming"),reminderLabel("overdue")),x->equipmentReminder=x),false);
        int count=0;for(var e:work().equipment()){String reminder=work().reminder(e,java.time.LocalDate.now());if((!equipmentReminder.isEmpty()&&!reminder.equals(equipmentReminder))||!(e.name()+" "+e.category()+" "+e.brand_model()+" "+e.equipment_code()+" "+e.notes()).toLowerCase(Locale.ROOT).contains(workQuery.toLowerCase(Locale.ROOT)))continue;count++;textValue(e.name()+" · "+equipmentStatus(e.status()),20,true);textValue(e.brand_model()+" · "+quantity(e.current_meter())+" "+meterLabel(e.meter_type()),17,false);textValue(reminderLabel(reminder),17,false);var next=work().services().stream().filter(a->a.equipment_id().equals(e.id())&&(!a.next_service_date().isEmpty()||a.next_service_meter()!=null)).findFirst().orElse(null);if(next!=null)textValue(next.next_service_date()+" "+(next.next_service_meter()==null?"":quantity(next.next_service_meter())+" "+meterLabel(e.meter_type())),16,false);action(words("Στοιχεία μηχανήματος","Equipment details"),()->equipmentDetails(e),false);action(words("Ιστορικό συντήρησης","Maintenance history"),()->equipmentHistory(e.id()),false);if(e.windows_id().isEmpty())action(words("Διαγραφή μηχανήματος","Delete equipment"),()->workDelete(words("Να διαγραφεί το μηχάνημα;","Delete equipment?"),()->work().deleteEquipment(e.id())),false);}if(count==0)text(words("Δεν βρέθηκαν μηχανήματα.","No equipment found."),17,false);
        text(words("Επερχόμενη συντήρηση: έως 30 ημέρες ή 50 μονάδες μετρητή. Η υπενθύμιση βασίζεται στην τελευταία καταγραφή με επόμενο service.","Upcoming maintenance: within 30 days or 50 meter units. The reminder uses the latest record with a next service."),14,false);
    }
    private void equipmentDetails(WorkStore.Equipment a){String body=a.name()+"\n"+a.category()+"\n"+a.brand_model()+"\n"+a.equipment_code()+"\n"+words("Αγορά: ","Purchased: ")+a.purchase_date()+"\n"+a.fuel()+"\n"+quantity(a.current_meter())+" "+meterLabel(a.meter_type())+"\n"+equipmentStatus(a.status())+"\n"+a.notes();if(!a.windows_id().isEmpty())body+="\n\n"+words("Ιστορικό από Windows","Windows history");var d=new AlertDialog.Builder(this).setTitle(words("Στοιχεία μηχανήματος","Equipment details")).setMessage(body).setNegativeButton(t("Κλείσιμο"),null);if(a.windows_id().isEmpty())d.setPositiveButton(t("Επεξεργασία"),(x,y)->editEquipment(a));d.show();}
    private void editEquipment(WorkStore.Equipment a){var form=workForm();
        var name=input(form,words("Όνομα μηχανήματος *","Equipment name *"),a==null?"":a.name(),InputType.TYPE_CLASS_TEXT);
        var category=input(form,words("Κατηγορία","Category"),a==null?"":a.category(),InputType.TYPE_CLASS_TEXT);
        var brand_model=input(form,words("Μάρκα / μοντέλο","Brand / model"),a==null?"":a.brand_model(),InputType.TYPE_CLASS_TEXT);
        var equipment_code=input(form,words("Κωδικός μηχανήματος","Equipment code"),a==null?"":a.equipment_code(),InputType.TYPE_CLASS_TEXT);
        var purchase_date=input(form,words("Ημερομηνία αγοράς (YYYY-MM-DD, προαιρετική)","Purchase date (YYYY-MM-DD, optional)"),a==null?"":a.purchase_date(),InputType.TYPE_CLASS_TEXT);
        var fuel=input(form,words("Καύσιμο","Fuel"),a==null?"":a.fuel(),InputType.TYPE_CLASS_TEXT);
        var current_meter=input(form,words("Τρέχουσα ένδειξη","Current meter"),a==null?"0":quantity(a.current_meter()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var notes=input(form,words("Σημειώσεις","Notes"),a==null?"":a.notes(),InputType.TYPE_CLASS_TEXT);
        var meter=choice(form,words("Τύπος μετρητή","Meter type"),WorkStore.METERS.stream().map(this::meterLabel).toList(),a==null?0:WorkStore.METERS.indexOf(a.meter_type()));var status=choice(form,words("Κατάσταση","Status"),WorkStore.EQUIPMENT_STATUSES.stream().map(this::equipmentStatus).toList(),a==null?0:WorkStore.EQUIPMENT_STATUSES.indexOf(a.status()));
        saveForm(words("Μηχάνημα","Equipment"),form,()->work().saveEquipment(new WorkStore.Equipment(a==null?null:a.id(),name.getText().toString().trim(),category.getText().toString().trim(),brand_model.getText().toString().trim(),equipment_code.getText().toString().trim(),purchase_date.getText().toString().trim(),fuel.getText().toString().trim(),WorkStore.METERS.get(meter.getSelectedItemPosition()),decimal(current_meter),WorkStore.EQUIPMENT_STATUSES.get(status.getSelectedItemPosition()),notes.getText().toString(),"")));
    }
    private void serviceDetails(WorkStore.Service a){String body=a.service_date()+"\n"+equipmentName(a.equipment_id())+"\n"+a.service_type()+"\n"+words("Ένδειξη μετρητή: ","Meter reading: ")+quantity(a.meter_value())+"\n"+words("Τεχνικός: ","Technician: ")+a.technician()+"\n"+words("Επόμενη ημερομηνία: ","Next date: ")+a.next_service_date()+"\n"+words("Επόμενη ένδειξη: ","Next meter: ")+(a.next_service_meter()==null?"—":quantity(a.next_service_meter()))+"\n"+euros(java.math.BigDecimal.valueOf(a.cost()))+"\n"+a.notes();if(!a.windows_id().isEmpty())body+="\n\n"+words("Ιστορικό από Windows","Windows history");var d=new AlertDialog.Builder(this).setTitle(words("Στοιχεία συντήρησης","Service details")).setMessage(body).setNegativeButton(t("Κλείσιμο"),null);if(a.windows_id().isEmpty()){d.setPositiveButton(t("Επεξεργασία"),(x,y)->editService(a));d.setNeutralButton(t("Διαγραφή"),(x,y)->workDelete(words("Να διαγραφεί η συντήρηση και το συνδεδεμένο έξοδο;","Delete service and its linked expense?"),()->work().deleteService(a.id())));}d.show();}
    private void editService(WorkStore.Service a){var equipment=work().equipment();if(equipment.isEmpty()){backupMessage(words("Πρόσθεσε πρώτα μηχάνημα.","Add equipment first."));return;}var form=workForm();int index=0;String selected=a==null?equipmentFilter:a.equipment_id();for(int n=0;n<equipment.size();n++)if(equipment.get(n).id().equals(selected))index=n;var machine=choice(form,words("Μηχάνημα","Equipment"),equipment.stream().map(WorkStore.Equipment::name).toList(),index);
        var service_date=input(form,words("Ημερομηνία (YYYY-MM-DD) *","Date (YYYY-MM-DD) *"),a==null?java.time.LocalDate.now().toString():a.service_date(),InputType.TYPE_CLASS_TEXT);
        var service_type=input(form,words("Είδος service *","Service type *"),a==null?"":a.service_type(),InputType.TYPE_CLASS_TEXT);
        var cost=input(form,words("Κόστος €","Cost €"),a==null?"0":quantity(a.cost()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var meter_value=input(form,words("Ένδειξη μετρητή","Meter reading"),a==null?"0":quantity(a.meter_value()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var technician=input(form,words("Τεχνικός","Technician"),a==null?"":a.technician(),InputType.TYPE_CLASS_TEXT);
        var next_service_date=input(form,words("Επόμενο service (YYYY-MM-DD, προαιρετικό)","Next service date (YYYY-MM-DD, optional)"),a==null?"":a.next_service_date(),InputType.TYPE_CLASS_TEXT);
        var next_service_meter=input(form,words("Επόμενη ένδειξη (προαιρετική)","Next meter (optional)"),a==null?"":(a.next_service_meter()==null?"":quantity(a.next_service_meter())),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var notes=input(form,words("Σημειώσεις","Notes"),a==null?"":a.notes(),InputType.TYPE_CLASS_TEXT);
        saveForm(words("Συντήρηση","Maintenance"),form,()->work().saveService(new WorkStore.Service(a==null?null:a.id(),equipment.get(machine.getSelectedItemPosition()).id(),service_date.getText().toString().trim(),service_type.getText().toString().trim(),decimal(cost),decimal(meter_value),technician.getText().toString().trim(),notes.getText().toString(),next_service_date.getText().toString().trim(),next_service_meter.getText().toString().isBlank()?null:decimal(next_service_meter),"","")));
    }
    private void showPlantings(){
        text("Φυτεύσεις & Δέντρα",28,true);action(words("+ Νέα φύτευση","+ New planting"),()->editPlanting(null),true);
        action(words("Αναζήτηση: ","Search: ")+workQuery,()->{var q=new EditText(this);q.setText(workQuery);new AlertDialog.Builder(this).setTitle(words("Αναζήτηση","Search")).setView(q).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Εντάξει"),(d,w)->{workQuery=q.getText().toString().trim();showHome();}).show();},false);
        var years=new java.util.TreeSet<String>(java.util.Comparator.reverseOrder());for(var a:work().plantings())years.add(a.planting_date().substring(0,4));action(words("Έτος: ","Year: ")+(workYear.isEmpty()?words("Όλα","All"):workYear),()->activityFilter(words("Έτος","Year"),new java.util.ArrayList<>(years),x->workYear=x),false);
        var ids=new java.util.ArrayList<String>();var names=new java.util.ArrayList<String>();ids.add("");names.add(words("Όλα","All"));for(var f:store.fields()){ids.add(f.id());names.add(f.name());}action(words("Αγροτεμάχιο: ","Field: ")+(workField.isEmpty()?words("Όλα","All"):activityField(workField)),()->workFilter(words("Αγροτεμάχιο","Field"),ids,names,x->workField=x),false);
        long planted=0,alive=0;java.math.BigDecimal cost=java.math.BigDecimal.ZERO;int count=0;
        for(var a:work().plantings()){if(!workMatch(a.planting_date(),a.field_id(),a.material_type()+" "+a.source()+" "+a.variety()+" "+a.spacing()+" "+a.notes()))continue;count++;planted+=a.trees_planted();alive+=a.trees_alive();cost=cost.add(java.math.BigDecimal.valueOf(a.cost()));textValue(a.planting_date()+" · "+activityField(a.field_id()),20,true);textValue(a.variety()+" · "+a.material_type(),16,false);textValue(words("Φυτεμένα: ","Planted: ")+a.trees_planted()+words(" · Ζωντανά: "," · Alive: ")+a.trees_alive(),17,false);action(words("Στοιχεία φύτευσης","Planting details"),()->plantingDetails(a),false);}
        textValue(words("Παρτίδες: ","Batches: ")+count+words(" · Φυτεμένα: "," · Planted: ")+planted,19,true);textValue(words("Ζωντανά: ","Alive: ")+alive+words(" · Απώλειες: "," · Losses: ")+(planted-alive),18,true);textValue(words("Επιβίωση: ","Survival: ")+String.format(Locale.ROOT,"%.1f%%",planted==0?0:100.0*alive/planted),18,true);textValue(words("Κόστος: ","Cost: ")+euros(cost),18,true);
        text(words("Οι παρτίδες φύτευσης δεν αλλάζουν αυτόματα τα παραγωγικά δέντρα του αγροτεμαχίου και δεν δημιουργούν ξεχωριστό έξοδο.","Planting batches do not automatically change the field’s productive tree count or create a separate expense."),14,false);
    }
    private void plantingDetails(WorkStore.Planting a){String body=a.planting_date()+"\n"+activityField(a.field_id())+"\n"+words("Φυτεμένα: ","Planted: ")+a.trees_planted()+"\n"+words("Ζωντανά: ","Alive: ")+a.trees_alive()+"\n"+words("Απώλειες: ","Losses: ")+(a.trees_planted()-a.trees_alive())+"\n"+words("Επιβίωση: ","Survival: ")+String.format(Locale.ROOT,"%.1f%%",a.trees_planted()==0?0:100.0*a.trees_alive()/a.trees_planted())+"\n"+words("Υλικό: ","Material: ")+a.material_type()+"\n"+words("Προέλευση: ","Source: ")+a.source()+"\n"+words("Ποικιλία: ","Variety: ")+a.variety()+"\n"+words("Αποστάσεις: ","Spacing: ")+a.spacing()+"\n"+words("Κόστος: ","Cost: ")+euros(java.math.BigDecimal.valueOf(a.cost()))+"\n"+a.notes();if(!a.windows_id().isEmpty())body+="\n\n"+words("Ιστορικό από Windows","Windows history");var d=new AlertDialog.Builder(this).setTitle(words("Στοιχεία φύτευσης","Planting details")).setMessage(body).setNegativeButton(t("Κλείσιμο"),null);if(a.windows_id().isEmpty()){d.setPositiveButton(t("Επεξεργασία"),(x,y)->editPlanting(a));d.setNeutralButton(t("Διαγραφή"),(x,y)->workDelete(words("Να διαγραφεί η παρτίδα φύτευσης;","Delete this planting batch?"),()->work().deletePlanting(a.id())));}d.show();}
    private int treeCount(EditText input){double n=decimal(input);if(n!=Math.rint(n)||n>Integer.MAX_VALUE)throw new UiValidationException(words("Το πλήθος δέντρων πρέπει να είναι μη αρνητικός ακέραιος.","Tree count must be a nonnegative integer."));return (int)n;}
    private void editPlanting(WorkStore.Planting a){var fields=store.fields();if(fields.isEmpty()){backupMessage(words("Πρόσθεσε πρώτα αγροτεμάχιο.","Add a field first."));return;}if(a!=null&&fields.stream().noneMatch(f->f.id().equals(a.field_id()))){backupMessage(words("Το αγροτεμάχιο έχει διαγραφεί. Διατηρείται το ιστορικό.","The field was deleted. History is retained."));return;}var form=workForm();var date=input(form,words("Ημερομηνία (YYYY-MM-DD) *","Date (YYYY-MM-DD) *"),a==null?java.time.LocalDate.now().toString():a.planting_date(),InputType.TYPE_CLASS_TEXT);int index=0;for(int n=0;n<fields.size();n++)if(a!=null&&fields.get(n).id().equals(a.field_id()))index=n;var field=choice(form,words("Αγροτεμάχιο","Field"),fields.stream().map(FarmStore.Field::name).toList(),index);
        var trees_planted=input(form,words("Φυτεμένα δέντρα","Trees planted"),a==null?"0":quantity(a.trees_planted()),InputType.TYPE_CLASS_NUMBER);
        var trees_alive=input(form,words("Ζωντανά δέντρα","Trees alive"),a==null?"0":quantity(a.trees_alive()),InputType.TYPE_CLASS_NUMBER);
        var material_type=input(form,words("Υλικό φύτευσης","Planting material"),a==null?"":a.material_type(),InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        var source=input(form,words("Προέλευση","Source"),a==null?"":a.source(),InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        var variety=input(form,words("Ποικιλία","Variety"),a==null?"":a.variety(),InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        var spacing=input(form,words("Αποστάσεις φύτευσης","Planting spacing"),a==null?"":a.spacing(),InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        var cost=input(form,words("Κόστος €","Cost €"),a==null?"0":quantity(a.cost()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var notes=input(form,words("Σημειώσεις","Notes"),a==null?"":a.notes(),InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        saveForm(t("Φυτεύσεις & Δέντρα"),form,()->work().savePlanting(new WorkStore.Planting(a==null?null:a.id(),date.getText().toString().trim(),fields.get(field.getSelectedItemPosition()).id(),treeCount(trees_planted),treeCount(trees_alive),material_type.getText().toString().trim(),source.getText().toString().trim(),variety.getText().toString().trim(),spacing.getText().toString().trim(),decimal(cost),notes.getText().toString(),"")));
    }
    private WorkStore work(){return new WorkStore(store);}
    private String workerName(String id){return work().workers().stream().filter(w->w.id().equals(id)).map(WorkStore.Worker::name).findFirst().orElse(words("Διαγραμμένος εργαζόμενος","Deleted worker"));}
    private void workFilter(String title,java.util.List<String> ids,java.util.List<String> labels,java.util.function.Consumer<String> set){new AlertDialog.Builder(this).setTitle(title).setItems(labels.toArray(String[]::new),(d,n)->{set.accept(ids.get(n));showHome();}).show();}
    private void showWork(){
        boolean protection=currentPage.equals("Φυτοπροστασία"),workers=currentPage.equals("Προσωπικό");text(words(currentPage,protection?"Plant Protection":workers?"Staff":"Labor & Personnel"),28,true);
        action(words(protection?"+ Νέα επέμβαση":workers?"+ Νέος εργαζόμενος":"+ Νέα καταχώρηση εργατικών",protection?"+ New treatment":workers?"+ New worker":"+ New labor entry"),()->{if(protection)editProtection(null);else if(workers)editWorker(null);else editLabor(null);},true);
        if(!protection&&!workers)action(words("Προσωπικό","Staff"),()->navigate("Προσωπικό"),false);
        action(words("Αναζήτηση: ","Search: ")+workQuery,()->{var q=new EditText(this);q.setText(workQuery);new AlertDialog.Builder(this).setTitle(words("Αναζήτηση","Search")).setView(q).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Εντάξει"),(d,w)->{workQuery=q.getText().toString().trim();showHome();}).show();},false);
        if(workers){for(var w:work().workers()){if(!(w.name()+" "+w.role()+" "+w.phone()+" "+w.notes()).toLowerCase(Locale.ROOT).contains(workQuery.toLowerCase(Locale.ROOT)))continue;textValue(w.name()+" · "+words(w.active()==1?"Ενεργός":"Ανενεργός",w.active()==1?"Active":"Inactive"),20,true);textValue(w.role()+" · "+w.phone(),16,false);textValue(euros(java.math.BigDecimal.valueOf(w.default_hourly_rate()))+words(" / ώρα"," / hour"),17,false);action(words("Στοιχεία εργαζομένου","Worker details"),()->workerDetails(w),false);if(w.windows_id().isEmpty())action(words("Διαγραφή εργαζομένου","Delete worker"),()->workDelete(words("Να διαγραφεί ο εργαζόμενος; Αν υπάρχει ιστορικό, επίλεξε Ανενεργός.","Delete worker? If there is history, select Inactive instead."),()->work().deleteWorker(w.id())),false);}return;}
        var years=new java.util.TreeSet<String>(java.util.Comparator.reverseOrder());if(protection)for(var a:work().protections())years.add(a.application_date().substring(0,4));else for(var a:work().labor())years.add(a.work_date().substring(0,4));action(words("Έτος: ","Year: ")+(workYear.isEmpty()?words("Όλα","All"):workYear),()->activityFilter(words("Έτος","Year"),new java.util.ArrayList<>(years),x->workYear=x),false);
        var fieldIds=new java.util.ArrayList<String>();var fieldNames=new java.util.ArrayList<String>();fieldIds.add("");fieldNames.add(words("Όλα","All"));for(var f:store.fields()){fieldIds.add(f.id());fieldNames.add(f.name());}action(words("Αγροτεμάχιο: ","Field: ")+(workField.isEmpty()?words("Όλα","All"):activityField(workField)),()->workFilter(words("Αγροτεμάχιο","Field"),fieldIds,fieldNames,x->workField=x),false);
        if(!protection){var ids=new java.util.ArrayList<String>();var names=new java.util.ArrayList<String>();ids.add("");names.add(words("Όλοι","All"));for(var w:work().workers()){ids.add(w.id());names.add(w.name());}action(words("Εργαζόμενος: ","Worker: ")+(workWorker.isEmpty()?words("Όλοι","All"):workerName(workWorker)),()->workFilter(words("Εργαζόμενος","Worker"),ids,names,x->workWorker=x),false);}
        java.math.BigDecimal total=java.math.BigDecimal.ZERO;double hours=0;int count=0;
        if(protection)for(var a:work().protections()){if(!workMatch(a.application_date(),a.field_id(),a.product_name()+" "+a.purpose()+" "+a.applicator()+" "+a.notes()))continue;count++;total=total.add(java.math.BigDecimal.valueOf(a.cost()));textValue(a.application_date()+" · "+a.product_name(),20,true);textValue(activityField(a.field_id())+" · "+a.purpose(),16,false);action(words("Στοιχεία επέμβασης","Treatment details"),()->protectionDetails(a),false);}
        else for(var a:work().labor()){if(!workMatch(a.work_date(),a.field_id(),workerName(a.worker_id())+" "+a.work_type()+" "+a.notes())||(!workWorker.isEmpty()&&!workWorker.equals(a.worker_id())))continue;count++;hours+=a.hours();total=total.add(java.math.BigDecimal.valueOf(a.cost()));textValue(a.work_date()+" · "+workerName(a.worker_id()),20,true);textValue(activityField(a.field_id())+" · "+a.work_type(),16,false);textValue(quantity(a.hours())+words(" ώρες · "," hours · ")+euros(java.math.BigDecimal.valueOf(a.cost())),17,false);action(words("Στοιχεία εργατικών","Labor details"),()->laborDetails(a),false);}
        textValue(words("Εγγραφές: ","Records: ")+count+words(" · Κόστος: "," · Cost: ")+euros(total),19,true);if(!protection)textValue(words("Ώρες: ","Hours: ")+quantity(hours),18,true);text(words("Το κόστος παραμένει στην καταγραφή και δεν δημιουργεί αυτόματα ξεχωριστό έξοδο.","Cost stays in this record and does not automatically create a separate expense."),14,false);
    }
    private boolean workMatch(String date,String field,String value){return (workYear.isEmpty()||date.startsWith(workYear+"-"))&&(workField.isEmpty()||workField.equals(field))&&(activityField(field)+" "+value).toLowerCase(Locale.ROOT).contains(workQuery.toLowerCase(Locale.ROOT));}
    private LinearLayout workForm(){var form=new LinearLayout(this);form.setOrientation(LinearLayout.VERTICAL);form.setPadding(dp(20),dp(8),dp(20),0);return form;}
    private void workDelete(String message,Runnable run){new AlertDialog.Builder(this).setMessage(message).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Διαγραφή"),(d,w)->inventoryAction(run)).show();}
    private void protectionDetails(WorkStore.Protection a){
        String body=a.application_date()+"\n"+activityField(a.field_id())+"\n"+a.purpose()+" · "+a.product_name()+"\n"+words("Δραστική ουσία: ","Active ingredient: ")+a.active_ingredient()+"\n"+words("Αριθμός έγκρισης: ","Authorization number: ")+a.authorization_number()+"\n"+words("Δόση: ","Dose: ")+quantity(a.dose())+" "+a.dose_unit()+"\n"+words("Ψεκαστικό υγρό: ","Spray volume: ")+quantity(a.spray_volume_l())+" L\n"+words("Έκταση: ","Area: ")+quantity(a.area_stremma())+words(" στρ."," stremma")+"\n"+a.applicator()+" · "+a.weather()+"\n"+words("Αναμονή συγκομιδής (ημέρες): ","Harvest interval (days): ")+a.harvest_interval_days()+"\n"+words("Κατανάλωση αποθήκης: ","Inventory consumption: ")+quantity(a.inventory_quantity())+"\n"+words("Κόστος: ","Cost: ")+euros(java.math.BigDecimal.valueOf(a.cost()))+"\n"+a.notes();
        if(!a.windows_id().isEmpty())body+="\n\n"+words("Ιστορικό από Windows","Windows history");var d=new AlertDialog.Builder(this).setTitle(words("Στοιχεία επέμβασης","Treatment details")).setMessage(body).setNegativeButton(t("Κλείσιμο"),null);if(a.windows_id().isEmpty()){d.setPositiveButton(t("Επεξεργασία"),(x,y)->editProtection(a));d.setNeutralButton(t("Διαγραφή"),(x,y)->workDelete(words("Διαγραφή επέμβασης και επιστροφή κατανάλωσης στην αποθήκη;","Delete treatment and return its consumption to inventory?"),()->work().deleteProtection(a.id())));}d.show();
    }
    private void editProtection(WorkStore.Protection a){
        var form=workForm();var fields=store.fields();if(fields.isEmpty()){backupMessage(words("Πρόσθεσε πρώτα αγροτεμάχιο.","Add a field first."));return;}if(a!=null&&fields.stream().noneMatch(f->f.id().equals(a.field_id()))){backupMessage(words("Το αγροτεμάχιο έχει διαγραφεί. Διατηρείται το ιστορικό.","The field was deleted. History is retained."));return;}
        var date=input(form,words("Ημερομηνία (YYYY-MM-DD) *","Date (YYYY-MM-DD) *"),a==null?java.time.LocalDate.now().toString():a.application_date(),InputType.TYPE_CLASS_TEXT);int fi=0;for(int n=0;n<fields.size();n++)if(a!=null&&fields.get(n).id().equals(a.field_id()))fi=n;var field=choice(form,words("Αγροτεμάχιο","Field"),fields.stream().map(FarmStore.Field::name).toList(),fi);
        var ids=new java.util.ArrayList<String>();var names=new java.util.ArrayList<String>();ids.add("");names.add(words("Χωρίς σύνδεση αποθήκης","No inventory link"));for(var item:inventory().items()){ids.add(item.id());names.add(item.name()+" · "+quantity(inventory().stock(item.id()))+" "+item.unit());}if(a!=null&&!ids.contains(a.inventory_item_id())){ids.add(a.inventory_item_id());names.add(words("Διαγραμμένο είδος","Deleted item"));}var item=choice(form,words("Είδος αποθήκης","Inventory item"),names,a==null?0:ids.indexOf(a.inventory_item_id()));
        var purpose=input(form,words("Στόχος *","Purpose *"),a==null?"":a.purpose(),InputType.TYPE_CLASS_TEXT);
        var product_name=input(form,words("Σκεύασμα / προϊόν *","Product *"),a==null?"":a.product_name(),InputType.TYPE_CLASS_TEXT);
        var active_ingredient=input(form,words("Δραστική ουσία","Active ingredient"),a==null?"":a.active_ingredient(),InputType.TYPE_CLASS_TEXT);
        var authorization_number=input(form,words("Αριθμός έγκρισης","Authorization number"),a==null?"":a.authorization_number(),InputType.TYPE_CLASS_TEXT);
        var dose=input(form,words("Δόση","Dose"),a==null?"0":quantity(a.dose()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var dose_unit=input(form,words("Μονάδα δόσης","Dose unit"),a==null?"":a.dose_unit(),InputType.TYPE_CLASS_TEXT);
        var spray_volume_l=input(form,words("Ψεκαστικό υγρό (L)","Spray volume (L)"),a==null?"0":quantity(a.spray_volume_l()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var area_stremma=input(form,words("Έκταση (στρ.)","Area (stremma)"),a==null?"0":quantity(a.area_stremma()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var applicator=input(form,words("Εφαρμοστής","Applicator"),a==null?"":a.applicator(),InputType.TYPE_CLASS_TEXT);
        var weather=input(form,words("Καιρός","Weather"),a==null?"":a.weather(),InputType.TYPE_CLASS_TEXT);
        var harvest_interval_days=input(form,words("Αναμονή συγκομιδής (ημέρες)","Harvest interval (days)"),a==null?"0":quantity(a.harvest_interval_days()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var cost=input(form,words("Κόστος €","Cost €"),a==null?"0":quantity(a.cost()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var inventory_quantity=input(form,words("Ποσότητα αποθήκης (μονάδα είδους)","Inventory quantity (item unit)"),a==null?"0":quantity(a.inventory_quantity()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var notes=input(form,words("Σημειώσεις","Notes"),a==null?"":a.notes(),InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        saveForm(words("Φυτοπροστασία","Plant Protection"),form,()->{double days=decimal(harvest_interval_days);if(days!=Math.rint(days)||days>Integer.MAX_VALUE)throw new UiValidationException(words("Οι ημέρες αναμονής πρέπει να είναι ακέραιες.","Harvest interval days must be whole numbers."));work().saveProtection(new WorkStore.Protection(a==null?null:a.id(),date.getText().toString().trim(),fields.get(field.getSelectedItemPosition()).id(),ids.get(item.getSelectedItemPosition()),purpose.getText().toString().trim(),product_name.getText().toString().trim(),active_ingredient.getText().toString().trim(),authorization_number.getText().toString().trim(),decimal(dose),dose_unit.getText().toString().trim(),decimal(spray_volume_l),decimal(area_stremma),applicator.getText().toString().trim(),weather.getText().toString().trim(),(int)days,decimal(cost),notes.getText().toString(),decimal(inventory_quantity),"",""));});
    }
    private void workerDetails(WorkStore.Worker w){
        String body=w.name()+"\n"+w.role()+"\n"+w.phone()+"\n"+euros(java.math.BigDecimal.valueOf(w.default_hourly_rate()))+words(" / ώρα"," / hour")+"\n"+w.notes();if(!w.windows_id().isEmpty())body+="\n\n"+words("Ιστορικό από Windows","Windows history");var d=new AlertDialog.Builder(this).setTitle(words("Στοιχεία εργαζομένου","Worker details")).setMessage(body).setNegativeButton(t("Κλείσιμο"),null);d.setNeutralButton(words("Ιστορικό εργατικών","Labor history"),(x,y)->{navigate("Εργατικά & Προσωπικό");workWorker=w.id();workYear="";workField="";workQuery="";showHome();});if(w.windows_id().isEmpty())d.setPositiveButton(t("Επεξεργασία"),(x,y)->editWorker(w));d.show();
    }
    private void editWorker(WorkStore.Worker a){var form=workForm();
        var name=input(form,words("Ονοματεπώνυμο *","Full name *"),a==null?"":a.name(),InputType.TYPE_CLASS_TEXT);
        var role=input(form,words("Ρόλος","Role"),a==null?"":a.role(),InputType.TYPE_CLASS_TEXT);
        var phone=input(form,words("Τηλέφωνο","Phone"),a==null?"":a.phone(),InputType.TYPE_CLASS_TEXT);
        var default_hourly_rate=input(form,words("Προεπιλεγμένο ωρομίσθιο €","Default hourly rate €"),a==null?"0":quantity(a.default_hourly_rate()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var notes=input(form,words("Σημειώσεις","Notes"),a==null?"":a.notes(),InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        var active=choice(form,words("Κατάσταση","Status"),java.util.List.of(words("Ανενεργός","Inactive"),words("Ενεργός","Active")),a==null?1:a.active());
        saveForm(words("Προσωπικό","Staff"),form,()->work().saveWorker(new WorkStore.Worker(a==null?null:a.id(),name.getText().toString().trim(),role.getText().toString().trim(),phone.getText().toString().trim(),decimal(default_hourly_rate),active.getSelectedItemPosition(),notes.getText().toString(),"")));
    }
    private void laborDetails(WorkStore.Labor a){String body=a.work_date()+"\n"+workerName(a.worker_id())+"\n"+activityField(a.field_id())+"\n"+a.work_type()+"\n"+quantity(a.hours())+" × "+euros(java.math.BigDecimal.valueOf(a.hourly_rate()))+" = "+euros(java.math.BigDecimal.valueOf(a.cost()))+"\n"+a.notes();if(!a.windows_id().isEmpty())body+="\n\n"+words("Ιστορικό από Windows","Windows history");var d=new AlertDialog.Builder(this).setTitle(words("Στοιχεία εργατικών","Labor details")).setMessage(body).setNegativeButton(t("Κλείσιμο"),null);if(a.windows_id().isEmpty()){d.setPositiveButton(t("Επεξεργασία"),(x,y)->editLabor(a));d.setNeutralButton(t("Διαγραφή"),(x,y)->workDelete(words("Να διαγραφεί η καταχώρηση εργατικών;","Delete labor entry?"),()->work().deleteLabor(a.id())));}d.show();}
    private void editLabor(WorkStore.Labor a){var workers=work().workers().stream().filter(w->w.active()==1||(a!=null&&w.id().equals(a.worker_id()))).toList();if(workers.isEmpty()){backupMessage(words("Πρόσθεσε πρώτα ενεργό εργαζόμενο στο Προσωπικό.","Add an active worker in Staff first."));return;}var form=workForm();var date=input(form,words("Ημερομηνία (YYYY-MM-DD) *","Date (YYYY-MM-DD) *"),a==null?java.time.LocalDate.now().toString():a.work_date(),InputType.TYPE_CLASS_TEXT);int wi=0;for(int n=0;n<workers.size();n++)if(a!=null&&workers.get(n).id().equals(a.worker_id()))wi=n;var worker=choice(form,words("Εργαζόμενος","Worker"),workers.stream().map(WorkStore.Worker::name).toList(),wi);
        var ids=new java.util.ArrayList<String>();var names=new java.util.ArrayList<String>();ids.add("");names.add(words("Χωρίς αγροτεμάχιο","No field"));for(var f:store.fields()){ids.add(f.id());names.add(f.name());}if(a!=null&&!ids.contains(a.field_id())){ids.add(a.field_id());names.add(activityField(a.field_id()));}var field=choice(form,words("Αγροτεμάχιο","Field"),names,a==null?0:ids.indexOf(a.field_id()));
        var work_type=input(form,words("Εργασία *","Work type *"),a==null?"":a.work_type(),InputType.TYPE_CLASS_TEXT);
        var hours=input(form,words("Ώρες *","Hours *"),a==null?"0":quantity(a.hours()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var hourly_rate=input(form,words("Ωρομίσθιο €","Hourly rate €"),a==null?quantity(workers.get(wi).default_hourly_rate()):quantity(a.hourly_rate()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        var notes=input(form,words("Σημειώσεις","Notes"),a==null?"":a.notes(),InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        var total=new TextView(this);total.setTextSize(18);form.addView(total);Runnable update=()->{try{total.setText(words("Κόστος: ","Cost: ")+euros(java.math.BigDecimal.valueOf(decimal(hours)*decimal(hourly_rate))));}catch(Exception e){total.setText(words("Έλεγξε ώρες και ωρομίσθιο.","Check hours and hourly rate."));}};var watcher=new android.text.TextWatcher(){public void beforeTextChanged(CharSequence s,int start,int count,int after){}public void onTextChanged(CharSequence s,int start,int before,int count){update.run();}public void afterTextChanged(android.text.Editable e){}};hours.addTextChangedListener(watcher);hourly_rate.addTextChangedListener(watcher);update.run();
        final int[] lastWorker={wi};worker.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){public void onItemSelected(AdapterView<?> parent,android.view.View view,int pos,long id){if(lastWorker[0]!=pos){hourly_rate.setText(quantity(workers.get(pos).default_hourly_rate()));lastWorker[0]=pos;}}public void onNothingSelected(AdapterView<?> parent){}});
        saveForm(words("Εργατικά & Προσωπικό","Labor & Personnel"),form,()->work().saveLabor(new WorkStore.Labor(a==null?null:a.id(),date.getText().toString().trim(),ids.get(field.getSelectedItemPosition()),workers.get(worker.getSelectedItemPosition()).id(),work_type.getText().toString().trim(),decimal(hours),decimal(hourly_rate),0,notes.getText().toString(),"")));
    }
    private ActivityStore activities(){return new ActivityStore(store);}
    private String activityLabel(String value){return switch(value){case "Πότισμα"->words(value,"Irrigation");case "Λίπανση"->words(value,"Fertilization");case "Προγραμματισμένη"->words(value,"Planned");case "Ολοκληρώθηκε"->words(value,"Completed");case "Ακυρώθηκε"->words(value,"Cancelled");default->value;};}
    private String activityField(String id){return store.fields().stream().filter(f->f.id().equals(id)).map(FarmStore.Field::name).findFirst().orElse(id.isEmpty()?words("Χωρίς αγροτεμάχιο","No field"):words("Διαγραμμένο αγροτεμάχιο","Deleted field"));}
    private void activityFilter(String title,java.util.List<String> values,java.util.function.Consumer<String> selected){var options=new java.util.ArrayList<String>();options.add("");options.addAll(values);new AlertDialog.Builder(this).setTitle(title).setItems(options.stream().map(x->x.isEmpty()?words("Όλα","All"):activityLabel(x)).toArray(String[]::new),(d,n)->{selected.accept(options.get(n));showHome();}).show();}
    private void showActivities(){
        text("Άρδευση & Λίπανση",28,true);
        action(words("+ Νέα εργασία","+ New activity"),()->editActivity(null),true);
        action(words("Αναζήτηση: ","Search: ")+activityQuery,()->{var q=new EditText(this);q.setText(activityQuery);new AlertDialog.Builder(this).setTitle(words("Αγροτεμάχιο, προϊόν, υπεύθυνος ή σημειώσεις","Field, product, responsible person or notes")).setView(q).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Εντάξει"),(d,w)->{activityQuery=q.getText().toString().trim();showHome();}).show();},false);
        var years=new java.util.TreeSet<String>(java.util.Comparator.reverseOrder());for(var a:activities().activities())years.add(a.date().substring(0,4));
        action(words("Έτος: ","Year: ")+(activityYear.isEmpty()?words("Όλα","All"):activityYear),()->activityFilter(words("Έτος","Year"),new java.util.ArrayList<>(years),x->activityYear=x),false);
        action(words("Είδος: ","Type: ")+(activityCategory.isEmpty()?words("Όλα","All"):activityLabel(activityCategory)),()->activityFilter(words("Είδος εργασίας","Activity type"),ActivityStore.CATEGORIES,x->activityCategory=x),false);
        action(words("Κατάσταση: ","Status: ")+(activityStatus.isEmpty()?words("Όλα","All"):activityLabel(activityStatus)),()->activityFilter(words("Κατάσταση","Status"),ActivityStore.STATUSES,x->activityStatus=x),false);
        var visible=activities().activities().stream().filter(a->(activityYear.isEmpty()||a.date().startsWith(activityYear+"-"))&&(activityCategory.isEmpty()||a.category().equals(activityCategory))&&(activityStatus.isEmpty()||a.status().equals(activityStatus))&&(activityField(a.fieldId())+" "+a.product()+" "+a.responsible()+" "+a.description()+" "+a.notes()).toLowerCase(Locale.ROOT).contains(activityQuery.toLowerCase(Locale.ROOT))).toList();
        java.math.BigDecimal cost=java.math.BigDecimal.ZERO;for(var a:visible)cost=cost.add(java.math.BigDecimal.valueOf(a.cost()));
        textValue(visible.size()+words(" εργασίες · κόστος "," activities · cost ")+euros(cost),19,true);
        text(words("Το κόστος καταγράφεται στην εργασία και δεν δημιουργεί αυτόματα εγγραφή στα Έξοδα.","Activity cost does not automatically create an Expenses entry."),14,false);
        for(var a:visible){textValue(a.date()+" · "+activityLabel(a.category()),20,true);textValue(activityField(a.fieldId())+" · "+activityLabel(a.status()),16,false);textValue(a.category().equals("Πότισμα")?quantity(a.duration())+" min · "+quantity(a.water())+" m³":a.product()+" · "+quantity(a.dose())+" "+a.doseUnit(),17,false);action(words("Στοιχεία εργασίας","Activity details"),()->activityDetails(a),false);}
        if(visible.isEmpty())text(words("Δεν βρέθηκαν εργασίες.","No activities found."),17,false);
    }
    private void activityDetails(ActivityStore.Activity a){
        var item=inventory().items().stream().filter(x->x.id().equals(a.itemId())).findFirst().orElse(null);
        String body=a.date()+"\n"+activityLabel(a.category())+" · "+activityLabel(a.status())+"\n"+activityField(a.fieldId())+"\n"+words("Διάρκεια: ","Duration: ")+quantity(a.duration())+" min\n"+words("Νερό: ","Water: ")+quantity(a.water())+" m³\n"+a.product()+" · "+quantity(a.dose())+" "+a.doseUnit()+"\n"+words("Κόστος: ","Cost: ")+euros(java.math.BigDecimal.valueOf(a.cost()))+"\n"+words("Υπεύθυνος: ","Responsible: ")+a.responsible()+"\n"+words("Κατανάλωση αποθήκης: ","Inventory consumption: ")+quantity(ActivityStore.consumption(a))+" "+(item==null?"":item.unit()+" · "+item.name())+"\n"+a.description()+"\n"+(a.quantity()>0?quantity(a.quantity())+" "+a.unit()+"\n":"")+a.notes();
        if(!a.windowsId().isEmpty())body+="\n\n"+words("Ιστορικό από Windows","Windows history");
        var dialog=new AlertDialog.Builder(this).setTitle(words("Στοιχεία εργασίας","Activity details")).setMessage(body).setNegativeButton(t("Κλείσιμο"),null);
        if(a.windowsId().isEmpty()){dialog.setPositiveButton(t("Επεξεργασία"),(d,w)->editActivity(a));dialog.setNeutralButton(t("Διαγραφή"),(d,w)->new AlertDialog.Builder(this).setMessage(words("Να διαγραφεί η εργασία και να επιστραφεί η κατανάλωσή της στην αποθήκη;","Delete the activity and return its consumption to inventory?")).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Διαγραφή"),(x,y)->inventoryAction(()->activities().delete(a.id()))).show());}
        dialog.show();
    }
    private void editActivity(ActivityStore.Activity a){
        var form=new LinearLayout(this);form.setOrientation(LinearLayout.VERTICAL);form.setPadding(dp(20),dp(8),dp(20),0);
        var date=input(form,words("Ημερομηνία (YYYY-MM-DD) *","Date (YYYY-MM-DD) *"),a==null?java.time.LocalDate.now().toString():a.date(),InputType.TYPE_CLASS_TEXT);
        var fieldIds=new java.util.ArrayList<String>();var fieldNames=new java.util.ArrayList<String>();fieldIds.add("");fieldNames.add(words("Χωρίς αγροτεμάχιο","No field"));for(var f:store.fields()){fieldIds.add(f.id());fieldNames.add(f.name());}if(a!=null&&!fieldIds.contains(a.fieldId())){fieldIds.add(a.fieldId());fieldNames.add(activityField(a.fieldId()));}
        var field=choice(form,words("Αγροτεμάχιο","Field"),fieldNames,a==null?0:fieldIds.indexOf(a.fieldId()));
        var category=choice(form,words("Είδος εργασίας","Activity type"),ActivityStore.CATEGORIES.stream().map(this::activityLabel).toList(),a==null?0:ActivityStore.CATEGORIES.indexOf(a.category()));
        var status=choice(form,words("Κατάσταση","Status"),ActivityStore.STATUSES.stream().map(this::activityLabel).toList(),a==null?1:ActivityStore.STATUSES.indexOf(a.status()));
        int num=InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL;
        var duration=input(form,words("Διάρκεια (λεπτά)","Duration (minutes)"),a==null?"0":quantity(a.duration()),num);var water=input(form,words("Ποσότητα νερού (m³)","Water quantity (m³)"),a==null?"0":quantity(a.water()),num);
        var product=input(form,words("Προϊόν λίπανσης","Fertilizer product"),a==null?"":a.product(),InputType.TYPE_CLASS_TEXT);var dose=input(form,words("Δόση","Dose"),a==null?"0":quantity(a.dose()),num);var unit=input(form,words("Μονάδα δόσης","Dose unit"),a==null?"kg":a.doseUnit(),InputType.TYPE_CLASS_TEXT);
        var itemIds=new java.util.ArrayList<String>();var itemNames=new java.util.ArrayList<String>();itemIds.add("");itemNames.add(words("Χωρίς κατανάλωση αποθήκης","No inventory consumption"));for(var i:inventory().items()){itemIds.add(i.id());itemNames.add(i.name()+" · "+quantity(inventory().stock(i.id()))+" "+i.unit());}if(a!=null&&!itemIds.contains(a.itemId())){itemIds.add(a.itemId());itemNames.add(words("Διαγραμμένο είδος","Deleted item"));}
        var item=choice(form,words("Είδος αποθήκης","Inventory item"),itemNames,a==null?0:itemIds.indexOf(a.itemId()));var amount=input(form,words("Ποσότητα αποθήκης (μονάδα είδους)","Inventory quantity (item unit)"),a==null?"0":quantity(a.inventoryQuantity()),num);
        var cost=input(form,words("Κόστος €","Cost €"),a==null?"0":quantity(a.cost()),num);var responsible=input(form,words("Υπεύθυνος","Responsible person"),a==null?"":a.responsible(),InputType.TYPE_CLASS_TEXT);var notes=input(form,words("Σημειώσεις","Notes"),a==null?"":a.notes(),InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        Runnable update=()->{boolean irrigation=category.getSelectedItemPosition()==0;duration.setEnabled(irrigation);water.setEnabled(irrigation);product.setEnabled(!irrigation);dose.setEnabled(!irrigation);unit.setEnabled(!irrigation);item.setEnabled(!irrigation);amount.setEnabled(!irrigation);};
        category.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){public void onItemSelected(AdapterView<?> parent,android.view.View view,int position,long id){update.run();}public void onNothingSelected(AdapterView<?> parent){}});update.run();
        saveForm(t("Άρδευση & Λίπανση"),form,()->{boolean irrigation=category.getSelectedItemPosition()==0;activities().save(new ActivityStore.Activity(a==null?null:a.id(),date.getText().toString().trim(),fieldIds.get(field.getSelectedItemPosition()),ActivityStore.CATEGORIES.get(category.getSelectedItemPosition()),ActivityStore.STATUSES.get(status.getSelectedItemPosition()),irrigation?decimal(duration):0,irrigation?decimal(water):0,irrigation?"":product.getText().toString().trim(),irrigation?0:decimal(dose),irrigation?"":unit.getText().toString().trim(),decimal(cost),responsible.getText().toString().trim(),notes.getText().toString(),irrigation?"":itemIds.get(item.getSelectedItemPosition()),irrigation?0:decimal(amount),a==null?0:a.quantity(),a==null?"":a.unit(),a==null?"":a.description(),"",""));});
    }
    private ProductionStore production(){return new ProductionStore(store);}
    private String productionProduct(String id,String fallback){return catalog().products().stream().filter(p->p.id().equals(id)).map(CatalogStore.Product::name).findFirst().orElse(fallback);}
    private String productionUnit(String id){return catalog().products().stream().filter(p->p.id().equals(id)).map(CatalogStore.Product::unit).findFirst().orElse("");}
    private boolean productionMatch(String date,String value){return (productionYear.isEmpty()||date.startsWith(productionYear+"-"))&&value.toLowerCase(Locale.ROOT).contains(productionQuery.toLowerCase(Locale.ROOT));}
    private void showProduction(boolean sales){
        text(sales?"Πωλήσεις Παραγωγής":"Παραγωγή",28,true);
        action(words(sales?"+ Νέα πώληση":"+ Νέα παραγωγή",sales?"+ New sale":"+ New production"),()->{if(sales)editSale(null);else editHarvest(null);},true);
        action(words("Αναζήτηση: ","Search: ")+productionQuery,()->{var q=new EditText(this);q.setText(productionQuery);new AlertDialog.Builder(this).setTitle(words("Προϊόν, σημειώσεις ή αγοραστής","Product, notes or buyer")).setView(q).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Εντάξει"),(d,w)->{productionQuery=q.getText().toString().trim();showHome();}).show();},false);
        var years=new java.util.TreeSet<String>(java.util.Comparator.reverseOrder());if(sales)for(var sale:production().sales())years.add(sale.date().substring(0,4));else for(var h:production().harvests())years.add(h.date().substring(0,4));var choices=new java.util.ArrayList<String>();choices.add("");choices.addAll(years);
        action(words("Έτος: ","Year: ")+(productionYear.isEmpty()?words("Όλα","All"):productionYear),()->new AlertDialog.Builder(this).setTitle(words("Επιλογή έτους","Select year")).setItems(choices.stream().map(y->y.isEmpty()?words("Όλα","All"):y).toArray(String[]::new),(d,n)->{productionYear=choices.get(n);showHome();}).show(),false);
        text(words("Διαθέσιμη παραγωγή · όλα τα έτη","Available production · all years"),20,true);
        for(var p:catalog().products()){double produced=production().produced(p.id()),sold=production().sold(p.id());if(produced==0&&sold==0)continue;textValue(p.name()+": "+quantity(produced-sold)+" "+p.unit()+words(" διαθέσιμα (παραγωγή "," available (produced ")+quantity(produced)+words(", πωλήσεις ",", sold ")+quantity(sold)+")",16,false);}
        int visible=0;
        if(sales){java.math.BigDecimal total=java.math.BigDecimal.ZERO;for(var sale:production().sales()){String product=productionProduct(sale.productId(),sale.productName());if(!productionMatch(sale.date(),product+" "+sale.buyerName()+" "+sale.notes()))continue;visible++;total=total.add(java.math.BigDecimal.valueOf(sale.total()));textValue(sale.date()+" · "+product,20,true);textValue(quantity(sale.quantity())+" "+productionUnit(sale.productId())+" · "+euros(java.math.BigDecimal.valueOf(sale.total())),18,false);textValue(sale.buyerName(),16,false);action(words("Στοιχεία πώλησης","Sale details"),()->saleDetails(sale),false);}textValue(words("Σύνολο πωλήσεων φίλτρου: ","Filtered sales total: ")+euros(total),19,true);}
        else for(var h:production().harvests()){String product=productionProduct(h.productId(),h.productName());if(!productionMatch(h.date(),product+" "+h.notes()))continue;visible++;textValue(h.date()+" · "+product,20,true);textValue(quantity(h.quantity())+" "+productionUnit(h.productId()),18,false);textValue(store.fields().stream().filter(f->f.id().equals(h.fieldId())).map(FarmStore.Field::name).findFirst().orElse(h.fieldId().isEmpty()?words("Χωρίς αγροτεμάχιο","No field"):words("Διαγραμμένο αγροτεμάχιο","Deleted field")),16,false);textValue(h.notes(),15,false);if(!h.windowsId().isEmpty())text(words("Ιστορικό από Windows","Windows history"),14,false);else{action("Επεξεργασία",()->editHarvest(h),false);action(words("Διαγραφή παραγωγής","Delete production"),()->new AlertDialog.Builder(this).setMessage(words("Να διαγραφεί η παραγωγή;","Delete production?")).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Διαγραφή"),(d,w)->productionAction(()->production().deleteHarvest(h.id()))).show(),false);}}
        if(visible==0)text(words("Δεν βρέθηκαν εγγραφές.","No records found."),16,false);
    }
    private void productionAction(Runnable run){try{run.run();showHome();}catch(IllegalArgumentException error){backupMessage(words("Έλεγξε τη διαθέσιμη παραγωγή και τις συνδεδεμένες εγγραφές. Το εισαγόμενο ιστορικό δεν αλλάζει.","Check available production and linked records. Imported history cannot be changed."));}catch(Exception error){backupMessage(words("Η ενέργεια απέτυχε.","The action failed."));}}
    private java.util.List<CatalogStore.Product> productionProducts(String existing){return catalog().products().stream().filter(p->p.active()||p.id().equals(existing)).toList();}
    private void editHarvest(ProductionStore.Harvest h){
        var products=productionProducts(h==null?"":h.productId());var fields=store.fields();if(products.isEmpty()||fields.isEmpty()){backupMessage(words("Πρόσθεσε πρώτα προϊόν και αγροτεμάχιο.","Add a product and field first."));return;}
        var form=new LinearLayout(this);form.setOrientation(LinearLayout.VERTICAL);form.setPadding(dp(20),dp(8),dp(20),0);
        var date=input(form,words("Ημερομηνία (YYYY-MM-DD) *","Date (YYYY-MM-DD) *"),h==null?java.time.LocalDate.now().toString():h.date(),InputType.TYPE_CLASS_TEXT);
        int productIndex=0,fieldIndex=0;for(int n=0;n<products.size();n++)if(h!=null&&products.get(n).id().equals(h.productId()))productIndex=n;for(int n=0;n<fields.size();n++)if(h!=null&&fields.get(n).id().equals(h.fieldId()))fieldIndex=n;
        if(h!=null&&fields.stream().noneMatch(f->f.id().equals(h.fieldId()))){backupMessage(words("Το αγροτεμάχιο έχει διαγραφεί. Η ιστορική παραγωγή διατηρείται.","The field was deleted. Historical production is retained."));return;}
        var product=choice(form,words("Προϊόν","Product"),products.stream().map(CatalogStore.Product::toString).toList(),productIndex);product.setEnabled(h==null);var field=choice(form,words("Αγροτεμάχιο","Field"),fields.stream().map(FarmStore.Field::name).toList(),fieldIndex);
        var amount=input(form,words("Ποσότητα *","Quantity *"),h==null?"":quantity(h.quantity()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);var notes=input(form,words("Σημειώσεις","Notes"),h==null?"":h.notes(),InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        saveForm(t("Παραγωγή"),form,()->{var p=products.get(product.getSelectedItemPosition());production().saveHarvest(new ProductionStore.Harvest(h==null?null:h.id(),date.getText().toString().trim(),p.id(),p.name(),fields.get(field.getSelectedItemPosition()).id(),decimal(amount),notes.getText().toString(),""));});
    }
    private void editSale(ProductionStore.Sale sale){
        var products=productionProducts(sale==null?"":sale.productId());if(products.isEmpty()){backupMessage(words("Πρόσθεσε πρώτα προϊόν και παραγωγή.","Add a product and production first."));return;}
        var form=new LinearLayout(this);form.setOrientation(LinearLayout.VERTICAL);form.setPadding(dp(20),dp(8),dp(20),0);var date=input(form,words("Ημερομηνία (YYYY-MM-DD) *","Date (YYYY-MM-DD) *"),sale==null?java.time.LocalDate.now().toString():sale.date(),InputType.TYPE_CLASS_TEXT);
        int index=0;for(int n=0;n<products.size();n++)if(sale!=null&&products.get(n).id().equals(sale.productId()))index=n;var product=choice(form,words("Προϊόν","Product"),products.stream().map(p->p.toString()+" · "+quantity(production().available(p.id()))+words(" διαθέσιμα"," available")).toList(),index);product.setEnabled(sale==null);
        var buyerIds=new java.util.ArrayList<String>();var buyerNames=new java.util.ArrayList<String>();buyerIds.add("");buyerNames.add(words("Χωρίς σύνδεση αγοραστή","No linked buyer"));for(var p:partners().partners())if(!p.type().equals("supplier")||(sale!=null&&p.id().equals(sale.buyerId()))){buyerIds.add(p.id());buyerNames.add(p.name());}if(sale!=null&&!buyerIds.contains(sale.buyerId())){buyerIds.add(sale.buyerId());buyerNames.add(sale.buyerName());}
        var buyer=choice(form,words("Αγοραστής","Buyer"),buyerNames,sale==null?0:buyerIds.indexOf(sale.buyerId()));var buyerName=input(form,words("Όνομα αγοραστή χωρίς σύνδεση","Unlinked buyer name"),sale==null?"":sale.buyerName(),InputType.TYPE_CLASS_TEXT);
        var amount=input(form,words("Ποσότητα *","Quantity *"),sale==null?"":quantity(sale.quantity()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);var price=input(form,words("Τιμή ανά μονάδα € *","Price per unit € *"),sale==null?"0":quantity(sale.price()),InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);var payment=input(form,words("Τρόπος πληρωμής","Payment method"),sale==null?"":sale.payment(),InputType.TYPE_CLASS_TEXT);var notes=input(form,words("Σημειώσεις","Notes"),sale==null?"":sale.notes(),InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        saveForm(t("Πωλήσεις Παραγωγής"),form,()->{var p=products.get(product.getSelectedItemPosition());String buyerId=buyerIds.get(buyer.getSelectedItemPosition());double q=decimal(amount),unitPrice=decimal(price);production().saveSale(new ProductionStore.Sale(sale==null?null:sale.id(),date.getText().toString().trim(),p.id(),p.name(),buyerId,buyerId.isEmpty()?buyerName.getText().toString():buyerNames.get(buyer.getSelectedItemPosition()),q,unitPrice,q*unitPrice,payment.getText().toString(),notes.getText().toString(),"",""));});
    }
    private void saleDetails(ProductionStore.Sale s){
        String body=s.date()+"\n"+productionProduct(s.productId(),s.productName())+"\n"+s.buyerName()+"\n"+quantity(s.quantity())+" "+productionUnit(s.productId())+" × "+euros(java.math.BigDecimal.valueOf(s.price()))+"\n"+euros(java.math.BigDecimal.valueOf(s.total()))+"\n"+s.payment()+"\n\n"+s.notes();var dialog=new AlertDialog.Builder(this).setTitle(t("Πωλήσεις Παραγωγής")).setMessage(body).setNegativeButton(t("Κλείσιμο"),null);
        if(s.windowsId().isEmpty()){dialog.setPositiveButton(t("Επεξεργασία"),(d,w)->editSale(s));dialog.setNeutralButton(t("Διαγραφή"),(d,w)->new AlertDialog.Builder(this).setMessage(words("Να διαγραφεί η πώληση και το συνδεδεμένο έσοδο;","Delete sale and its linked income?")).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Διαγραφή"),(a,b)->productionAction(()->production().deleteSale(s.id()))).show());}dialog.show();
    }
    private void showProducts() {
        text("Προϊόντα",28,true);
        action(words("+ Νέο προϊόν","+ New product"),()->editProduct(null),true);
        action(words("Αναζήτηση: ","Search: ")+productQuery,()-> {
            var query=new EditText(this); query.setText(productQuery);
            new AlertDialog.Builder(this).setTitle(words("Αναζήτηση προϊόντος","Find product")).setView(query).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Εντάξει"),(d,w)->{productQuery=query.getText().toString().trim();showHome();}).show();
        },false);
        action(words("Κατάσταση: ","Status: ")+new String[]{words("Όλα","All"),words("Ενεργά","Active"),words("Ανενεργά","Inactive")}[productFilter],()->{productFilter=(productFilter+1)%3;showHome();},false);
        var products=catalog().products(); int visible=0;
        for(var p:products) {
            if(!p.name().toLowerCase(Locale.ROOT).contains(productQuery.toLowerCase(Locale.ROOT)) || (productFilter==1&&!p.active()) || (productFilter==2&&p.active())) continue;
            visible++; textValue(p.name()+" ("+p.unit()+")",21,true); text(p.active()?words("Ενεργό","Active"):words("Ανενεργό","Inactive"),15,false);
            action("Επεξεργασία",()->editProduct(p),false);
            action(words("Καλλιέργειες / αγροτεμάχια","Cultivations / fields"),()->showLinks(p),false);
        }
        if(visible==0) text(words("Δεν βρέθηκαν προϊόντα.","No products found."),16,false);
    }
    private void editProduct(CatalogStore.Product p) {
        var form=new LinearLayout(this); form.setOrientation(LinearLayout.VERTICAL); form.setPadding(dp(20),dp(8),dp(20),0);
        var name=input(form,words("Όνομα προϊόντος *","Product name *"),p==null?"":p.name(),InputType.TYPE_CLASS_TEXT);
        var unit=input(form,words("Μονάδα μέτρησης *","Unit *"),p==null?"kg":p.unit(),InputType.TYPE_CLASS_TEXT);
        var active=new CheckBox(this); active.setText(words("Ενεργό προϊόν","Active product")); active.setChecked(p==null || p.active()); form.addView(active);
        saveForm(t("Προϊόντα"),form,()->catalog().saveProduct(p==null?null:p.id(),name.getText().toString(),unit.getText().toString(),active.isChecked()));
    }
    private void showLinks(CatalogStore.Product product) {
        var labels=new java.util.ArrayList<String>(); var links=new java.util.ArrayList<CatalogStore.Link>();
        for(var link:catalog().links()) if(link.productId().equals(product.id())) {
            String name=store.fields().stream().filter(f->f.id().equals(link.fieldId())).map(FarmStore.Field::name).findFirst().orElse(words("Διαγραμμένο αγροτεμάχιο","Deleted field"));
            labels.add(name+" · "+link.variety()+" · "+link.plantingDate()+" · "+(link.status().equals("active")?words("Ενεργή","Active"):words("Ανενεργή","Inactive"))); links.add(link);
        }
        new AlertDialog.Builder(this).setTitle(product.name()).setItems(labels.toArray(new String[0]),(d,index)-> {
            var link=links.get(index);
            new AlertDialog.Builder(this).setItems(new String[]{t("Επεξεργασία"),words("Αφαίρεση σύνδεσης","Remove link")},(a,which)-> {
                if(which==0) editLink(product,link);
                else new AlertDialog.Builder(this).setMessage(words("Να αφαιρεθεί η σύνδεση καλλιέργειας;","Remove this cultivation link?")).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Διαγραφή"),(x,y)->{catalog().removeLink(link.id());showHome();}).show();
            }).show();
        }).setPositiveButton(words("Νέα σύνδεση","New link"),(d,w)->editLink(product,null)).setNegativeButton(t("Κλείσιμο"),null).show();
    }
    private void editLink(CatalogStore.Product product,CatalogStore.Link link) {
        var fields=store.fields(); if(fields.isEmpty()) { backupMessage(words("Πρόσθεσε πρώτα αγροτεμάχιο.","Add a field first.")); return; }
        if(link!=null && fields.stream().noneMatch(f->f.id().equals(link.fieldId()))) { backupMessage(words("Το αγροτεμάχιο έχει διαγραφεί. Μπορείς να αφαιρέσεις τη σύνδεση.","The field was deleted. You can remove this link.")); return; }
        var form=new LinearLayout(this); form.setOrientation(LinearLayout.VERTICAL); form.setPadding(dp(20),dp(8),dp(20),0);
        var chooser=new Spinner(this); chooser.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,fields.stream().map(FarmStore.Field::name).toArray(String[]::new))); form.addView(chooser);
        if(link!=null) { for(int i=0;i<fields.size();i++) if(fields.get(i).id().equals(link.fieldId())) chooser.setSelection(i); chooser.setEnabled(false); }
        var variety=input(form,words("Ποικιλία","Variety"),link==null?"":link.variety(),InputType.TYPE_CLASS_TEXT);
        var date=input(form,words("Φύτευση / έναρξη (YYYY-MM-DD, προαιρετικό)","Planting / start (YYYY-MM-DD, optional)"),link==null?"":link.plantingDate(),InputType.TYPE_CLASS_TEXT);
        var active=new CheckBox(this); active.setText(words("Ενεργή καλλιέργεια","Active cultivation")); active.setChecked(link==null||link.status().equals("active")); form.addView(active);
        saveForm(product.name(),form,()-> {
            String fieldId=fields.get(chooser.getSelectedItemPosition()).id();
            if(link==null && catalog().links().stream().anyMatch(l->l.productId().equals(product.id())&&l.fieldId().equals(fieldId))) throw new UiValidationException(words("Υπάρχει ήδη σύνδεση με αυτό το αγροτεμάχιο.","This field is already linked."));
            catalog().saveLink(product.id(),fieldId,variety.getText().toString(),date.getText().toString().trim(),active.isChecked()?"active":"inactive");
        });
    }
    private EditText input(LinearLayout form, String label, String value, int type) {
        TextView caption = new TextView(this); caption.setText(t(label)); form.addView(caption);
        EditText edit = new EditText(this); edit.setText(value); edit.setContentDescription(t(label)); edit.setInputType(type); form.addView(edit); return edit;
    }
    private void editField(FarmStore.Field field) {
        LinearLayout form = new LinearLayout(this); form.setOrientation(LinearLayout.VERTICAL); form.setPadding(dp(24),dp(8),dp(24),0);
        EditText name = input(form,"Όνομα αγροτεμαχίου *",field == null ? "" : field.name(),InputType.TYPE_CLASS_TEXT);
        EditText area = input(form,"Έκταση σε στρέμματα *",field == null ? "" : String.valueOf(field.area()),InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        EditText kaek = input(form,"ΚΑΕΚ",field == null ? "" : field.kaek(),InputType.TYPE_CLASS_TEXT);
        EditText location = input(form,"Τοποθεσία",field == null ? "" : field.location(),InputType.TYPE_CLASS_TEXT);
        EditText trees = input(form,"Παραγωγικά δέντρα",field == null ? "0" : String.valueOf(field.trees()),InputType.TYPE_CLASS_NUMBER);
        EditText notes = input(form,"Σημειώσεις",field == null ? "" : field.notes(),InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        ScrollView formScroll = new ScrollView(this); formScroll.addView(form);
        AlertDialog.Builder builder = new AlertDialog.Builder(this).setTitle(t(field == null ? "Νέο αγροτεμάχιο" : "Επεξεργασία αγροτεμαχίου")).setView(formScroll).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Αποθήκευση"),null);
        if (field != null) builder.setNeutralButton(t("Διαγραφή"),(d,w) -> new AlertDialog.Builder(this).setTitle(t("Διαγραφή αγροτεμαχίου;")).setMessage(words("Να διαγραφεί το «","Delete “") + field.name() + words("»;","”? ")).setNegativeButton(t("Ακύρωση"),(a,b) -> editField(field)).setPositiveButton(t("Διαγραφή"),(a,b) -> {
            try { store.deleteField(field.id()); showHome(); }
            catch (RuntimeException error) { Toast.makeText(this,t("Δεν διαγράφηκε. Δοκίμασε ξανά."),Toast.LENGTH_LONG).show(); }
        }).show());
        AlertDialog dialog = builder.create();
        dialog.setOnShowListener(v -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(button -> {
            try {
                if (name.getText().toString().trim().isEmpty()) { name.setError(t("Χρειάζεται όνομα.")); return; }
                double areaValue;
                try { areaValue = Double.parseDouble(area.getText().toString().trim().replace(',', '.')); if (!Double.isFinite(areaValue) || areaValue < 0) throw new NumberFormatException(); }
                catch (NumberFormatException error) { area.setError(t("Χρειάζεται έγκυρη μη αρνητική έκταση.")); return; }
                int treeValue;
                try { treeValue = Integer.parseInt(trees.getText().toString().trim()); if (treeValue < 0) throw new NumberFormatException(); }
                catch (NumberFormatException error) { trees.setError(t("Χρειάζεται ακέραιος αριθμός από 0 και πάνω.")); return; }
                store.saveField(field == null ? null : field.id(),name.getText().toString(),areaValue,kaek.getText().toString(),location.getText().toString(),treeValue,notes.getText().toString());
                dialog.dismiss(); showHome();
            } catch (IllegalArgumentException error) { area.setError(t("Συμπλήρωσε όνομα και έγκυρη έκταση.")); }
            catch (android.database.SQLException error) { Toast.makeText(this,t("Δεν αποθηκεύτηκε. Δοκίμασε ξανά."),Toast.LENGTH_LONG).show(); }
        })); dialog.show();
    }
    private void sessionTimeout(){
        int[] minutes={1,5,15,30};String[] labels=java.util.Arrays.stream(minutes).mapToObj(n->n+words(n==1?" λεπτό":" λεπτά",n==1?" minute":" minutes")).toArray(String[]::new);
        new AlertDialog.Builder(this).setTitle(words("Χρόνος στο παρασκήνιο πριν τη σύνδεση","Background time before sign-in")).setSingleChoiceItems(labels,java.util.Arrays.binarySearch(minutes,UserSession.timeoutMinutes(this)),(d,index)->{UserSession.setTimeoutMinutes(this,minutes[index]);d.dismiss();showHome();}).setNegativeButton(t("Ακύρωση"),null).show();
    }
    private void changePassword() {
        LinearLayout form=new LinearLayout(this); form.setOrientation(LinearLayout.VERTICAL); form.setPadding(dp(24),dp(8),dp(24),0);
        int type=InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD;
        EditText old=input(form,"Τρέχων κωδικός","",type), next=input(form,"Νέος κωδικός","",type), repeat=input(form,"Επιβεβαίωση κωδικού","",type);
        for(EditText edit:new EditText[]{old,next,repeat}) { edit.setSaveEnabled(false); edit.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(128)}); }
        var scroll=new ScrollView(this); scroll.addView(form);
        var dialog=new AlertDialog.Builder(this).setTitle(t("Αλλαγή κωδικού")).setView(scroll).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Αποθήκευση"),null).create();
        dialog.setOnShowListener(v->dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(w->{
            if(!next.getText().toString().equals(repeat.getText().toString())) { repeat.setError(t("Οι κωδικοί δεν ταιριάζουν.")); return; }
            char[] before=old.getText().toString().toCharArray(),after=next.getText().toString().toCharArray();
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(false); dialog.getButton(AlertDialog.BUTTON_NEGATIVE).setEnabled(false); dialog.setCancelable(false);
            new Thread(()-> {
                String problem=null;
                try(var registry=new ProfileStore(this)) { registry.changePassword(profile,before,after); }
                catch(IllegalArgumentException ex) { problem=t(ex.getMessage()); }
                catch(Exception ex) { problem=t("Η ενέργεια απέτυχε. Δοκίμασε ξανά."); }
                finally { java.util.Arrays.fill(before,'\0'); java.util.Arrays.fill(after,'\0'); }
                String message=problem;
                runOnUiThread(()-> {
                    if(isFinishing() || isDestroyed()) return;
                    dialog.dismiss(); backupMessage(message==null?t("Ο κωδικός άλλαξε."):message);
                });
            },"password-change").start();
        })); dialog.show(); dialog.getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE);
    }
    @Override protected void onResume() {
        super.onResume(); if(!isFinishing() && (!UserSession.valid(this) || profile==null || !UserSession.profile.id().equals(profile.id()))) logout();
    }
    @Override protected void onDestroy() { if(activeOcrDialog!=null)activeOcrDialog.dismiss();ocrExecutor.shutdown(); if(store!=null) store.close(); super.onDestroy(); }
    private String documentQuery="",documentYear="",pendingDocument="";
    private String reportFrom="",reportTo="",reportField="",reportProduct="",reportBuyer="";
    private final java.util.concurrent.ExecutorService ocrExecutor=java.util.concurrent.Executors.newSingleThreadExecutor();
    private boolean ocrBusy=false;
    private AlertDialog activeOcrDialog;
    private DocumentStore documents(){return new DocumentStore(store);}
    private void chooseDocument(int request){startActivityForResult(new android.content.Intent(android.content.Intent.ACTION_OPEN_DOCUMENT).addCategory(android.content.Intent.CATEGORY_OPENABLE).setType("*/*").putExtra(android.content.Intent.EXTRA_MIME_TYPES,new String[]{"image/*","application/pdf"}),request);}
    private void exportFile(int request,String name,String mime){startActivityForResult(new android.content.Intent(android.content.Intent.ACTION_CREATE_DOCUMENT).addCategory(android.content.Intent.CATEGORY_OPENABLE).setType(mime).putExtra(android.content.Intent.EXTRA_TITLE,name),request);}
    private String fileName(android.net.Uri uri){try(var c=getContentResolver().query(uri,new String[]{android.provider.OpenableColumns.DISPLAY_NAME},null,null,null)){if(c!=null&&c.moveToFirst())return c.getString(0);}throw new IllegalArgumentException("Λείπει όνομα αρχείου / Filename missing");}
    private void documentResult(int request,android.net.Uri uri)throws Exception{
        if(request==118){var rows=new java.util.ArrayList<String[]>();rows.add(new String[]{words("Προτεραιότητα","Priority"),words("Κατηγορία","Category"),words("Ημερομηνία","Date"),words("Θέμα","Subject"),words("Μήνυμα","Message")});for(var a:visibleAlerts())rows.add(new String[]{severityLabel(a.severity()),alertKindLabel(a.kind()),a.date(),a.subject(),a.message()});try(var out=getContentResolver().openOutputStream(uri,"wt")){if(out==null)throw new java.io.IOException();out.write(ReportStore.csv(rows));}backupMessage(words("Το αρχείο αποθηκεύτηκε.","File saved."));return;}
        if(request==116){java.util.List<DocumentPackage.Attachment> attachments;try(var in=getContentResolver().openInputStream(uri)){attachments=DocumentPackage.preview(store,in);}new AlertDialog.Builder(this).setTitle(words("Σύνδεση συνημμένων","Attach invoice files")).setMessage(words("Νέα συνημμένα: ","New attachments: ")+attachments.size()+words("\nΘα συνδεθούν με τα ήδη εισαγμένα τιμολόγια. Δεν δημιουργούνται οικονομικές εγγραφές. Κλειδωμένο έτος πρέπει πρώτα να ξεκλειδωθεί.","\nFiles will attach to existing imported documents. No financial entries are created. Locked years must first be unlocked.")).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Εισαγωγή"),(d,w)->{try{DocumentPackage.apply(store,attachments,recoveryFile());showHome();}catch(Exception e){backupMessage(words("Η σύνδεση συνημμένων απέτυχε. Έλεγξε το ZIP και τα υπάρχοντα τιμολόγια.","Attaching files failed. Check the ZIP and existing invoice records."));}}).show();return;}
        if(request==110||request==111){byte[] bytes;try(var in=getContentResolver().openInputStream(uri)){bytes=DocumentStore.read(in);}String name=fileName(uri);DocumentStore.mime(name);
            if(request==111){var d=documents().get(pendingDocument);if(!DocumentStore.mime(name).equals(DocumentStore.mime(d.metadata().optString("original_filename"))))throw new IllegalArgumentException("Ο τύπος αρχείου πρέπει να ταιριάζει / File type must match");documents().attach(d.id(),bytes);showHome();}
            else{String id=documents().add(name,bytes);showHome();if(currentPage.equals("Σάρωση OCR"))runOcr(id);else documentDetails(id);}return;
        }
        byte[] bytes;
        if(request==112){var d=documents().get(pendingDocument);bytes=android.util.Base64.decode(d.attachment(),android.util.Base64.DEFAULT);}
        else if(request==113||request==114||request==117){var rows=new ReportStore(store,profile.language().equals("en")).report(currentPage,reportFilter());bytes=request==113?ReportStore.csv(rows):request==117?ReportStore.xlsx(rows):ReportStore.pdf(rows);}
        else if(request==115){bytes=DocumentPackage.export(documents().list().stream().filter(this::documentMatches).toList());}
        else return;
        try(var out=getContentResolver().openOutputStream(uri,"wt")){if(out==null)throw new java.io.IOException();out.write(bytes);}backupMessage(words("Το αρχείο αποθηκεύτηκε.","File saved."));
    }
    private boolean documentMatches(DocumentStore.Document d){return (documentYear.isEmpty()||d.date().startsWith(documentYear))&&(d.metadata().toString()+d.date()).toLowerCase(java.util.Locale.ROOT).contains(documentQuery.toLowerCase(java.util.Locale.ROOT));}
    private String ocrStatusLabel(String value){return switch(value){case "pending"->words("Σε αναμονή","Pending");case "review_required"->words("Χρειάζεται έλεγχος","Review required");case "no_text"->words("Δεν βρέθηκε κείμενο","No text found");default->value;};}
    private void showDocuments(){text(currentPage,28,true);text(words("PDF και εικόνες έως 5 MB. OCR στη συσκευή, ελληνικά και αγγλικά. Έλεγξε τα στοιχεία πριν τη μεταφορά στα οικονομικά.","PDF and images up to 5 MB. On-device Greek and English OCR. Review all details before posting to finances."),16,false);
        action(words("+ Προσθήκη εγγράφου","+ Add document"),()->chooseDocument(110),true);
        action(words("Σύνδεση συνημμένων από ZIP Windows","Attach files from Windows invoice ZIP"),()->startActivityForResult(new android.content.Intent(android.content.Intent.ACTION_OPEN_DOCUMENT).addCategory(android.content.Intent.CATEGORY_OPENABLE).setType("application/zip"),116),false);
        action(words("Αναζήτηση: ","Search: ")+documentQuery,()->{var q=new EditText(this);q.setText(documentQuery);new AlertDialog.Builder(this).setTitle(words("Προμηθευτής, αριθμός ή σημειώσεις","Supplier, number or notes")).setView(q).setPositiveButton(t("Εντάξει"),(d,w)->{documentQuery=q.getText().toString().trim();showHome();}).setNegativeButton(t("Ακύρωση"),null).show();},false);
        action(words("Έτος: ","Year: ")+(documentYear.isEmpty()?words("Όλα","All"):documentYear),()->{var years=new java.util.TreeSet<String>();for(var d:documents().list())if(d.date().length()>=4)years.add(d.date().substring(0,4));activityFilter(words("Έτος","Year"),new java.util.ArrayList<>(years),v->documentYear=v);},false);
        var rows=documents().list().stream().filter(this::documentMatches).toList();text(words("Έγγραφα: ","Documents: ")+rows.size(),18,true);if(!rows.isEmpty())action(words("Εξαγωγή εμφανιζόμενων εγγράφων ZIP","Export visible documents ZIP"),()->exportFile(115,"mastixa-invoices.zip","application/zip"),false);
        for(var d:rows){action(d.date()+" · "+d.metadata().optString("supplier")+"\n"+d.metadata().optString("original_filename"),()->documentDetails(d.id()),false);text(words("Ποσό: ","Amount: ")+d.metadata().optString("amount_text")+" · "+(d.attachment().isEmpty()?words("Λείπει συνημμένο — παλαιό ZIP μεταδεδομένων","Attachment missing — legacy metadata ZIP"):words("Συνημμένο αποθηκευμένο","Attachment saved")),14,false);}
    }
    private void documentDetails(String id){var d=documents().get(id);var m=d.metadata();String body=d.date()+"\n"+m.optString("supplier")+"\n"+m.optString("invoice_number")+" · "+m.optString("amount_text")+" €\n"+m.optString("category")+"\n"+m.optString("notes")+"\nOCR: "+ocrStatusLabel(m.optString("ocr_status"))+(d.financialId().isEmpty()?"":"\n"+words("Συνδεδεμένο στα οικονομικά","Linked to finances"));
        var actions=new java.util.ArrayList<String>();actions.add(words("Στοιχεία / Επεξεργασία","Details / Edit"));actions.add(d.attachment().isEmpty()?words("Προσθήκη συνημμένου","Attach file"):words("Προβολή συνημμένου","View attachment"));actions.add(words("Αναγνώριση OCR","Run OCR"));actions.add(words("Κείμενο OCR","OCR text"));actions.add(words("Καταχώρηση στα οικονομικά","Post to finances"));actions.add(words("Αποθήκευση συνημμένου","Save attachment"));actions.add(words("Διαγραφή εγγράφου","Delete document"));if(!d.financialId().isEmpty()&&d.windowsId().isEmpty())actions.add(words("Αναίρεση οικονομικής καταχώρησης","Reverse financial posting"));
        new AlertDialog.Builder(this).setTitle(m.optString("original_filename")).setItems(actions.toArray(String[]::new),(dialog,n)->{switch(n){case 0->editDocument(id,null);case 1->{if(d.attachment().isEmpty()){pendingDocument=id;chooseDocument(111);}else viewDocument(d);}case 2->runOcr(id);case 3->{var text=new TextView(this);text.setText(m.optString("ocr_text",words("Δεν υπάρχει κείμενο","No text")));text.setTextIsSelectable(true);text.setPadding(dp(16),dp(16),dp(16),dp(16));var scroll=new ScrollView(this);scroll.addView(text);new AlertDialog.Builder(this).setTitle("OCR").setView(scroll).setPositiveButton(t("Κλείσιμο"),null).show();}case 4->{if(!d.financialId().isEmpty()){new MoneyStore(store).entries(null).stream().filter(e->e.id().equals(d.financialId())).findFirst().ifPresent(this::moneyDetails);return;}new AlertDialog.Builder(this).setTitle(words("Επιβεβαίωση οικονομικής καταχώρησης","Confirm financial posting")).setMessage(body+"\n\n"+words("Θα δημιουργηθεί μία εγγραφή εσόδου/εξόδου. Έλεγξες ημερομηνία, τύπο, προμηθευτή και τελικό ποσό;","One income/expense entry will be created. Have you reviewed date, type, supplier and final amount?")).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(words("Καταχώρηση","Post"),(x,y)->documentAction(()->documents().post(id))).show();}case 5->{if(d.attachment().isEmpty()){backupMessage(words("Λείπει συνημμένο","Attachment missing"));return;}pendingDocument=id;exportFile(112,m.optString("original_filename"),DocumentStore.mime(m.optString("original_filename")));}case 6->workDelete(words("Διαγραφή εγγράφου και συνημμένου;","Delete document and attachment?"),()->documents().delete(id));case 7->new AlertDialog.Builder(this).setMessage(words("Να αφαιρεθεί η συνδεδεμένη οικονομική εγγραφή ώστε να διορθωθεί το τιμολόγιο;","Remove the linked financial entry to correct the invoice?")).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(words("Αναίρεση","Reverse"),(x,y)->documentAction(()->documents().unpost(id))).show();}}).setNegativeButton(t("Κλείσιμο"),null).show();
    }
    private void documentAction(Runnable action){try{action.run();showHome();}catch(Exception e){backupMessage(words("Η ενέργεια απέτυχε.","Action failed."));}}
    private void editDocument(String id,org.json.JSONObject suggestions){var d=documents().get(id);var m=d.metadata();if(!d.financialId().isEmpty()){backupMessage(words("Τα στοιχεία συνδέονται ήδη με οικονομική εγγραφή. Δεν επιτρέπεται ανεξάρτητη αλλαγή.","Details are already linked to a financial entry and cannot be edited independently."));return;}var form=workForm();
        if(suggestions!=null){var hint=new TextView(this);hint.setText(words("Προτάσεις OCR — έλεγξε κάθε πεδίο πριν την αποθήκευση.","OCR suggestions — review every field before saving."));form.addView(hint);}
        var date=input(form,words("Ημερομηνία (YYYY-MM-DD)","Date (YYYY-MM-DD)"),suggestions==null?d.date():suggestions.optString("ocr_suggested_date",d.date()),InputType.TYPE_CLASS_TEXT);
        var supplier=input(form,words("Προμηθευτής / Αγοραστής","Supplier / Buyer"),suggestions==null?m.optString("supplier"):suggestions.optString("ocr_suggested_supplier",m.optString("supplier")),InputType.TYPE_CLASS_TEXT);
        var number=input(form,words("Αριθμός τιμολογίου","Invoice number"),m.optString("invoice_number"),InputType.TYPE_CLASS_TEXT);
        var amount=input(form,words("Τελικό ποσό","Final amount"),suggestions==null?m.optString("amount_text"):suggestions.optString("ocr_suggested_amount",m.optString("amount_text")),InputType.TYPE_CLASS_TEXT);
        var types=java.util.List.of("unknown","purchase","sale");var type=choice(form,words("Τύπος εγγράφου","Document type"),java.util.List.of(words("Άγνωστο","Unknown"),words("Αγορά / Έξοδο","Purchase / Expense"),words("Πώληση / Έσοδο","Sale / Income")),types.indexOf(m.optString("document_type","unknown")));
        var partnerIds=new java.util.ArrayList<String>();var labels=new java.util.ArrayList<String>();partnerIds.add("");labels.add(words("Χωρίς σύνδεση συνεργάτη","No linked partner"));for(var p:partners().partners()){partnerIds.add(p.id());labels.add(p.name());}var partner=choice(form,words("Σύνδεση συνεργάτη","Linked partner"),labels,Math.max(0,partnerIds.indexOf(m.optString("partner_id"))));
        var category=input(form,words("Κατηγορία","Category"),m.optString("category"),InputType.TYPE_CLASS_TEXT);var notes=input(form,words("Σημειώσεις","Notes"),m.optString("notes"),InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        saveForm(words("Στοιχεία τιμολογίου","Invoice details"),form,()->{try{var updated=new org.json.JSONObject(m.toString());if(suggestions!=null)for(var keys=suggestions.keys();keys.hasNext();){String key=keys.next();updated.put(key,suggestions.get(key));}String a=amount.getText().toString().trim();if(!a.isEmpty())DocumentStore.amount(a);String pid=partnerIds.get(partner.getSelectedItemPosition());updated.put("supplier",pid.isEmpty()?supplier.getText().toString():labels.get(partner.getSelectedItemPosition())).put("partner_id",pid).put("invoice_number",number.getText().toString()).put("amount_text",a).put("document_type",types.get(type.getSelectedItemPosition())).put("category",category.getText().toString()).put("notes",notes.getText().toString());documents().save(id,date.getText().toString().trim(),updated);}catch(org.json.JSONException error){throw new IllegalArgumentException(error);}});
    }
    private void runOcr(String id){var d=documents().get(id);if(ocrBusy){backupMessage(words("Η αναγνώριση είναι σε εξέλιξη.","Recognition is already running."));return;}if(d.attachment().isEmpty()||!d.financialId().isEmpty()){backupMessage(words("Χρειάζεται συνημμένο και έγγραφο χωρίς οικονομική σύνδεση.","An attachment and an unposted document are required."));return;}ocrBusy=true;var progress=new AlertDialog.Builder(this).setMessage(words("Αναγνώριση στη συσκευή… Μπορεί να διαρκέσει λίγο.","Recognizing on device… This may take a moment.")).setCancelable(false).show();activeOcrDialog=progress;String owner=profile.id();var context=getApplicationContext();ocrExecutor.execute(()->{org.json.JSONObject result=null;try{result=OfflineOcr.suggestions(OfflineOcr.recognize(context,android.util.Base64.decode(d.attachment(),android.util.Base64.DEFAULT),d.metadata().optString("original_filename")));}catch(Exception ignored){}var found=result;runOnUiThread(()->{ocrBusy=false;activeOcrDialog=null;if(!isDestroyed())progress.dismiss();if(isFinishing()||isDestroyed()||!UserSession.valid(this)||!UserSession.profile.id().equals(owner))return;if(found!=null)editDocument(id,found);else backupMessage(words("Το OCR απέτυχε. Μπορείς να συμπληρώσεις τα στοιχεία χειροκίνητα.","OCR failed. You can enter the details manually."));});});}
    private void viewDocument(DocumentStore.Document d){try{byte[] bytes=android.util.Base64.decode(d.attachment(),android.util.Base64.DEFAULT);var layout=workForm();var image=new ImageView(this);image.setAdjustViewBounds(true);layout.addView(image,new LinearLayout.LayoutParams(-1,dp(420)));var scroll=new ScrollView(this);scroll.addView(layout);var dialog=new AlertDialog.Builder(this).setTitle(d.metadata().optString("original_filename")).setView(scroll).setPositiveButton(t("Κλείσιμο"),null).create();
        if(DocumentStore.mime(d.metadata().optString("original_filename")).equals("application/pdf")){var file=java.io.File.createTempFile("preview-",".pdf",getCacheDir());try(var out=new java.io.FileOutputStream(file)){out.write(bytes);}var fd=android.os.ParcelFileDescriptor.open(file,android.os.ParcelFileDescriptor.MODE_READ_ONLY);var pdf=new android.graphics.pdf.PdfRenderer(fd);final int[] index={0};final android.graphics.Bitmap[] bitmap={null};var label=new TextView(this);layout.addView(label);Runnable render=()->{try(var page=pdf.openPage(index[0])){float scale=1400f/Math.max(page.getWidth(),page.getHeight());var next=android.graphics.Bitmap.createBitmap(Math.max(1,(int)(page.getWidth()*scale)),Math.max(1,(int)(page.getHeight()*scale)),android.graphics.Bitmap.Config.ARGB_8888);next.eraseColor(Color.WHITE);page.render(next,null,null,android.graphics.pdf.PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY);image.setImageBitmap(next);if(bitmap[0]!=null)bitmap[0].recycle();bitmap[0]=next;label.setText((index[0]+1)+" / "+pdf.getPageCount());}};var prev=new Button(this);prev.setText(words("Προηγούμενη σελίδα","Previous page"));layout.addView(prev);prev.setOnClickListener(v->{if(index[0]>0){index[0]--;render.run();}});var next=new Button(this);next.setText(words("Επόμενη σελίδα","Next page"));layout.addView(next);next.setOnClickListener(v->{if(index[0]+1<pdf.getPageCount()){index[0]++;render.run();}});dialog.setOnDismissListener(x->{pdf.close();try{fd.close();}catch(Exception ignored){}file.delete();if(bitmap[0]!=null)bitmap[0].recycle();});render.run();}
        else{var options=new android.graphics.BitmapFactory.Options();options.inJustDecodeBounds=true;android.graphics.BitmapFactory.decodeByteArray(bytes,0,bytes.length,options);options.inSampleSize=1;while(Math.max(options.outWidth,options.outHeight)/options.inSampleSize>1800)options.inSampleSize*=2;options.inJustDecodeBounds=false;var b=android.graphics.BitmapFactory.decodeByteArray(bytes,0,bytes.length,options);if(b==null)throw new java.io.IOException();image.setImageBitmap(b);dialog.setOnDismissListener(x->b.recycle());}dialog.show();}catch(Exception e){backupMessage(words("Η προεπισκόπηση δεν είναι διαθέσιμη. Αποθήκευσε το συνημμένο για εξωτερική προβολή.","Preview unavailable. Save the attachment to open externally."));}}
    private void showYearLocks(){text("Κλείδωμα Έτους",28,true);text(words("Αποτρέπει προσθήκη, αλλαγή και διαγραφή ετήσιων εγγραφών, μαζί με αυτόματες κινήσεις. Τα αγροτεμάχια και τα μητρώα παραμένουν επεξεργάσιμα. Η πλήρης επαναφορά αντιγράφου ασφαλείας αντικαθιστά και τα κλειδώματα.","Prevents adding, changing and deleting annual records, including automatic entries. Fields and master registries remain editable. Full backup restore also replaces year locks."),16,false);
        action(words("Διαχείριση έτους","Manage year"),()->{var form=workForm();var year=input(form,words("Έτος","Year"),String.valueOf(java.time.LocalDate.now().getYear()),InputType.TYPE_CLASS_NUMBER);var reason=input(form,words("Αιτιολογία","Reason"),"",InputType.TYPE_CLASS_TEXT);var mode=choice(form,words("Ενέργεια","Action"),java.util.List.of(words("Κλείδωμα","Lock"),words("Ξεκλείδωμα","Unlock")),0);saveForm(words("Κλείδωμα / Ξεκλείδωμα","Lock / Unlock"),form,()->YearLocks.set(store.getWritableDatabase(),year.getText().toString().trim(),mode.getSelectedItemPosition()==0,reason.getText().toString()));},true);
        try(var c=store.getReadableDatabase().rawQuery("SELECT id,is_locked,reason,locked_at,unlocked_at FROM year_locks ORDER BY id DESC",null)){while(c.moveToNext()){textValue(c.getString(0)+" · "+(c.getInt(1)==1?words("Κλειδωμένο","Locked"):words("Ανοιχτό","Open")),20,true);textValue(c.getString(2)+"\n"+words("Κλείδωμα: ","Locked: ")+c.getString(3)+"\n"+words("Ξεκλείδωμα: ","Unlocked: ")+c.getString(4),14,false);}}
    }
    private ReportStore.Filter reportFilter(){return new ReportStore.Filter(reportFrom,reportTo,reportField,reportProduct,reportBuyer);}
    private void showReports(){text(currentPage,28,true);boolean stock=currentPage.equals("Αναφορά Αποθήκης & Αξίας Stock");if(!stock)action(words("Φίλτρα αναφοράς","Report filters"),this::reportFilters,true);action(words("Εξαγωγή CSV","Export CSV"),()->exportFile(113,"mastixa-report.csv","text/csv"),false);action(words("Εξαγωγή PDF","Export PDF"),()->exportFile(114,"mastixa-report.pdf","application/pdf"),false);action(words("Εξαγωγή Excel","Export Excel"),()->exportFile(117,"mastixa-report.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),false);var rows=new ReportStore(store,profile.language().equals("en")).report(currentPage,reportFilter());for(var row:rows){textValue(row[0],17,true);textValue(row[1],16,false);}}
    private void reportFilters(){var form=workForm();var from=input(form,words("Από (YYYY-MM-DD, κενό = όλα)","From (YYYY-MM-DD, blank = all)"),reportFrom,InputType.TYPE_CLASS_TEXT);var to=input(form,words("Έως (YYYY-MM-DD, κενό = όλα)","To (YYYY-MM-DD, blank = all)"),reportTo,InputType.TYPE_CLASS_TEXT);var fi=new java.util.ArrayList<String>();var fn=new java.util.ArrayList<String>();fi.add("");fn.add(words("Όλα","All"));for(var f:store.fields()){fi.add(f.id());fn.add(f.name());}var field=choice(form,words("Αγροτεμάχιο","Field"),fn,Math.max(0,fi.indexOf(reportField)));var pi=new java.util.ArrayList<String>();var pn=new java.util.ArrayList<String>();pi.add("");pn.add(words("Όλα","All"));for(var p:catalog().products()){pi.add(p.id());pn.add(p.name());}var product=choice(form,words("Προϊόν (παραγωγή / πωλήσεις)","Product (production / sales)"),pn,Math.max(0,pi.indexOf(reportProduct)));var bi=new java.util.ArrayList<String>();var bn=new java.util.ArrayList<String>();bi.add("");bn.add(words("Όλοι","All"));for(var p:partners().partners()){bi.add(p.id());bn.add(p.name());}var buyer=choice(form,words("Αγοραστής (πωλήσεις)","Buyer (sales)"),bn,Math.max(0,bi.indexOf(reportBuyer)));saveForm(words("Φίλτρα αναφοράς","Report filters"),form,()->{var f=new ReportStore.Filter(from.getText().toString().trim(),to.getText().toString().trim(),fi.get(field.getSelectedItemPosition()),pi.get(product.getSelectedItemPosition()),bi.get(buyer.getSelectedItemPosition()));reportFrom=f.from();reportTo=f.to();reportField=f.field();reportProduct=f.product();reportBuyer=f.buyer();});}

    private String dashboardYear="",alertKind="",alertQuery="";
    private int alertSeverity=-1;
    private DashboardStore dashboard(){return new DashboardStore(store,profile.language().equals("en"));}
    private String severityLabel(int value){return switch(value){case 0->words("Άμεση","Urgent");case 1->words("Προσοχή","Attention");default->words("Ενημέρωση","Information");};}
    private String alertKindLabel(String kind){return switch(kind){case "activity"->words("Προγραμματισμένες εργασίες","Scheduled activities");case "inventory"->words("Απόθεμα","Stock");case "equipment"->words("Συντήρηση μηχανημάτων","Equipment service");case "harvest_wait"->words("Αναμονή φυτοπροστασίας","Plant protection waiting period");case "crop_task"->words("Εργασίες προγράμματος","Crop program tasks");default->words("Όλες","All");};}
    private void showDashboard(){
        var data=dashboard().snapshot(dashboardYear,java.time.LocalDate.now());text("Dashboard",28,true);textValue(profile.name(),20,true);text(words("Συνολική εικόνα εκμετάλλευσης","Farm overview"),16,false);
        action(words("Έτος: ","Year: ")+(dashboardYear.isEmpty()?words("Όλα","All"):dashboardYear),()->{var years=new java.util.ArrayList<String>();years.add("");years.addAll(dashboard().years());if(!years.contains(String.valueOf(java.time.LocalDate.now().getYear())))years.add(String.valueOf(java.time.LocalDate.now().getYear()));workFilter(words("Επιλογή έτους","Select year"),years,years.stream().map(y->y.isEmpty()?words("Όλα","All"):y).toList(),v->dashboardYear=v);},false);
        var grid=new LinearLayout(this);grid.setOrientation(LinearLayout.VERTICAL);content.addView(grid);
        dashboardMetric(grid,words("Έσοδα","Income"),euros(data.income()),()->openDashboardMoney("income"));dashboardMetric(grid,words("Έξοδα","Expenses"),euros(data.expenses()),()->openDashboardMoney("expense"));dashboardMetric(grid,words("Οικονομικό αποτέλεσμα","Financial result"),euros(data.income().subtract(data.expenses())),()->{navigate("Αναφορές");reportFrom=dashboardYear.isEmpty()?"":dashboardYear+"-01-01";reportTo=dashboardYear.isEmpty()?"":dashboardYear+"-12-31";reportField="";reportProduct="";reportBuyer="";showHome();});
        text(words("Καταχωρημένα ποσά. Οι συνδεδεμένες πωλήσεις και τα αυτόματα έξοδα μετρούν μία φορά.","Posted amounts. Linked sales and automatic expenses are counted once."),14,false);
        action(data.fields()+words(" αγροτεμάχια · "," fields · ")+quantity(data.area())+words(" στρέμματα · "," stremma · ")+data.trees()+words(" δέντρα"," trees"),()->navigate("Αγροτεμάχια"),false);
        text(words("Παραγωγή ανά προϊόν","Production by product"),22,true);if(data.products().isEmpty())text(words("Δεν υπάρχουν προϊόντα. Πρόσθεσε προϊόν για να καταχωρίσεις παραγωγή.","No products yet. Add a product to record production."),16,false);
        for(var p:data.products()){action(p.name()+" · "+quantity(p.produced())+" "+p.unit(),()->{navigate("Παραγωγή");productionQuery=p.name();productionYear=dashboardYear;showHome();},false);textValue(words("Διαθέσιμο όλων των ετών: ","Available across all years: ")+quantity(p.available())+" "+p.unit(),15,false);}
        long urgent=data.alerts().stream().filter(a->a.severity()==0).count();text(words("Εκκρεμότητες σήμερα","Current pending items"),22,true);action(data.alerts().size()+words(" ειδοποιήσεις · "," alerts · ")+urgent+words(" άμεσες"," urgent"),()->{navigate("Ειδοποιήσεις");alertKind="";alertSeverity=-1;alertQuery="";showHome();},true);
        for(var a:data.alerts().stream().limit(3).toList())alertButton(a);
        text(words("Ασφάλεια δεδομένων","Data backups"),22,true);long last=getSharedPreferences(profile.preferences(),MODE_PRIVATE).getLong("last_exported_backup_at",0);text(last==0?words("Δεν έχει καταγραφεί επιτυχής εξαγωγή backup από αυτή την έκδοση.","No successful backup export has been recorded by this version."):words("Τελευταία επιτυχής εξαγωγή: ","Last successful export: ")+java.time.Instant.ofEpochMilli(last).atZone(java.time.ZoneId.systemDefault()).format(java.time.format.DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm")),16,false);
        if(recoveryFile().exists())text(words("Υπάρχει εσωτερικό αντίγραφο πριν από εισαγωγή/επαναφορά.","An internal recovery copy from an import/restore is available."),15,false);
        text(words("Η ένδειξη εξαγωγής δεν επιβεβαιώνει ότι το εξωτερικό αρχείο εξακολουθεί να υπάρχει. Αυτόματο/online backup δεν έχει ενεργοποιηθεί.","Export history does not verify that the external file still exists. Automatic/online backup is not enabled."),14,false);
        action(words("Δημιουργία backup","Create backup"),()->exportFile(101,"mastixa-"+System.currentTimeMillis()+".json","application/json"),false);action(words("Επαναφορά και αντίγραφο ασφαλείας","Restore and recovery copy"),()->navigate("Τοπικό backup"),false);
        action(words("Ανανέωση","Refresh"),this::showHome,false);
    }
    private void dashboardMetric(LinearLayout parent,String label,String value,Runnable run){var box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(18),dp(12),dp(18),dp(12));box.setBackground(surface(Color.WHITE,14));var params=new LinearLayout.LayoutParams(-1,-2);params.topMargin=dp(12);parent.addView(box,params);var title=new TextView(this);title.setText(label);title.setTextColor(Color.rgb(55,80,65));title.setTextSize(16);box.addView(title);var number=new Button(this);number.setText(value);number.setContentDescription(label);number.setTextSize(27);number.setAllCaps(false);number.setTextColor(Color.rgb(30,62,49));number.setBackgroundColor(Color.TRANSPARENT);box.addView(number);number.setOnClickListener(v->run.run());}
    private void openDashboardMoney(String kind){navigate(kind.equals("income")?"Έσοδα":"Έξοδα");moneyYear=dashboardYear;moneyQuery="";showHome();}
    private java.util.List<DashboardStore.Alert> visibleAlerts(){return DashboardStore.filter(Phase13Alerts.alerts(store,profile.language().equals("en"),java.time.LocalDate.now()),alertKind,alertSeverity,alertQuery);}
    private void showAlerts(){var all=Phase13Alerts.alerts(store,profile.language().equals("en"),java.time.LocalDate.now());var visible=DashboardStore.filter(all,alertKind,alertSeverity,alertQuery);text(words("Ειδοποιήσεις & Εκκρεμότητες","Alerts & Pending Items"),28,true);text(words("Υπολογίζονται από τις καταχωρίσεις του ενεργού προφίλ κατά το άνοιγμα ή την ανανέωση. Δεν αποστέλλονται ειδοποιήσεις παρασκηνίου.","Calculated from the active profile when opened or refreshed. No background notifications are sent."),15,false);
        text(all.size()+words(" συνολικά · "," total · ")+all.stream().filter(a->a.severity()==0).count()+words(" άμεσες"," urgent"),20,true);
        action(words("Κατηγορία: ","Category: ")+alertKindLabel(alertKind),()->{var ids=java.util.List.of("","activity","crop_task","inventory","equipment","harvest_wait");workFilter(words("Κατηγορία","Category"),ids,ids.stream().map(this::alertKindLabel).toList(),v->alertKind=v);},false);
        action(words("Προτεραιότητα: ","Priority: ")+(alertSeverity<0?words("Όλες","All"):severityLabel(alertSeverity)),()->new AlertDialog.Builder(this).setTitle(words("Προτεραιότητα","Priority")).setItems(new String[]{words("Όλες","All"),severityLabel(0),severityLabel(1),severityLabel(2)},(d,n)->{alertSeverity=n-1;showHome();}).show(),false);
        action(words("Αναζήτηση: ","Search: ")+alertQuery,()->{var q=new EditText(this);q.setText(alertQuery);new AlertDialog.Builder(this).setTitle(words("Αναζήτηση ειδοποιήσεων","Find alerts")).setView(q).setNegativeButton(t("Ακύρωση"),null).setPositiveButton(t("Εντάξει"),(d,n)->{alertQuery=q.getText().toString();showHome();}).show();},false);
        action(words("Ανανέωση","Refresh"),this::showHome,false);text(visible.size()+words(" εμφανιζόμενες"," shown"),18,true);if(visible.isEmpty())text(all.isEmpty()?words("Δεν υπάρχουν τρέχουσες εκκρεμότητες από τα καταχωρημένα δεδομένα.","No current pending items in the recorded data."):words("Καμία ειδοποίηση δεν ταιριάζει στα φίλτρα.","No alerts match these filters."),16,false);
        for(var a:visible)alertButton(a);if(!visible.isEmpty())action(words("Εξαγωγή ειδοποιήσεων CSV","Export alerts CSV"),()->exportFile(118,"mastixa-alerts.csv","text/csv"),false);
        text(words("Η αναμονή φυτοπροστασίας βασίζεται μόνο στις ημέρες που έχουν καταχωριστεί. Έλεγξε την αρχική εγγραφή και την ετικέτα του σκευάσματος.","Plant protection waiting periods use the recorded number of days. Check the source record and the product label."),14,false);
    }
    private void alertButton(DashboardStore.Alert a){action(severityLabel(a.severity())+" · "+a.subject()+"\n"+a.message()+(a.date().isEmpty()?"":"\n"+a.date()),()->openAlert(a),false);}
    private void openAlert(DashboardStore.Alert a){try{switch(a.kind()){case "inventory"->openInventoryItem(a.recordId());case "activity"->{var row=new ActivityStore(store).activities().stream().filter(x->x.id().equals(a.recordId())).findFirst().orElseThrow();navigate("Άρδευση & Λίπανση");activityDetails(row);}case "equipment"->{var row=work().equipment().stream().filter(x->x.id().equals(a.recordId())).findFirst().orElseThrow();navigate("Μηχανήματα & Συντήρηση");equipmentDetails(row);}case "crop_task"->startActivity(new android.content.Intent(this,UnifiedCalendarActivity.class).putExtra("focus_task",a.recordId()));case "harvest_wait"->{var row=work().protections().stream().filter(x->x.id().equals(a.recordId())).findFirst().orElseThrow();navigate("Φυτοπροστασία");protectionDetails(row);}}}catch(java.util.NoSuchElementException e){backupMessage(words("Η εγγραφή δεν είναι πλέον διαθέσιμη. Ανανέωσε τις ειδοποιήσεις.","The record is no longer available. Refresh alerts."));}}

}
