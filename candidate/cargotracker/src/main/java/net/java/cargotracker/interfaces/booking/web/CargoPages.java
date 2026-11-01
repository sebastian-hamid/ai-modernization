package net.java.cargotracker.interfaces.booking.web;
import jakarta.inject.*;import jakarta.faces.view.ViewScoped;import jakarta.faces.context.FacesContext;import jakarta.faces.application.FacesMessage;
import jakarta.servlet.http.HttpServletRequest;
import java.io.*;import java.time.*;import java.util.*;
import lab.modernization.security.*;
import net.java.cargotracker.interfaces.booking.facade.BookingServiceFacade;
import net.java.cargotracker.interfaces.booking.facade.dto.*;
@Named @ViewScoped
public class CargoPages implements Serializable {
    @Inject BookingServiceFacade facade;
    @Inject HttpServletRequest request;
    private String trackingId,origin,destination,deadline;
    private CargoRoute cargo;
    public List<CargoRoute> getCargos(){return facade.listAllCargos();}
    public List<Location> getLocations(){return facade.listShippingLocations();}
    public boolean isOperator(){return request.isUserInRole("Operator") || request.isUserInRole("Administrator");}
    public String getCsrf(){return SessionTokens.get(request.getSession());}
    public String getTrackingId(){return trackingId;}
    public void setTrackingId(String value){trackingId=value;}
    public String getOrigin(){return origin;}
    public void setOrigin(String value){origin=value;}
    public String getDestination(){return destination;}
    public void setDestination(String value){destination=value;}
    public String getDeadline(){return deadline;}
    public void setDeadline(String value){deadline=value;}
    public CargoRoute getCargo(){return cargo;}
    public void load() throws IOException {
        if(trackingId==null || !trackingId.matches("[A-Z0-9]{6,8}")){notFound();return;}
        try {cargo=facade.loadCargoForRouting(trackingId);}
        catch(net.java.cargotracker.interfaces.booking.facade.CargoNotFoundException missing){notFound();return;}
        destination=cargo.getFinalDestinationCode();
    }
    private void notFound()throws IOException {
        FacesContext context=FacesContext.getCurrentInstance();
        context.getExternalContext().responseSendError(404,"Cargo not found");
        context.responseComplete();
    }
    private void message(String text){FacesContext.getCurrentInstance().addMessage(null,new FacesMessage(FacesMessage.SEVERITY_ERROR,text,null));}
    private boolean known(String code){return code!=null && getLocations().stream().anyMatch(location->location.getUnLocode().equals(code));}
    public String book(){
        if(!known(origin) || !known(destination) || origin.equals(destination)){message("Choose different valid origin and destination locations.");return null;}
        LocalDate date;
        try {date=LocalDate.parse(deadline);}
        catch(RuntimeException invalid){message("Enter a valid arrival deadline in YYYY-MM-DD format.");return null;}
        String id=facade.bookNewCargo(origin,destination,Date.from(date.atStartOfDay(ZoneOffset.UTC).toInstant()));
        return "/admin/show.xhtml?faces-redirect=true&trackingId="+id;
    }
    public String changeDestination(){
        if(cargo==null || !known(destination) || destination.equals(cargo.getOriginCode())){message("Choose a valid destination different from the origin.");return null;}
        facade.changeDestination(cargo.getTrackingId(),destination);
        return "/admin/show.xhtml?faces-redirect=true&trackingId="+cargo.getTrackingId();
    }
}
