package gr.mastixa.manager;

import android.database.sqlite.SQLiteDatabase;
import android.content.ContentValues;
import java.util.*;

/** Enforced inside SQLite, including automatic financial and stock changes. */
public final class YearLocks {
    static final String[] COLUMNS={"id","is_locked","reason","locked_at","unlocked_at","revision","updated_at"};
    static final String[][] DATED={{"money_entries","entry_date"},{"production","entry_date"},{"production_sales","sale_date"},{"inventory_movements","movement_date"},{"farm_activities","activity_date"},{"plant_protection_records","application_date"},{"labor_entries","work_date"},{"planting_batches","planting_date"},{"equipment_maintenance","service_date"},{"invoice_documents","invoice_date"}};
    static void create(SQLiteDatabase db){
        db.execSQL("CREATE TABLE IF NOT EXISTS year_locks(id TEXT PRIMARY KEY,is_locked INTEGER NOT NULL CHECK(is_locked IN (0,1)),reason TEXT NOT NULL,locked_at TEXT NOT NULL,unlocked_at TEXT NOT NULL,revision INTEGER NOT NULL,updated_at INTEGER NOT NULL)");
        for(var pair:DATED) for(String event:new String[]{"INSERT","UPDATE","DELETE"}){
            String check=event.equals("INSERT")?condition("NEW",pair[1]):event.equals("DELETE")?condition("OLD",pair[1]):"("+condition("OLD",pair[1])+" OR "+condition("NEW",pair[1])+")";
            db.execSQL("CREATE TRIGGER IF NOT EXISTS year_guard_"+pair[0]+"_"+event+" BEFORE "+event+" ON "+pair[0]+" WHEN "+check+" BEGIN SELECT RAISE(ABORT,'Το έτος είναι κλειδωμένο / Year is locked'); END");
        }
    }
    private static String condition(String row,String date){return "EXISTS(SELECT 1 FROM year_locks WHERE id=substr("+row+"."+date+",1,4) AND is_locked=1)";}
    public static boolean locked(SQLiteDatabase db,String year){try(var c=db.rawQuery("SELECT is_locked FROM year_locks WHERE id=?",new String[]{year})){return c.moveToFirst()&&c.getInt(0)==1;}}
    public static void set(SQLiteDatabase db,String year,boolean locked,String reason){
        if(!year.matches("[1-9][0-9]{3}"))throw new IllegalArgumentException("Έτος: τέσσερα ψηφία / Year: four digits");
        db.beginTransaction();try{
            int rev=0;String at="",unlocked="";
            try(var c=db.rawQuery("SELECT revision,locked_at,unlocked_at FROM year_locks WHERE id=?",new String[]{year})){if(c.moveToFirst()){rev=c.getInt(0);at=c.getString(1);unlocked=c.getString(2);}}
            var v=new ContentValues();v.put("id",year);v.put("is_locked",locked?1:0);v.put("reason",reason.trim());v.put("locked_at",locked?java.time.Instant.now().toString():at);v.put("unlocked_at",locked?unlocked:java.time.Instant.now().toString());v.put("revision",rev+1);v.put("updated_at",System.currentTimeMillis());
            if(rev==0)db.insertOrThrow("year_locks",null,v);else db.update("year_locks",v,"id=?",new String[]{year});
            DocumentStore.queue(db,"year_locks",year,rev==0?"create":"update",rev+1);db.setTransactionSuccessful();
        }finally{db.endTransaction();}
    }
}
