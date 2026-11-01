package net.java.cargotracker.interfaces.booking.facade;
public class CargoNotFoundException extends RuntimeException {
    public CargoNotFoundException(){super("Cargo not found");}
}
