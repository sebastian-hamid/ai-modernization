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
    private List<RouteCandidate> routes=Collections.emptyList();
    private int selectedRoute=-1;
    public List<CargoRoute> getCargos(){return facade.listAllCargos();}
    public List<Location> getLocations(){return facade.listShippingLocations();}
    public boolean isOperator(){return request.isUserInRole("Operator") || request.isUserInRole("Administrator");}
    public boolean isAdministrator(){return request.isUserInRole("Administrator");}
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
    public String lookupOnGet()throws IOException{
        if(trackingId==null)return null;
        load();return cargo==null?null:"/admin/show.xhtml?faces-redirect=true&trackingId="+cargo.getTrackingId();
    }
    public String lookup(){
        if(trackingId==null || !trackingId.matches("[A-Z0-9]{6,8}")){message("Enter a valid tracking ID.");return null;}
        try{cargo=facade.loadCargoForRouting(trackingId);}
        catch(net.java.cargotracker.interfaces.booking.facade.CargoNotFoundException missing){message("Cargo not found.");return null;}
        return "/admin/show.xhtml?faces-redirect=true&trackingId="+cargo.getTrackingId();
    }
    public void load() throws IOException {
        if(trackingId==null || !trackingId.matches("[A-Z0-9]{6,8}")){notFound();return;}
        try {cargo=facade.loadCargoForRouting(trackingId);}
        catch(net.java.cargotracker.interfaces.booking.facade.CargoNotFoundException missing){notFound();return;}
        destination=cargo.getFinalDestinationCode();
    }
    public void loadRouting()throws IOException{
        load();
        if(FacesContext.getCurrentInstance().getResponseComplete())return;
        routes=facade.requestPossibleRoutesForCargo(cargo.getTrackingId());
        if(routes.isEmpty())message("No sample routes meet this cargo's arrival deadline.");
    }
    public List<RouteCandidate> getRoutes(){return routes;}
    public int getSelectedRoute(){return selectedRoute;}
    public void setSelectedRoute(int value){selectedRoute=value;}
    public List<jakarta.faces.model.SelectItem> getRouteChoices(){
        List<jakarta.faces.model.SelectItem> choices=new ArrayList<>();
        for(int i=0;i<routes.size();i++)choices.add(new jakarta.faces.model.SelectItem(i,"Route "+(i+1)+" ("+routes.get(i).getLegs().size()+" legs)"));
        return choices;
    }
    public String assignRoute(){
        if(cargo==null || selectedRoute<0 || selectedRoute>=routes.size()){message("Choose a valid route.");return null;}
        try{facade.assignCargoToRoute(cargo.getTrackingId(),routes.get(selectedRoute));}
        catch(net.java.cargotracker.application.RouteSelectionException stale){message(stale.getMessage());return null;}
        return "/admin/show.xhtml?faces-redirect=true&trackingId="+cargo.getTrackingId();
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
