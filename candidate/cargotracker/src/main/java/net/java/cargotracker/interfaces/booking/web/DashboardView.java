package net.java.cargotracker.interfaces.booking.web;
import java.io.Serializable;
import jakarta.faces.view.ViewScoped;
import jakarta.inject.Named;
import org.primefaces.model.dashboard.*;
@Named @ViewScoped
public class DashboardView implements Serializable {
    private DashboardModel model=new DefaultDashboardModel();
    public DashboardView(){
        model.addWidget(new DefaultDashboardWidget("Routed","col-12"));
        model.addWidget(new DefaultDashboardWidget("NotRouted","col-12"));
        model.addWidget(new DefaultDashboardWidget("Claimed","col-12"));
    }
    public DashboardModel getModel(){return model;}
    public void setModel(DashboardModel model){this.model=model;}
    public String getName(){return "Cargo Tracker";}
}
