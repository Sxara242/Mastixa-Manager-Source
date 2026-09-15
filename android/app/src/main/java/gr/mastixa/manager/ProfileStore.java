package gr.mastixa.manager;

import android.content.*;
import android.database.sqlite.*;
import android.util.Base64;
import java.security.*;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import java.util.*;

/** Local credentials and profile registry, kept outside farm backups. */
public final class ProfileStore extends SQLiteOpenHelper {
    private static final int ROUNDS=210_000;
    public record Profile(String id,String name,String username,String language) {
        @Override public String toString() { return name; }
        public String database() { return id.equals("legacy") ? "mastixa.db" : "farm-"+id+".db"; }
        public String preferences() { return id.equals("legacy") ? "navigation" : "navigation-"+id; }
        public String recovery() { return id.equals("legacy") ? "before-restore.json" : "before-restore-"+id+".json"; }
    }
    public ProfileStore(Context context) { this(context,"profiles.db"); }
    public ProfileStore(Context context,String database) { super(context,database,null,1); }
    @Override public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE profiles(id TEXT PRIMARY KEY,name TEXT NOT NULL COLLATE NOCASE UNIQUE,username TEXT NOT NULL COLLATE NOCASE UNIQUE,language TEXT NOT NULL,salt TEXT NOT NULL,hash TEXT NOT NULL,failures INTEGER NOT NULL DEFAULT 0,locked_until INTEGER NOT NULL DEFAULT 0)");
    }
    @Override public void onUpgrade(SQLiteDatabase db,int oldVersion,int newVersion) {}
    public List<Profile> profiles() {
        var result=new ArrayList<Profile>();
        try(var c=getReadableDatabase().rawQuery("SELECT id,name,username,language FROM profiles ORDER BY rowid",null)) {
            while(c.moveToNext()) result.add(new Profile(c.getString(0),c.getString(1),c.getString(2),c.getString(3)));
        }
        return result;
    }
    private static byte[] derive(char[] password,byte[] salt) throws Exception {
        var spec=new PBEKeySpec(password,salt,ROUNDS,256);
        try { return SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).getEncoded(); }
        finally { spec.clearPassword(); }
    }
    private static void validatePassword(char[] password) {
        if(password.length<8 || password.length>128) throw new IllegalArgumentException("Ο κωδικός πρέπει να έχει 8–128 χαρακτήρες.");
    }
    public Profile create(String name,String username,char[] password,String language) throws Exception {
        name=name.trim(); username=username.trim();
        if(name.isEmpty() || name.length()>60 || !username.matches("[A-Za-z0-9._-]{3,40}")) throw new IllegalArgumentException("Συμπλήρωσε όνομα προφίλ και username με 3–40 λατινικούς χαρακτήρες, αριθμούς ή . _ -");
        validatePassword(password); checkLanguage(language);
        byte[] salt=new byte[16]; new SecureRandom().nextBytes(salt); byte[] hash=derive(password,salt);
        var db=getWritableDatabase(); db.beginTransaction();
        try {
            // The first local owner claims the existing installation without moving its data.
            String id=profiles().isEmpty() ? "legacy" : UUID.randomUUID().toString();
            ContentValues row=new ContentValues(); row.put("id",id); row.put("name",name); row.put("username",username); row.put("language",language);
            row.put("salt",Base64.encodeToString(salt,Base64.NO_WRAP)); row.put("hash",Base64.encodeToString(hash,Base64.NO_WRAP));
            db.insertOrThrow("profiles",null,row); db.setTransactionSuccessful();
            return new Profile(id,name,username,language);
        } finally { db.endTransaction(); Arrays.fill(hash,(byte)0); }
    }
    public Profile authenticate(String id,String username,char[] password,String language) throws Exception {
        checkLanguage(language);
        var db=getWritableDatabase(); db.beginTransaction();
        try(var c=db.rawQuery("SELECT name,username,salt,hash,failures,locked_until FROM profiles WHERE id=?",new String[]{id})) {
            if(!c.moveToFirst()) return null;
            long now=System.currentTimeMillis();
            if(c.getLong(5)>now) throw new IllegalArgumentException("Πολλές προσπάθειες. Περίμενε ένα λεπτό και δοκίμασε ξανά.");
            byte[] calculated=derive(password,Base64.decode(c.getString(2),Base64.NO_WRAP));
            boolean valid=MessageDigest.isEqual(calculated,Base64.decode(c.getString(3),Base64.NO_WRAP)) && c.getString(1).equalsIgnoreCase(username.trim());
            Arrays.fill(calculated,(byte)0); ContentValues row=new ContentValues();
            int failures=valid ? 0 : c.getInt(4)+1;
            row.put("failures",failures>=5 ? 0 : failures); row.put("locked_until",failures>=5 ? now+60_000 : 0L);
            if(valid) row.put("language",language);
            db.update("profiles",row,"id=?",new String[]{id}); db.setTransactionSuccessful();
            return valid ? new Profile(id,c.getString(0),c.getString(1),language) : null;
        } finally { db.endTransaction(); }
    }
    public void changePassword(Profile profile,char[] oldPassword,char[] newPassword) throws Exception {
        validatePassword(newPassword);
        if(authenticate(profile.id(),profile.username(),oldPassword,profile.language())==null) throw new IllegalArgumentException("Λάθος όνομα χρήστη ή κωδικός.");
        byte[] salt=new byte[16]; new SecureRandom().nextBytes(salt); byte[] hash=derive(newPassword,salt);
        try {
            ContentValues row=new ContentValues(); row.put("salt",Base64.encodeToString(salt,Base64.NO_WRAP)); row.put("hash",Base64.encodeToString(hash,Base64.NO_WRAP));
            getWritableDatabase().update("profiles",row,"id=?",new String[]{profile.id()});
        } finally { Arrays.fill(hash,(byte)0); }
    }
    private static void checkLanguage(String language) { if(!Set.of("el","en").contains(language)) throw new IllegalArgumentException("Invalid language"); }
}
