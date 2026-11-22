package net.java.cargotracker.interfaces.handling.rest;

import jakarta.ejb.EJB;
import jakarta.ejb.Stateless;
import jakarta.annotation.security.RolesAllowed;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.Context;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.core.SecurityContext;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.json.JsonObject;
import net.java.cargotracker.infrastructure.quarantine.HandlingAttemptQuarantineService;
import net.java.cargotracker.infrastructure.quarantine.HandlingReplayConflictException;

/** Administrator-only status and review API for expired handling attempts. */
@RolesAllowed("Administrator")
@Stateless
@Path("/handling/quarantine")
public class HandlingAttemptQuarantineResource {
    @EJB
    private HandlingAttemptQuarantineService quarantineService;

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public JsonObject listAndStatus() {
        return quarantineService.snapshot();
    }

    @POST
    @Path("/replay")
    @Produces(MediaType.APPLICATION_JSON)
    public Response replay(@QueryParam("id") long id, @Context SecurityContext securityContext) {
        try {
            JsonObject result = quarantineService.replay(id, securityContext.getUserPrincipal().getName());
            return Response.accepted(result).build();
        } catch (HandlingReplayConflictException conflict) {
            return Response.status(Response.Status.CONFLICT)
                    .entity("Quarantine entry is already queued, processed, or otherwise unavailable").build();
        }
    }
}
