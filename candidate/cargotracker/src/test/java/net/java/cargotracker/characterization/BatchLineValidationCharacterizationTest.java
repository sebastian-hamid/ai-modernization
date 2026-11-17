package net.java.cargotracker.characterization;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.fail;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import net.java.cargotracker.domain.model.handling.HandlingEvent;
import net.java.cargotracker.interfaces.handling.HandlingEventRegistrationAttempt;
import net.java.cargotracker.interfaces.handling.file.EventItemReader;
import net.java.cargotracker.interfaces.handling.file.EventLineParseException;
import org.junit.Test;

/** Characterizes supported and rejected rows in the batch event CSV reader. */
public class BatchLineValidationCharacterizationTest {

    @Test
    public void parsesValidReceiveRow() throws Exception {
        HandlingEventRegistrationAttempt attempt = parse(
                "2026-11-17 09:15,CARGO123,,GBFXT,RECEIVE");

        assertEquals("CARGO123", attempt.getTrackingId().getIdString());
        assertEquals(null, attempt.getVoyageNumber());
        assertEquals("GBFXT", attempt.getUnLocode().getIdString());
        assertEquals(HandlingEvent.Type.RECEIVE, attempt.getType());
    }

    @Test
    public void rejectsRowsWithWrongColumnCount() throws Exception {
        assertRejected("2026-11-17 09:15,CARGO123,,GBFXT");
        assertRejected("2026-11-17 09:15,CARGO123,,GBFXT,RECEIVE,extra");
    }

    @Test
    public void rejectsUnparseableCompletionTime() throws Exception {
        assertRejected("not-a-date,CARGO123,,GBFXT,RECEIVE");
    }

    @Test
    public void rejectsMalformedLocationCode() throws Exception {
        assertRejected("2026-11-17 09:15,CARGO123,,GBF0X,RECEIVE");
    }

    @Test
    public void rejectsUnknownEventType() throws Exception {
        assertRejected("2026-11-17 09:15,CARGO123,,GBFXT,ARRIVE");
    }

    private HandlingEventRegistrationAttempt parse(String line) throws Exception {
        Method parser = EventItemReader.class.getDeclaredMethod("parseLine",
                String.class);
        parser.setAccessible(true);
        try {
            return (HandlingEventRegistrationAttempt) parser.invoke(
                    new EventItemReader(), line);
        } catch (InvocationTargetException wrapped) {
            Throwable cause = wrapped.getCause();
            if (cause instanceof Exception exception) {
                throw exception;
            }
            throw wrapped;
        }
    }

    private void assertRejected(String line) throws Exception {
        try {
            parse(line);
            fail("Invalid batch row should be rejected: " + line);
        } catch (EventLineParseException expected) {
            assertEquals(line, expected.getLine());
        }
    }
}
