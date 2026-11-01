package net.java.cargotracker.interfaces.booking.web;
import jakarta.servlet.annotation.WebServlet;import jakarta.servlet.http.*;import java.io.IOException;
import java.util.*;
@WebServlet(urlPatterns={"/public/track.xhtml","/admin/map.xhtml","/admin/mapFrame.html","/admin/selectItinerary.xhtml","/eventLogger/eventLogger.xhtml","/eventLogger/root.xhtml","/booking/booking.xhtml","/booking/booking-date.xhtml","/booking/booking-destination.xhtml"})
public class LegacyNavigationServlet extends HttpServlet {
    private static final Map<String,String> TARGETS=Map.of(
        "/public/track.xhtml","/admin/track.xhtml",
        "/admin/map.xhtml","/admin/live.xhtml",
        "/admin/mapFrame.html","/admin/live.xhtml",
        "/admin/selectItinerary.xhtml","/admin/route.xhtml",
        "/eventLogger/eventLogger.xhtml","/mobile.xhtml",
        "/eventLogger/root.xhtml","/mobile.xhtml",
        "/booking/booking.xhtml","/admin/book.xhtml",
        "/booking/booking-date.xhtml","/admin/book.xhtml",
        "/booking/booking-destination.xhtml","/admin/book.xhtml");
    @Override protected void doGet(HttpServletRequest req,HttpServletResponse res)throws IOException{
        String target=TARGETS.get(req.getServletPath());
        if(target==null){res.sendError(404);return;}
        if(req.getServletPath().equals("/admin/selectItinerary.xhtml") || req.getServletPath().equals("/public/track.xhtml")){
            String id=req.getParameter("trackingId");
            if(id!=null){
                if(req.getParameterValues("trackingId").length!=1 || !id.matches("[A-Z0-9]{6,8}")){res.sendError(404);return;}
                target+="?trackingId="+id;
            }else if(req.getServletPath().equals("/admin/selectItinerary.xhtml")){res.sendError(404);return;}
        }
        res.setHeader("Cache-Control","no-store");res.setStatus(303);res.setHeader("Location",req.getContextPath()+target);
    }
}
