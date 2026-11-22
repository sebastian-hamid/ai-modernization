package net.java.cargotracker.interfaces.handling.rest;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.time.format.ResolverStyle;
import java.util.Date;
import java.util.Locale;
import jakarta.ejb.Stateless;
import jakarta.inject.Inject;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import jakarta.ws.rs.BadRequestException;
import jakarta.ws.rs.HeaderParam;
import jakarta.ws.rs.WebApplicationException;
import jakarta.ws.rs.core.Response;
import java.util.UUID;
import java.util.regex.Pattern;
import net.java.cargotracker.infrastructure.quarantine.HandlingRequestIdConflictException;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.core.MediaType;
import net.java.cargotracker.application.ApplicationEvents;
import net.java.cargotracker.domain.model.cargo.TrackingId;
import net.java.cargotracker.domain.model.handling.HandlingEvent;
import net.java.cargotracker.domain.model.location.UnLocode;
import net.java.cargotracker.domain.model.voyage.VoyageNumber;
import net.java.cargotracker.interfaces.handling.HandlingEventRegistrationAttempt;


/**
 * This REST endpoint implementation performs basic validation and parsing of
 * incoming data, and in case of a valid registration attempt, sends an
 * asynchronous message with the information to the handling event registration
 * system for proper registration.
 */
@jakarta.annotation.security.RolesAllowed({"Operator","Administrator"})
@Stateless // TODO Make this a stateless bean for better scalability.
@Path("/handling")
public class HandlingReportService {

    public static final String ISO_8601_FORMAT = "uuuu-MM-dd HH:mm";
    private static final Pattern REQUEST_ID_PATTERN = Pattern.compile("[A-Za-z0-9._:-]{1,128}");
    private static final DateTimeFormatter COMPLETION_TIME_FORMAT =
            DateTimeFormatter.ofPattern(ISO_8601_FORMAT, Locale.ROOT)
                    .withResolverStyle(ResolverStyle.STRICT);
    @Inject
    private ApplicationEvents applicationEvents;

    public HandlingReportService() {}

    /** Backward-compatible entry point for the mobile form; it receives a fresh request identity. */
    public void submitReport(HandlingReport handlingReport) {
        submitReport(handlingReport, null);
    }

    @POST
    @Path("/reports")
    @Consumes(MediaType.APPLICATION_JSON)
    // TODO Better exception handling.
    public void submitReport(@NotNull @Valid HandlingReport handlingReport,
            @HeaderParam("Idempotency-Key") String requestId) {
        final Date completionTime;
        final HandlingEvent.Type type;
        final UnLocode unLocode;
        final TrackingId trackingId;
        final VoyageNumber voyageNumber;
        try {
            LocalDateTime parsed = LocalDateTime.parse(
                    handlingReport.getCompletionTime(), COMPLETION_TIME_FORMAT);
            completionTime = Date.from(parsed.atZone(ZoneId.systemDefault()).toInstant());
        } catch (DateTimeParseException ex) {
            throw new BadRequestException("Invalid handling report");
        }
        try {
            type = HandlingEvent.Type.valueOf(handlingReport.getEventType());
            unLocode = new UnLocode(handlingReport.getUnLocode());
            trackingId = new TrackingId(handlingReport.getTrackingId());
            voyageNumber = handlingReport.getVoyageNumber() == null ? null
                    : new VoyageNumber(handlingReport.getVoyageNumber());
        } catch (IllegalArgumentException ex) {
            throw new BadRequestException("Invalid handling report");
        }

        if (requestId == null) requestId = UUID.randomUUID().toString();
        else if (!REQUEST_ID_PATTERN.matcher(requestId).matches()) {
            throw new BadRequestException("Invalid Idempotency-Key");
        }

        Date registrationTime = new Date();
        HandlingEventRegistrationAttempt attempt = new HandlingEventRegistrationAttempt(
                registrationTime, completionTime, trackingId, voyageNumber, type, unLocode);
        try {
            applicationEvents.receivedHandlingEventRegistrationAttempt(attempt, requestId);
        } catch (HandlingRequestIdConflictException conflict) {
            throw new WebApplicationException("Idempotency-Key was already used with a different payload",
                    Response.Status.CONFLICT);
        }
    }
}
