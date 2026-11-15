package net.java.cargotracker.interfaces.tracking.web;

import java.io.Serializable;
import java.util.List;
import jakarta.faces.application.FacesMessage;
import jakarta.faces.context.FacesContext;
import jakarta.faces.view.ViewScoped;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.inject.Inject;
import jakarta.inject.Named;
import net.java.cargotracker.domain.model.cargo.Cargo;
import net.java.cargotracker.domain.model.cargo.CargoRepository;
import net.java.cargotracker.domain.model.cargo.TrackingId;
import net.java.cargotracker.domain.model.handling.HandlingEvent;
import net.java.cargotracker.domain.model.handling.HandlingEventRepository;

/**
 * Backing bean for tracking cargo. This interface sits immediately on top of
 * the domain layer, unlike the booking interface which has a facade and
 * supporting DTOs in between.
 * <p/>
 * An adapter class, designed for the tracking use case, is used to wrap the
 * domain model to make it easier to work with in a web page rendering context.
 * We do not want to apply view rendering constraints to the design of our
 * domain model and the adapter helps us shield the domain model classes where
 * needed.
 * <p/>
 * In some very simplistic cases, it is fine to not use even an adapter.
 */
@Named
@ViewScoped
public class Track implements Serializable {

    private static final long serialVersionUID = 1L;

    @Inject
    private HttpServletRequest request;
    @Inject
    private CargoRepository cargoRepository;
    @Inject
    private HandlingEventRepository handlingEventRepository;

    private String trackingId;
    private CargoTrackingViewAdapter cargo;

    public String getTrackingId() {
        return trackingId;
    }

    public void setTrackingId(String trackingId) {
        // TODO See if a more global trimming mechanism is needed.
        if (trackingId != null) {
            trackingId = trackingId.trim();
        }

        this.trackingId = trackingId;
    }

    public CargoTrackingViewAdapter getCargo() {
        return cargo;
    }

    public void setCargo(CargoTrackingViewAdapter cargo) {
        this.cargo = cargo;
    }

    public void lookupOnGet() throws java.io.IOException {
        String[] values = request.getParameterValues("trackingId");
        if (values == null) return;
        if (values.length != 1 || trackingId == null || !trackingId.matches("[A-Z0-9]{6,8}")) {
            notFound(); return;
        }
        loadCargo();
        if (cargo == null) notFound();
    }

    public void onTrackById() {
        if (trackingId == null || !trackingId.matches("[A-Z0-9]{6,8}")) {
            notFoundMessage(); return;
        }
        loadCargo();
    }

    private void loadCargo() {
        Cargo cargo = cargoRepository.find(new TrackingId(trackingId));

        if (cargo != null) {
            List<HandlingEvent> handlingEvents = handlingEventRepository
                    .lookupHandlingHistoryOfCargo(new TrackingId(trackingId))
                    .getDistinctEventsByCompletionTime();
            this.cargo = new CargoTrackingViewAdapter(cargo, handlingEvents);
        } else {
            // TODO See if this can be injected.
            FacesContext context = FacesContext.getCurrentInstance();
            FacesMessage message = new FacesMessage("Cargo not found.");
            message.setSeverity(FacesMessage.SEVERITY_ERROR);
            context.addMessage(null, message);
            this.cargo = null;
        }
    }

    private void notFound() throws java.io.IOException {
        FacesContext context = FacesContext.getCurrentInstance();
        context.getExternalContext().responseSendError(404, "Cargo not found");
        context.responseComplete();
    }

    private void notFoundMessage() {
        FacesContext context = FacesContext.getCurrentInstance();
        FacesMessage message = new FacesMessage("Enter a valid tracking ID.");
        message.setSeverity(FacesMessage.SEVERITY_ERROR);
        context.addMessage(null, message);
        this.cargo = null;
    }
}
