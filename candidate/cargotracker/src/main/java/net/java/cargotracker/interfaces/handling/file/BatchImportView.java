package net.java.cargotracker.interfaces.handling.file;

import jakarta.annotation.PostConstruct;
import jakarta.faces.application.FacesMessage;
import jakarta.faces.context.FacesContext;
import jakarta.faces.view.ViewScoped;
import jakarta.inject.Inject;
import jakarta.inject.Named;
import jakarta.servlet.http.HttpServletRequest;
import java.io.Serializable;
import java.util.UUID;
import lab.modernization.security.SessionTokens;

@Named
@ViewScoped
public class BatchImportView implements Serializable {
    @Inject
    private BatchImportRequestService requestService;
    @Inject
    private HttpServletRequest request;

    private final String nonce = UUID.randomUUID().toString();
    private BatchImportResult result;

    @PostConstruct
    public void initialize() {
        if (request.getSession(false) == null) {
            throw new IllegalStateException("Authenticated session is required");
        }
        requestService.issueNonce(request.getSession(false).getId(), nonce);
    }

    public String getNonce() {
        return nonce;
    }

    public String getCsrf() {
        return SessionTokens.get(request.getSession());
    }

    public boolean isEnabled() {
        return Boolean.getBoolean(BatchImportPaths.ENABLED_PROPERTY);
    }

    public BatchImportResult getResult() {
        return result;
    }

    public void start() {
        try {
            if (request.getUserPrincipal() == null) {
                throw new SecurityException("Authenticated Administrator is required");
            }
            result = requestService.start(request.getSession(false).getId(), nonce,
                    request.getUserPrincipal().getName());
            FacesContext.getCurrentInstance().addMessage(null,
                    new FacesMessage(FacesMessage.SEVERITY_INFO,
                            "Import accepted as run " + result.runId(), null));
        } catch (RuntimeException deniedOrUnavailable) {
            FacesContext.getCurrentInstance().addMessage(null,
                    new FacesMessage(FacesMessage.SEVERITY_ERROR,
                            "Import was not started. Refresh the page or contact an administrator.", null));
        }
    }
}
