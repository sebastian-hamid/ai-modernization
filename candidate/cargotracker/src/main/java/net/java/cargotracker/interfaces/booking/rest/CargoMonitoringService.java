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

        for(Cargo cargo:cargos)builder.add(CargoSnapshot.of(cargo));

        return builder.build();
    }
}
