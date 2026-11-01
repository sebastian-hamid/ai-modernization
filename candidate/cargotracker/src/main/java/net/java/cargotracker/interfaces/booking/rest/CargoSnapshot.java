package net.java.cargotracker.interfaces.booking.rest;
import jakarta.json.*;import net.java.cargotracker.domain.model.cargo.Cargo;
/** Same complete authorized snapshot for initial reads and live updates. */
public final class CargoSnapshot {
    private CargoSnapshot(){}
    public static JsonObject forSocket(Cargo cargo){
        return Json.createObjectBuilder(of(cargo)).add("origin",cargo.getOrigin().getName()).add("destination",cargo.getRouteSpecification().getDestination().getName()).add("lastKnownLocation",cargo.getDelivery().getLastKnownLocation().getName()).build();
    }
    public static JsonObject of(Cargo cargo){
        var delivery=cargo.getDelivery();var last=delivery.getLastKnownLocation();
        return Json.createObjectBuilder()
            .add("trackingId",cargo.getTrackingId().getIdString())
            .add("routingStatus",delivery.getRoutingStatus().toString())
            .add("misdirected",delivery.isMisdirected())
            .add("transportStatus",delivery.getTransportStatus().toString())
            .add("atDestination",delivery.isUnloadedAtDestination())
            .add("origin",cargo.getOrigin().getUnLocode().getIdString())
            .add("originName",cargo.getOrigin().getName())
            .add("originCode",cargo.getOrigin().getUnLocode().getIdString())
            .add("destination",cargo.getRouteSpecification().getDestination().getUnLocode().getIdString())
            .add("destinationName",cargo.getRouteSpecification().getDestination().getName())
            .add("destinationCode",cargo.getRouteSpecification().getDestination().getUnLocode().getIdString())
            .add("lastKnownLocation",last.getUnLocode().getIdString().equals("XXXXX")?"Unknown":last.getUnLocode().getIdString())
            .add("lastKnownLocationName",last.getName())
            .add("lastKnownLocationCode",last.getUnLocode().getIdString().equals("XXXXX")?"Unknown":last.getUnLocode().getIdString())
            .add("updatedAt",delivery.getCalculatedAt().getTime()).build();
    }
}
