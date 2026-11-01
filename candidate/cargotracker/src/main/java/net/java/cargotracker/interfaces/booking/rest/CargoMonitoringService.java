package net.java.cargotracker.interfaces.booking.rest;

import java.util.List;
import jakarta.ejb.Stateless;
import jakarta.inject.Inject;
import jakarta.json.Json;
import jakarta.json.JsonArray;
import jakarta.json.JsonArrayBuilder;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import net.java.cargotracker.domain.model.cargo.Cargo;
import net.java.cargotracker.domain.model.cargo.CargoRepository;

@jakarta.annotation.security.RolesAllowed({"Reader","Operator","Administrator"})
@Stateless
@Path("/cargo")
public class CargoMonitoringService {

    public static final String ISO_8601_FORMAT = "yyyy-MM-dd HH:mm";
    @Inject
    private CargoRepository cargoRepository;

    public CargoMonitoringService() {}

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public JsonArray getAllCargo() {
        List<Cargo> cargos = cargoRepository.findAll();

        JsonArrayBuilder builder = Json.createArrayBuilder();

        for (Cargo cargo : cargos) {
            builder.add(Json.createObjectBuilder()
                    .add("trackingId", cargo.getTrackingId().getIdString())
                    .add("routingStatus", cargo.getDelivery()
                            .getRoutingStatus().toString())
                    .add("misdirected", cargo.getDelivery().isMisdirected())
                    .add("transportStatus", cargo.getDelivery()
                            .getTransportStatus().toString())
                    .add("atDestination", cargo.getDelivery()
                            .isUnloadedAtDestination())
                    .add("origin", cargo.getOrigin().getUnLocode().getIdString())
                    .add("lastKnownLocation",
                            cargo.getDelivery().getLastKnownLocation().getUnLocode().getIdString().equals("XXXXX")
                                    ? "Unknown"
                                    : cargo.getDelivery().getLastKnownLocation().getUnLocode().getIdString())
            );
        }

        return builder.build();
    }
}
