package lab.fixture;

import jakarta.batch.operations.JobOperator;
import jakarta.batch.operations.JobSecurityException;
import jakarta.batch.runtime.BatchRuntime;
import jakarta.ejb.EJB;
import jakarta.ejb.EJBException;
import jakarta.ejb.EJBAccessException;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import jakarta.jms.MessageListener;
import jakarta.jms.JMSContext;
import jakarta.jms.Queue;
import jakarta.annotation.Resource;
import jakarta.jms.ObjectMessage;
import java.util.Properties;
import java.util.UUID;
import net.java.cargotracker.interfaces.handling.file.BatchImportRequestService;
import net.java.cargotracker.application.HandlingEventService;
import net.java.cargotracker.application.CargoInspectionService;
import net.java.cargotracker.domain.model.handling.HandlingEvent;
import net.java.cargotracker.domain.model.handling.CannotCreateHandlingEventException;
import net.java.cargotracker.domain.model.cargo.TrackingId;
import net.java.cargotracker.domain.model.location.UnLocode;
import net.java.cargotracker.interfaces.handling.HandlingEventRegistrationAttempt;
import java.util.Date;

/** Test-only endpoint for exercising BatchRuntime under real HTTP principals. */
public final class BatchApiProbe extends HttpServlet {
    @EJB
    private BatchImportRequestService importRequests;
    @EJB
    private HandlingEventService handlingEventService;
    @EJB
    private CargoInspectionService cargoInspectionService;
    @jakarta.inject.Inject
    private JMSContext jmsContext;
    @Resource(lookup = "java:app/jms/HandlingEventRegistrationAttemptQueue")
    private Queue handlingEventQueue;

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) throws IOException {
        String operation = request.getParameter("operation");
        if ("switch".equals(operation)) {
            if (request.getUserPrincipal() == null || !request.isUserInRole("Administrator")) {
                response.sendError(403);
                return;
            }
            String enabled = request.getParameter("enabled");
            if (!"true".equals(enabled) && !"false".equals(enabled)) {
                response.sendError(400);
                return;
            }
            String nonce = null;
            if ("false".equals(enabled)) {
                nonce = UUID.randomUUID().toString();
                importRequests.issueNonce(request.getSession(true).getId(), nonce);
            }
            System.setProperty("lab.import.enabled", enabled);
            if (nonce != null) {
                response.setHeader("X-Fixture-Issued-Nonce", nonce);
            }
            response.setStatus(204);
            return;
        }
        if ("service-start".equals(operation)) {
            if (request.getUserPrincipal() == null || !request.isUserInRole("Administrator")) {
                response.sendError(403);
                return;
            }
            try {
                importRequests.start(request.getSession(true).getId(),
                        request.getParameter("nonce"), request.getUserPrincipal().getName());
                response.setStatus(200);
                response.getWriter().write("service start succeeded");
            } catch (IllegalStateException disabled) {
                if ("Import is disabled by server configuration".equals(disabled.getMessage())) {
                    response.setHeader("X-Fixture-Probe-Result", "disabled-before-launch");
                    response.sendError(409);
                } else {
                    response.setHeader("X-Fixture-Probe-Failure", disabled.getClass().getSimpleName());
                    response.sendError(500);
                }
            } catch (EJBException wrapped) {
                Throwable cause = wrapped;
                boolean disabled = false;
                for (int depth = 0; cause != null && depth < 8; depth++) {
                    if (cause instanceof IllegalStateException
                            && "Import is disabled by server configuration".equals(cause.getMessage())) {
                        disabled = true;
                        break;
                    }
                    if (cause.getCause() == cause) break;
                    cause = cause.getCause();
                }
                if (disabled) {
                    response.setHeader("X-Fixture-Probe-Result", "disabled-before-launch");
                    response.sendError(409);
                } else {
                    response.setHeader("X-Fixture-Probe-Failure", cause == null
                            ? wrapped.getClass().getSimpleName() : cause.getClass().getSimpleName());
                    response.sendError(500);
                }
            } catch (RuntimeException unexpected) {
                response.setHeader("X-Fixture-Probe-Failure", unexpected.getClass().getSimpleName());
                response.sendError(500);
            }
            return;
        }
        if ("poison-handling-attempt".equals(operation)) {
            if (request.getUserPrincipal() == null || !request.isUserInRole("Administrator")) {
                response.sendError(403);
                return;
            }
            try {
                Date now = new Date();
                HandlingEventRegistrationAttempt attempt = new HandlingEventRegistrationAttempt(
                        now, now, new TrackingId("NOCARGO1"), null, HandlingEvent.Type.RECEIVE,
                        new UnLocode("USCHI"));
                ObjectMessage message = jmsContext.createObjectMessage(attempt);
                jmsContext.createProducer().send(handlingEventQueue, message);
                response.setStatus(202);
            } catch (RuntimeException rejected) {
                response.sendError(500);
            }
            return;
        }
        if ("notification-consumer".equals(operation)) {
            String[] consumers = {"DeliveredCargoConsumer", "MisdirectedCargoConsumer",
                "RejectedRegistrationAttemptsConsumer"};
            boolean exposed = false;
            try {
                InitialContext context = new InitialContext();
                for (String consumer : consumers) {
                    String name = "java:app/cargo-tracker/" + consumer + "!" + MessageListener.class.getName();
                    try {
                        context.lookup(name);
                        exposed = true;
                    } catch (NamingException notExposed) {
                        // Message-driven beans must not publish a caller-facing business view.
                    }
                }
                context.close();
            } catch (NamingException lookupFailure) {
                response.sendError(500);
                return;
            }
            if (exposed) {
                response.setHeader("X-Fixture-Probe-Failure", "consumer-view-exposed");
                response.sendError(500);
            } else {
                response.setHeader("X-Fixture-Probe-Result", "no-consumer-client-view");
                response.sendError(403);
            }
            return;
        }
        if ("inspection-service".equals(operation)) {
            try {
                cargoInspectionService.inspectCargo(new TrackingId("ABC123"));
                response.setStatus(200);
                response.setContentType("text/plain;charset=UTF-8");
                response.getWriter().write("inspection service call completed");
            } catch (EJBAccessException denied) {
                response.setHeader("X-Fixture-Probe-Result", "worker-only-denied");
                response.sendError(403);
            } catch (RuntimeException unexpected) {
                response.setHeader("X-Fixture-Probe-Failure", unexpected.getClass().getSimpleName());
                response.sendError(500);
            }
            return;
        }
        if ("handling-service".equals(operation)) {
            try {
                handlingEventService.registerHandlingEvent(new Date(),
                        new TrackingId("ABC123"), null, new UnLocode("FIHEL"),
                        HandlingEvent.Type.RECEIVE);
                response.setStatus(200);
                response.setContentType("text/plain;charset=UTF-8");
                response.getWriter().write("handling service call completed");
            } catch (EJBAccessException denied) {
                response.setHeader("X-Fixture-Probe-Result", "worker-only-denied");
                response.sendError(403);
            } catch (CannotCreateHandlingEventException invalidEvent) {
                response.setHeader("X-Fixture-Probe-Result", "handling-event-rejected");
                response.sendError(422);
            } catch (RuntimeException unexpected) {
                response.setHeader("X-Fixture-Probe-Failure", unexpected.getClass().getSimpleName());
                response.sendError(500);
            }
            return;
        }
        try {
            JobOperator operator = BatchRuntime.getJobOperator();
            if ("read".equals(operation)) {
                operator.getJobNames();
            } else if ("start".equals(operation)) {
                operator.start("EventFilesProcessorJob", new Properties());
            } else if ("restart".equals(operation)) {
                String id = request.getParameter("executionId");
                operator.restart(Long.parseLong(id), new Properties());
            } else {
                response.sendError(400);
                return;
            }
            response.setStatus(200);
            response.setContentType("text/plain;charset=UTF-8");
            response.getWriter().write("operation completed");
        } catch (JobSecurityException | SecurityException denied) {
            response.sendError(403);
        } catch (RuntimeException unexpected) {
            response.setHeader("X-Fixture-Probe-Failure", unexpected.getClass().getSimpleName());
            response.sendError(500);
        }
    }
}
