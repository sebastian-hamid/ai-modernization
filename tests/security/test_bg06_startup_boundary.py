import re
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
JAVA = ROOT / "candidate/cargotracker/src/main/java"
WEBAPP = ROOT / "candidate/cargotracker/src/main/webapp"


def java_sources():
    return list(JAVA.rglob("*.java"))


def compose_ports_blocks(text):
    lines = text.splitlines()
    blocks = []
    in_services = False
    service = None
    for index, line in enumerate(lines):
        if line == "services:":
            in_services = True
            service = None
            continue
        if in_services:
            if line.strip() and not line.lstrip().startswith("#"):
                indent = len(line) - len(line.lstrip())
                if indent == 0:
                    in_services = False
                    service = None
                elif indent == 2:
                    match_service = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
                    service = match_service.group(1) if match_service else None
        match = re.match(r"^( *)ports\s*:\s*(.*)$", line)
        if not match:
            continue
        parent_indent = len(match.group(1))
        inline = match.group(2).strip()
        entries = [inline] if inline else []
        if not inline:
            for child in lines[index + 1:]:
                if not child.strip() or child.lstrip().startswith("#"):
                    continue
                indent = len(child) - len(child.lstrip())
                if indent <= parent_indent:
                    break
                entries.append(child.strip())
        blocks.append((service if in_services else None, entries))
    return blocks

class Bg06StartupBoundaryTests(unittest.TestCase):
    def test_sample_generator_is_container_startup_only_and_opt_in(self):
        path = JAVA / "net/java/cargotracker/application/util/SampleDataGenerator.java"
        source = path.read_text()
        method = source.index("public void loadSampleData()")
        body = source[method:]
        guard = body.index('if (!Boolean.getBoolean("lab.candidate.disposable")) return;')
        destructive = body.index("unLoadAll();")
        self.assertIn("@Singleton", source)
        self.assertIn("@Startup", source)
        self.assertIn("@PostConstruct", source)
        self.assertLess(guard, destructive)
        self.assertNotIn("@Path(", source)
        self.assertNotIn("@WebServlet", source)
        self.assertNotIn("@Remote", source)
        self.assertNotIn("@Schedule", source)

    def test_no_candidate_java_caller_invokes_sample_generator(self):
        generator = JAVA / "net/java/cargotracker/application/util/SampleDataGenerator.java"
        callers = [p.relative_to(ROOT).as_posix() for p in java_sources()
                   if p != generator and "SampleDataGenerator" in p.read_text()]
        self.assertEqual(callers, [])

    def test_candidate_network_entry_point_inventory_is_explicit(self):
        sources = java_sources()
        rest_path_map = {p.name: set(re.findall(r'@Path\("([^"]+)"\)', p.read_text()))
                         for p in sources if "@Path(" in p.read_text()}
        app_paths = {p.name: set(re.findall(r'@ApplicationPath\("([^"]+)"\)', p.read_text()))
                     for p in sources if "@ApplicationPath(" in p.read_text()}
        self.assertEqual(app_paths, {"RestConfiguration.java": {"rest"}})
        self.assertEqual(rest_path_map, {
            "CargoMonitoringService.java": {"/cargo"},
            "HandlingReportService.java": {"/handling", "/reports"},
            "GraphTraversalService.java": {"/graph-traversal", "/shortest-path"},
        })
        servlet_mappings = {}
        for source_path in sources:
            source = source_path.read_text()
            annotation = re.search(r"@WebServlet\((.*?)\)", source, re.DOTALL)
            if annotation:
                servlet_mappings[source_path.name] = set(re.findall(r'"([^"]+)"', annotation.group(1)))
        self.assertEqual(servlet_mappings, {
            "SessionServlet.java": {"/session"},
            "LegacyNavigationServlet.java": {
                "/public/track.xhtml", "/admin/map.xhtml", "/admin/mapFrame.html",
                "/admin/selectItinerary.xhtml", "/eventLogger/eventLogger.xhtml",
                "/eventLogger/root.xhtml", "/booking/booking.xhtml",
                "/booking/booking-date.xhtml", "/booking/booking-destination.xhtml",
            },
        })
        web = ET.parse(WEBAPP / "WEB-INF/web.xml").getroot()
        ns = {"j": "https://jakarta.ee/xml/ns/jakartaee"}
        declarations = {item.findtext("j:servlet-name", namespaces=ns):
                        item.findtext("j:servlet-class", namespaces=ns)
                        for item in web.findall("j:servlet", ns)}
        mappings = {item.findtext("j:servlet-name", namespaces=ns):
                    [path.text for path in item.findall("j:url-pattern", ns)]
                    for item in web.findall("j:servlet-mapping", ns)}
        self.assertEqual(declarations, {
            "login": "lab.modernization.security.LocalLoginServlet",
            "logout": "lab.modernization.security.LocalLogoutServlet",
            "Faces Servlet": "jakarta.faces.webapp.FacesServlet",
        })
        self.assertEqual(mappings, {
            "login": ["/login"], "logout": ["/logout"], "Faces Servlet": ["*.xhtml"],
        })
        websocket = [p.read_text() for p in sources if "@ServerEndpoint(" in p.read_text()]
        self.assertEqual(len(websocket), 1)
        self.assertIn('@ServerEndpoint("/tracking")', websocket[0])
        self.assertNotIn("@OnMessage", websocket[0])
        mdb_names = {re.search(r"public class (\w+)", p.read_text()).group(1)
                     for p in sources if "@MessageDriven" in p.read_text()}
        self.assertEqual(mdb_names, {
            "CargoHandledConsumer", "DeliveredCargoConsumer",
            "HandlingEventRegistrationAttemptConsumer", "MisdirectedCargoConsumer",
            "RejectedRegistrationAttemptsConsumer",
        })
        startup_names = {re.search(r"public class (\w+)", p.read_text()).group(1)
                         for p in sources if "@Startup" in p.read_text()}
        self.assertEqual(startup_names, {"SampleDataGenerator", "BatchImportRequestService"})
        self.assertFalse(any("@Remote" in p.read_text() for p in sources))
        self.assertFalse(any(re.search(r"@(Schedule|Schedules|Timeout)\b", p.read_text())
                             for p in sources))

    def test_admin_staged_import_is_separate_from_bg06_startup_and_migration(self):
        page = (WEBAPP / "admin/import.xhtml").read_text()
        view = (JAVA / "net/java/cargotracker/interfaces/handling/file/BatchImportView.java").read_text()
        request = (JAVA / "net/java/cargotracker/interfaces/handling/file/BatchImportRequestService.java").read_text()
        paths = (JAVA / "net/java/cargotracker/interfaces/handling/file/BatchImportPaths.java").read_text()
        launcher = (JAVA / "net/java/cargotracker/interfaces/handling/file/BatchImportLauncher.java").read_text()
        self.assertIn("#{batchImportView.start}", page)
        self.assertIn('ENABLED_PROPERTY = "lab.import.enabled"', paths)
        self.assertIn('@RolesAllowed("Administrator")', request)
        self.assertIn('@RunAs("BatchTrigger")', request)
        self.assertIn('@RolesAllowed("BatchTrigger")', launcher)
        self.assertIn('@RunAs("BatchWorker")', launcher)
        self.assertIn('JOB_NAME = "EventFilesProcessorJob"', paths)
        for source in (page, view, request, paths, launcher):
            self.assertNotIn("SampleDataGenerator", source)
            self.assertNotIn("schema-generation", source)

    def test_candidate_database_fixture_exposes_only_local_app_http_port(self):
        compose = (ROOT / "infrastructure/database/compose.yaml").read_text()
        self.assertEqual(compose_ports_blocks(compose), [
            ("candidate-app", ['- "127.0.0.1:8082:8080"']),
        ])
        self.assertNotIn("9990:", compose)
        self.assertNotIn("9993:", compose)
        self.assertNotIn("4447:", compose)


if __name__ == "__main__":
    unittest.main()
