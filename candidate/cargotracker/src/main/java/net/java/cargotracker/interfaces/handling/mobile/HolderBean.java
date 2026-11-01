package net.java.cargotracker.interfaces.handling.mobile;

//import jakarta.enterprise.context.SessionScoped;
import java.io.Serializable;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.context.RequestScoped;
import jakarta.enterprise.context.SessionScoped;
import jakarta.faces.context.FacesContext;
import jakarta.faces.flow.FlowHandler;
import jakarta.inject.Named;

/**
 *
 * @author davidd
 */
@Named
@SessionScoped
public class HolderBean implements Serializable{

    // TODO: this is really a workaround for now as viewaction can't invoke a faceflow directly!

    private String holder = "workaround";

    void setHolder(String holder) {
        this.holder = holder;
    }

    public String getHolder() {
        return holder;
    }

    public String initFlow() {
        FacesContext context = FacesContext.getCurrentInstance();
        FlowHandler handler = context.getApplication().getFlowHandler();
        handler.transition(context, null, handler.getFlow(context, "", "eventLogger"), null, "");
        return "eventLogger";
    }

}
