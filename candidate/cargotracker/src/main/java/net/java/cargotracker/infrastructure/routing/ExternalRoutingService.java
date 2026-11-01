package net.java.cargotracker.infrastructure.routing;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.logging.Level;
import java.util.logging.Logger;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.Resource;
import jakarta.ejb.Stateless;
import jakarta.inject.Inject;
import jakarta.ws.rs.client.Client;
import jakarta.ws.rs.client.ClientBuilder;
import jakarta.ws.rs.client.WebTarget;
import jakarta.ws.rs.core.GenericType;
import jakarta.ws.rs.core.MediaType;

import net.java.cargotracker.domain.model.cargo.Itinerary;
import net.java.cargotracker.domain.model.cargo.Leg;
import net.java.cargotracker.domain.model.cargo.RouteSpecification;
import net.java.cargotracker.domain.model.location.LocationRepository;
import net.java.cargotracker.domain.model.location.UnLocode;
import net.java.cargotracker.domain.model.voyage.VoyageNumber;
import net.java.cargotracker.domain.model.voyage.VoyageRepository;
import net.java.cargotracker.domain.service.RoutingService;
import net.java.pathfinder.api.TransitEdge;
import net.java.pathfinder.api.TransitPath;


/**
 * Our end of the routing service. This is basically a data model translation
 * layer between our domain model and the API put forward by the routing team,
 * which operates in a different context from us.
 *
 */
@jakarta.annotation.security.RolesAllowed({"Operator","Administrator"})
@Stateless
public class ExternalRoutingService implements RoutingService {

    @Resource(lookup = "java:app/configuration/GraphTraversalUrl")
    private String graphTraversalUrl;
    // TODO Can I use injection?
    private final Client jaxrsClient = ClientBuilder.newBuilder().connectTimeout(5,java.util.concurrent.TimeUnit.SECONDS).readTimeout(15,java.util.concurrent.TimeUnit.SECONDS).property("dev.resteasy.client.follow.redirects",false).build();
    private WebTarget graphTraversalResource;
    private String authorization;
    @Inject
    private LocationRepository locationRepository;
    @Inject
    private VoyageRepository voyageRepository;
    // TODO Use injection instead?
    private static final Logger log = Logger.getLogger(
            ExternalRoutingService.class.getName());

    @PostConstruct
    public void init() {
        java.net.URI endpoint=java.net.URI.create(graphTraversalUrl);
        if(!"http".equals(endpoint.getScheme()) || !Set.of("localhost","127.0.0.1").contains(endpoint.getHost())
                || endpoint.getPort()!=8080 || !"/cargo-tracker/rest/graph-traversal/shortest-path".equals(endpoint.getPath())
                || endpoint.getUserInfo()!=null || endpoint.getQuery()!=null || endpoint.getFragment()!=null)
            throw new IllegalStateException("Routing endpoint must be the fixed loopback service");
        graphTraversalResource = jaxrsClient.target(endpoint);
        // Credentials are provisioned outside the WAR/image. No fallback to a human identity.
        String credentialFile=System.getProperty("cargo.routing.credentials");
        if(credentialFile==null)throw new IllegalStateException("Routing service credentials must be provisioned");
        java.util.Properties credentials=new java.util.Properties();
        try(var input=java.nio.file.Files.newInputStream(java.nio.file.Path.of(credentialFile))){credentials.load(input);}
        catch(java.io.IOException missing){throw new IllegalStateException("Routing credentials unavailable");}
        String username=credentials.getProperty("username"),password=credentials.getProperty("password");
        if(username==null || password==null || username.isBlank() || password.isBlank())throw new IllegalStateException("Routing credentials incomplete");
        authorization="Basic "+java.util.Base64.getEncoder().encodeToString((username+":"+password).getBytes(java.nio.charset.StandardCharsets.UTF_8));

    }

    @Override
    public List<Itinerary> fetchRoutesForSpecification(
            RouteSpecification routeSpecification) {
        // The RouteSpecification is picked apart and adapted to the external API.
        String origin = routeSpecification.getOrigin().getUnLocode().getIdString();
        String destination = routeSpecification.getDestination().getUnLocode()
                .getIdString();

        List<TransitPath> transitPaths = graphTraversalResource
                .queryParam("origin", origin)
                .queryParam("destination", destination)
                .queryParam("deadline", java.time.Instant.ofEpochMilli(routeSpecification.getArrivalDeadline().getTime()).atZone(java.time.ZoneOffset.UTC).toLocalDate().toString())
                .request(MediaType.APPLICATION_JSON_TYPE)
                .header("Authorization",authorization)
                .get(new GenericType<List<TransitPath>>() {
                });

        // The returned result is then translated back into our domain model.
        List<Itinerary> itineraries = new ArrayList<>();

        for (TransitPath transitPath : transitPaths) {
            Itinerary itinerary = toItinerary(transitPath);
            // Use the specification to safe-guard against invalid itineraries
            if (routeSpecification.isSatisfiedBy(itinerary)) {
                itineraries.add(itinerary);
            } else {
                log.log(Level.FINE,
                        "Received itinerary that did not satisfy the route specification");
            }
        }

        return itineraries;
    }

    @jakarta.annotation.PreDestroy
    public void close(){jaxrsClient.close();}

    private Itinerary toItinerary(TransitPath transitPath) {
        List<Leg> legs = new ArrayList<>(transitPath.getTransitEdges().size());
        for (TransitEdge edge : transitPath.getTransitEdges()) {
            legs.add(toLeg(edge));
        }
        return new Itinerary(legs);
    }

    private Leg toLeg(TransitEdge edge) {
        return new Leg(
                voyageRepository.find(new VoyageNumber(edge.getVoyageNumber())),
                locationRepository.find(new UnLocode(edge.getFromUnLocode())),
                locationRepository.find(new UnLocode(edge.getToUnLocode())),
                edge.getFromDate(), edge.getToDate());
    }
}
