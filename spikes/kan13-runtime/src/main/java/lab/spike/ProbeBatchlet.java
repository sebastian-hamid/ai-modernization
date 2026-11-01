package lab.spike;
import jakarta.batch.api.AbstractBatchlet;
import jakarta.batch.runtime.context.JobContext;
import jakarta.enterprise.context.Dependent;
import jakarta.inject.Inject;
import jakarta.inject.Named;
@Named("probeBatchlet") @Dependent
public class ProbeBatchlet extends AbstractBatchlet {
    @Inject JobContext context;
    @Inject ProbeService service;
    public String process() {
        service.markBatch(context.getProperties().getProperty("recordId"));
        return "COMPLETED";
    }
}

