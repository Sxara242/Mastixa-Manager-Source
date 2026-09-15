package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.concurrent.*;
import static org.junit.Assert.*;

/** Failure injection uses only synthetic profiles and the isolated checks application. */
public class ExportFailureUiTest {
    private java.util.List<android.view.View> views(android.view.View v){var result=new java.util.ArrayList<android.view.View>();result.add(v);if(v instanceof android.view.ViewGroup g)for(int n=0;n<g.getChildCount();n++)result.addAll(views(g.getChildAt(n)));return result;}
    private boolean hasTextContaining(String value){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof android.widget.TextView text&&text.getText().toString().contains(value))return true;return false;}

    @Test public void unavailableDocumentPickerDoesNotCrashOrRetainPreparedFile()throws Exception{
        var i=InstrumentationRegistry.getInstrumentation();var c=i.getTargetContext();var profile=new ProfileStore.Profile("export-picker-test","Picker failure","test","en");String id=seed(profile);byte[] before=snapshot(profile);var screen=start(profile,id);File temp=new File(c.getCacheDir(),"coordinates-00000000-0000-0000-0000-000000000024.tmp");
        var calls=new java.util.concurrent.atomic.AtomicInteger();
        var monitor=new android.app.Instrumentation.ActivityMonitor(){@Override public android.app.Instrumentation.ActivityResult onStartActivity(Intent intent){if(Intent.ACTION_CREATE_DOCUMENT.equals(intent.getAction())){calls.incrementAndGet();throw new android.content.ActivityNotFoundException("Injected missing picker");}return null;}};
        i.addMonitor(monitor);
        try{
            Files.write(temp.toPath(),"synthetic export".getBytes(StandardCharsets.UTF_8));i.runOnMainSync(()->{set(screen,"pending",temp);invoke(screen,"openDocumentPicker",new Class[]{Intent.class},new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("text/csv"));});i.waitForIdleSync();
            assertEquals(1,calls.get());assertNull(field(screen,"pending"));assertFalse(temp.exists());assertFalse(screen.isFinishing());assertArrayEquals(before,snapshot(profile));
            assertTrue(hasTextContaining("Document picker unavailable. Export again."));assertFalse(hasTextContaining("Injected missing picker"));
        }finally{i.removeMonitor(monitor);i.runOnMainSync(()->{screen.finish();UserSession.clear();});temp.delete();}
    }

    @Test public void greekUnavailableDocumentPickerIsLocalizedWithoutRawException()throws Exception{
        var i=InstrumentationRegistry.getInstrumentation();var c=i.getTargetContext();var profile=new ProfileStore.Profile("export-picker-el-test","Αποτυχία επιλογέα","test","el");String id=seed(profile);var screen=start(profile,id);File temp=new File(c.getCacheDir(),"coordinates-00000000-0000-0000-0000-000000000025.tmp");
        var monitor=new android.app.Instrumentation.ActivityMonitor(){@Override public android.app.Instrumentation.ActivityResult onStartActivity(Intent intent){if(Intent.ACTION_CREATE_DOCUMENT.equals(intent.getAction()))throw new android.content.ActivityNotFoundException("RAW_PICKER_SENTINEL");return null;}};
        i.addMonitor(monitor);
        try{
            Files.write(temp.toPath(),"synthetic export".getBytes(StandardCharsets.UTF_8));i.runOnMainSync(()->{set(screen,"pending",temp);invoke(screen,"openDocumentPicker",new Class[]{Intent.class},new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("text/csv"));});i.waitForIdleSync();
            assertTrue(hasTextContaining("Ο επιλογέας αρχείου δεν είναι διαθέσιμος. Επανέλαβε την εξαγωγή."));assertFalse(hasTextContaining("RAW_PICKER_SENTINEL"));assertNull(field(screen,"pending"));assertFalse(temp.exists());
        }finally{i.removeMonitor(monitor);i.runOnMainSync(()->{screen.finish();UserSession.clear();});temp.delete();}
    }

    private Object field(Object target,String name){try{var f=target.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(target);}catch(Exception e){throw new RuntimeException(e);}}
    private void set(Object target,String name,Object value){try{var f=target.getClass().getDeclaredField(name);f.setAccessible(true);f.set(target,value);}catch(Exception e){throw new RuntimeException(e);}}
    private void invoke(Object target,String name,Class<?>[] types,Object... values){try{var m=target.getClass().getDeclaredMethod(name,types);m.setAccessible(true);m.invoke(target,values);}catch(Exception e){throw new RuntimeException(e);}}
    private String seed(ProfileStore.Profile profile){var c=InstrumentationRegistry.getInstrumentation().getTargetContext();assertTrue(c.getPackageName().endsWith(".checks"));c.deleteDatabase(profile.database());try(var farm=new FarmStore(c,profile.database())){farm.addField("Export failure fixture",1);String id=farm.fields().get(0).id();new GeoStore(farm).saveGeometry(id,ParcelGeometry.manual("26 38\n26.001 38\n26.001 38.001\n26 38.001","EPSG:4326"),"fixture","",0);return id;}}
    private Activity start(ProfileStore.Profile profile,String id)throws Exception{var i=InstrumentationRegistry.getInstrumentation();i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});var screen=i.startActivitySync(new Intent(i.getTargetContext(),CoordinateExportActivity.class).putExtra("field_id",id).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));i.waitForIdleSync();((ExecutorService)field(screen,"worker")).submit(()->{}).get(5,TimeUnit.SECONDS);i.waitForIdleSync();return screen;}
    private byte[] snapshot(ProfileStore.Profile profile)throws Exception{try(var farm=new FarmStore(InstrumentationRegistry.getInstrumentation().getTargetContext(),profile.database())){return LocalBackup.snapshot(farm);}}

    @Test public void profileChangeCannotRestoreAnotherProfilesPreparedExport()throws Exception{
        var i=InstrumentationRegistry.getInstrumentation();var c=i.getTargetContext();var a=new ProfileStore.Profile("export-owner-a-test","A","test","en");var b=new ProfileStore.Profile("export-owner-b-test","B","test","en");String id=seed(a);seed(b);byte[] beforeA=snapshot(a),beforeB=snapshot(b);Activity screen=start(a,id);File temp=new File(c.getCacheDir(),"coordinates-00000000-0000-0000-0000-000000000021.tmp");
        try{
            Files.write(temp.toPath(),"private profile A export".getBytes(StandardCharsets.UTF_8));var old=screen;i.runOnMainSync(()->set(old,"pending",temp));
            var monitor=i.addMonitor(CoordinateExportActivity.class.getName(),null,false);
            try{i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(b);old.recreate();});screen=i.waitForMonitorWithTimeout(monitor,5000);}finally{i.removeMonitor(monitor);}
            assertNotNull(screen);i.waitForIdleSync();var replacement=screen;
            i.runOnMainSync(()->assertNull("Profile B must not inherit profile A's export",field(replacement,"pending")));
            assertFalse("Abandoned private staging file must be cleaned",temp.exists());assertArrayEquals(beforeA,snapshot(a));assertArrayEquals(beforeB,snapshot(b));
        }finally{var last=screen;i.runOnMainSync(()->{if(last!=null)last.finish();UserSession.clear();});temp.delete();}
    }

    private void queuedSave(boolean finish)throws Exception{
        var i=InstrumentationRegistry.getInstrumentation();var c=i.getTargetContext();var profile=new ProfileStore.Profile("export-queued-test","Queued export","test","en");String id=seed(profile);byte[] before=snapshot(profile);var screen=start(profile,id);
        File temp=new File(c.getCacheDir(),"coordinates-00000000-0000-0000-0000-000000000022.tmp"),destination=new File(c.getCacheDir(),"qa-queued-export.csv");byte[] bytes="complete synthetic export".getBytes(StandardCharsets.UTF_8);CountDownLatch release=new CountDownLatch(1),entered=new CountDownLatch(1);
        var worker=(ExecutorService)field(screen,"worker");
        try{
            worker.submit(()->{}).get(5,TimeUnit.SECONDS);i.waitForIdleSync();Files.write(temp.toPath(),bytes);Files.write(destination.toPath(),"old destination".getBytes(StandardCharsets.UTF_8));
            worker.submit(()->{entered.countDown();try{if(!release.await(10,TimeUnit.SECONDS))throw new AssertionError("Test gate timed out");}catch(InterruptedException e){Thread.currentThread().interrupt();}});assertTrue(entered.await(5,TimeUnit.SECONDS));
            i.runOnMainSync(()->{set(screen,"pending",temp);invoke(screen,"onActivityResult",new Class[]{int.class,int.class,Intent.class},203,Activity.RESULT_OK,new Intent().setData(Uri.fromFile(destination)));if(finish)screen.finish();else invoke(screen,"refresh",new Class[]{});});i.waitForIdleSync();if(finish){long deadline=android.os.SystemClock.uptimeMillis()+3000;while(!screen.isDestroyed()&&android.os.SystemClock.uptimeMillis()<deadline)android.os.SystemClock.sleep(20);assertTrue("Activity must actually be destroyed before releasing the queued save",screen.isDestroyed());}release.countDown();
            if(finish)assertTrue(worker.awaitTermination(5,TimeUnit.SECONDS));else worker.submit(()->{}).get(5,TimeUnit.SECONDS);
            i.waitForIdleSync();assertArrayEquals("Accepted save must finish despite preview change or Activity finish",bytes,Files.readAllBytes(destination.toPath()));assertFalse(temp.exists());assertArrayEquals(before,snapshot(profile));
        }finally{release.countDown();i.runOnMainSync(()->{screen.finish();UserSession.clear();});temp.delete();destination.delete();}
    }
    @Test public void selectionChangeDoesNotCancelAcceptedSave()throws Exception{queuedSave(false);}
    @Test public void activityFinishDoesNotDiscardAcceptedSave()throws Exception{queuedSave(true);}

    @Test public void unavailableDestinationCleansStagingAndPreservesData()throws Exception{
        var i=InstrumentationRegistry.getInstrumentation();var c=i.getTargetContext();var profile=new ProfileStore.Profile("export-destination-test","Destination failure","test","en");String id=seed(profile);byte[] before=snapshot(profile);var screen=start(profile,id);File temp=new File(c.getCacheDir(),"coordinates-00000000-0000-0000-0000-000000000023.tmp");
        try{
            Files.write(temp.toPath(),"synthetic export".getBytes(StandardCharsets.UTF_8));i.runOnMainSync(()->{set(screen,"pending",temp);invoke(screen,"onActivityResult",new Class[]{int.class,int.class,Intent.class},203,Activity.RESULT_OK,new Intent().setData(Uri.parse("content://gr.mastixa.qa.missing/document")));});
            ((ExecutorService)field(screen,"worker")).submit(()->{}).get(5,TimeUnit.SECONDS);i.waitForIdleSync();assertFalse(temp.exists());assertFalse(screen.isFinishing());assertArrayEquals(before,snapshot(profile));
            assertTrue(hasTextContaining("Save failed. The destination file may be incomplete. Try a different destination."));assertFalse(hasTextContaining("gr.mastixa.qa.missing"));
        }finally{i.runOnMainSync(()->{screen.finish();UserSession.clear();});temp.delete();}
    }
}
