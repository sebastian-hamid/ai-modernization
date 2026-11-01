package lab.spike;
import jakarta.inject.Named;
import jakarta.enterprise.context.RequestScoped;
@Named @RequestScoped
public class FacesProbe {
    public String getMessage() { return "KAN13_FACES_OK"; }
}

