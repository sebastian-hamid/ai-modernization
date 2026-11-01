package net.java.cargotracker.interfaces.handling.mobile;
import jakarta.inject.*;import jakarta.faces.view.ViewScoped;import jakarta.faces.context.FacesContext;import jakarta.faces.application.FacesMessage;import jakarta.servlet.http.HttpServletRequest;
import java.io.Serializable;import java.util.*;import java.time.*;import java.time.format.*;
import net.java.cargotracker.interfaces.booking.facade.BookingServiceFacade;
import net.java.cargotracker.interfaces.booking.facade.dto.CargoRoute;
import net.java.cargotracker.interfaces.handling.rest.*;
import net.java.cargotracker.domain.model.handling.HandlingEvent;
import lab.modernization.security.SessionTokens;
@Named @ViewScoped
public class HandlingPages implements Serializable {
    @Inject BookingServiceFacade facade;@Inject HandlingReportService service;@Inject HttpServletRequest request;
    private String trackingId,eventType,location,completionTime,voyage;
    public List<CargoRoute> getCargos(){return facade.listAllCargos().stream().filter(c->c.isRouted()&&!c.isClaimed()).toList();}
    public List<net.java.cargotracker.interfaces.booking.facade.dto.Location> getLocations(){return facade.listShippingLocations();}
    public List<String> getVoyages(){return facade.listVoyageNumbers();}
    public List<String> getTypes(){return Arrays.stream(HandlingEvent.Type.values()).map(Enum::name).toList();}
    public String getCsrf(){return SessionTokens.get(request.getSession());}
    public String getTrackingId(){return trackingId;}public void setTrackingId(String v){trackingId=v;}
    public String getEventType(){return eventType;}public void setEventType(String v){eventType=v;}
    public String getLocation(){return location;}public void setLocation(String v){location=v;}
    public String getCompletionTime(){return completionTime;}public void setCompletionTime(String v){completionTime=v;}
    public String getVoyage(){return voyage;}public void setVoyage(String v){voyage=v;}
    private void error(String text){FacesContext.getCurrentInstance().addMessage(null,new FacesMessage(FacesMessage.SEVERITY_ERROR,text,null));}
    public void submit(){
        if(getCargos().stream().noneMatch(c->c.getTrackingId().equals(trackingId))){error("Choose a currently routed, unclaimed cargo.");return;}
        if(!getTypes().contains(eventType)||getLocations().stream().noneMatch(l->l.getUnLocode().equals(location))){error("Choose a valid event and location.");return;}
        try{LocalDateTime.parse(completionTime,DateTimeFormatter.ofPattern("uuuu-MM-dd HH:mm").withResolverStyle(ResolverStyle.STRICT));}
        catch(RuntimeException invalid){error("Enter a valid completion time in YYYY-MM-DD HH:mm format.");return;}
        boolean needsVoyage=eventType.equals("LOAD")||eventType.equals("UNLOAD");
        if(needsVoyage&&!getVoyages().contains(voyage)){error("Choose a voyage for LOAD or UNLOAD.");return;}
        HandlingReport report=new HandlingReport();report.setTrackingId(trackingId);report.setEventType(eventType);report.setUnLocode(location);report.setCompletionTime(completionTime);report.setVoyageNumber(needsVoyage?voyage:null);
        service.submitReport(report);
        FacesContext.getCurrentInstance().addMessage(null,new FacesMessage("Accepted for processing. Check cargo details for the result."));
    }
}
