package lab.spike;
import jakarta.ejb.Stateless;
import jakarta.ejb.TransactionAttribute;
import jakarta.ejb.TransactionAttributeType;
import jakarta.annotation.security.DeclareRoles;
import jakarta.annotation.security.RolesAllowed;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import jakarta.json.Json;
import jakarta.json.JsonObject;
import jakarta.batch.runtime.BatchRuntime;
import java.util.Properties;
@Stateless @Path("/") @Produces(MediaType.APPLICATION_JSON)
@TransactionAttribute(TransactionAttributeType.NOT_SUPPORTED)
@DeclareRoles({"Reader","Operator","Administrator"})
@RolesAllowed({"Reader","Operator","Administrator"})
public class ProbeResource {
    @Inject ProbeService service;
    @GET @Path("status")
    public JsonObject status() {
        return Json.createObjectBuilder().add("javaFeature",Runtime.version().feature())
            .add("javaVersion",Runtime.version().toString()).add("api","Jakarta EE 11")
            .add("records",service.count()).build();
    }
    @POST @Path("probe") @RolesAllowed({"Operator","Administrator"})
    public Response create() {
        // Service transaction commits both record and message before batch starts.
        String id=service.create();
        Properties properties=new Properties();properties.setProperty("recordId",id);
        long execution=BatchRuntime.getJobOperator().start("capability",properties);
        return Response.accepted(Json.createObjectBuilder().add("id",id).add("batchExecution",execution).build()).build();
    }
    @GET @Path("probe/{id}")
    public Response get(@PathParam("id") String id) {
        ProbeRecord p=service.find(id);
        if(p==null)return Response.status(404).build();
        return Response.ok(Json.createObjectBuilder().add("id",p.id).add("jpa",true)
            .add("messageSeen",p.messageSeen).add("batchSeen",p.batchSeen).build()).build();
    }
    @GET @Path("batch/{id}")
    public JsonObject batch(@PathParam("id") long id) {
        return Json.createObjectBuilder().add("status",BatchRuntime.getJobOperator().getJobExecution(id).getBatchStatus().name()).build();
    }
}

