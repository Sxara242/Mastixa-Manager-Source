package gr.mastixa.manager;

import android.content.Context;
import android.graphics.*;
import android.graphics.pdf.PdfRenderer;
import android.os.ParcelFileDescriptor;
import com.googlecode.tesseract.android.TessBaseAPI;
import org.json.JSONObject;
import java.io.*;
import java.util.regex.*;

/** No network permission or service: bundled Greek/English LSTM models. */
public final class OfflineOcr {
    public static synchronized String recognize(Context context,byte[] bytes,String name)throws Exception{
        File root=new File(context.getFilesDir(),"ocr-models"),data=new File(root,"tessdata");data.mkdirs();
        for(String lang:new String[]{"ell","eng"}){File file=new File(data,lang+".traineddata");if(!file.isFile()){File temp=new File(data,lang+".tmp");try(var in=context.getAssets().open("tessdata/"+lang+".traineddata");var out=new FileOutputStream(temp)){byte[] buffer=new byte[8192];int count;while((count=in.read(buffer))!=-1)out.write(buffer,0,count);}if(!temp.renameTo(file))throw new IOException("OCR model installation failed");}}
        TessBaseAPI tess=new TessBaseAPI();try{
            if(!tess.init(root.getAbsolutePath(),"ell+eng",TessBaseAPI.OEM_LSTM_ONLY))throw new IOException("OCR initialization failed");
            if(name.toLowerCase(java.util.Locale.ROOT).endsWith(".pdf")){
                File temp=File.createTempFile("ocr-",".pdf",context.getCacheDir());try{try(var out=new FileOutputStream(temp)){out.write(bytes);}try(var fd=ParcelFileDescriptor.open(temp,ParcelFileDescriptor.MODE_READ_ONLY);var pdf=new PdfRenderer(fd)){
                    if(pdf.getPageCount()>20)throw new IOException("OCR: έως 20 σελίδες / up to 20 pages");StringBuilder result=new StringBuilder();
                    for(int n=0;n<pdf.getPageCount();n++)try(var page=pdf.openPage(n)){float scale=Math.min(3f,2400f/Math.max(page.getWidth(),page.getHeight()));Bitmap b=Bitmap.createBitmap(Math.max(1,(int)(page.getWidth()*scale)),Math.max(1,(int)(page.getHeight()*scale)),Bitmap.Config.ARGB_8888);try{b.eraseColor(Color.WHITE);page.render(b,null,null,PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY);tess.setImage(b);result.append(tess.getUTF8Text()).append('\n');}finally{b.recycle();}}return result.toString();}
                }finally{temp.delete();}
            }
            var options=new BitmapFactory.Options();options.inJustDecodeBounds=true;BitmapFactory.decodeByteArray(bytes,0,bytes.length,options);if(options.outWidth<=0)throw new IOException("Η εικόνα δεν υποστηρίζεται για OCR / Image cannot be decoded for OCR");options.inSampleSize=1;while(Math.max(options.outWidth,options.outHeight)/options.inSampleSize>2600)options.inSampleSize*=2;options.inJustDecodeBounds=false;options.inPreferredConfig=Bitmap.Config.ARGB_8888;Bitmap bitmap=BitmapFactory.decodeByteArray(bytes,0,bytes.length,options);try{tess.setImage(bitmap);return tess.getUTF8Text();}finally{if(bitmap!=null)bitmap.recycle();}
        }finally{tess.recycle();}
    }
    public static JSONObject suggestions(String text)throws Exception{
        var result=new JSONObject().put("ocr_text",text).put("ocr_source","Tesseract ell+eng offline").put("ocr_status",text.isBlank()?"no_text":"review_required");
        var date=Pattern.compile("\\b(\\d{1,2})[./-](\\d{1,2})[./-](20\\d{2})\\b").matcher(text);while(date.find())try{result.put("ocr_suggested_date",java.time.LocalDate.of(Integer.parseInt(date.group(3)),Integer.parseInt(date.group(2)),Integer.parseInt(date.group(1))).toString());break;}catch(java.time.DateTimeException ignored){}
        var total=Pattern.compile("(?:ΓΕΝΙΚΟ\\s+ΣΥΝΟΛΟ|ΠΛΗΡΩΤΕΟ|ΣΥΝΟΛΟ|TOTAL|AMOUNT\\s+DUE)[^\\d\\r\\n]{0,20}([\\d][\\d., ]*)",Pattern.CASE_INSENSITIVE|Pattern.UNICODE_CASE).matcher(text);while(total.find())try{result.put("ocr_suggested_amount",String.format(java.util.Locale.ROOT,"%.2f",DocumentStore.amount(total.group(1))));}catch(IllegalArgumentException ignored){}
        var supplier=Pattern.compile("(?:ΠΡΟΜΗΘΕΥΤΗΣ|ΕΚΔΟΤΗΣ|SUPPLIER|VENDOR)\\s*[:：]\\s*([^\\r\\n]+)",Pattern.CASE_INSENSITIVE|Pattern.UNICODE_CASE).matcher(text);if(supplier.find())result.put("ocr_suggested_supplier",supplier.group(1).trim());return result;
    }
}
