package net.java.cargotracker.application;
@jakarta.ejb.ApplicationException(rollback=true)
public class RouteSelectionException extends RuntimeException {
    public RouteSelectionException(){super("The selected route no longer matches this cargo. Request routes again.");}
}
