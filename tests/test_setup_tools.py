import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]

class SetupToolTests(unittest.TestCase):
    def project(self, folder):
        root=Path(folder)/"project"
        (root/"ci").mkdir(parents=True)
        (root/"infrastructure").mkdir()
        (root/"tests").mkdir()
        (root/"Jenkinsfile").write_text("pipeline input")
        (root/"VERSION").write_text("0.1.0")
        shutil.copy2(ROOT/"ci/update-local-snapshot.py", root/"ci/update-local-snapshot.py")
        return root

    def refresh(self, root):
        return subprocess.run([sys.executable,root/"ci/update-local-snapshot.py"],capture_output=True,text=True)

    def test_snapshot_removes_deleted_inputs_without_replacing_bind_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.project(folder)
            source=root/"infrastructure/old.sh"
            source.write_text("old")
            self.assertEqual(self.refresh(root).returncode,0)
            snapshot=root/".work/jenkins-ci/source"
            inode=snapshot.stat().st_ino
            source.unlink()
            (root/"infrastructure/new.sh").write_text("new")
            (root/".work/private-secret").write_text("local private material")
            result=self.refresh(root)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse((snapshot/"infrastructure/old.sh").exists())
            self.assertEqual(snapshot.stat().st_ino,inode)
            manifest=json.loads((snapshot/"source-snapshot.json").read_text())
            self.assertIn("infrastructure/new.sh",manifest)
            self.assertFalse(any(".work" in name for name in manifest))

    def test_snapshot_rejects_source_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.project(folder)
            outside=Path(folder)/"outside.txt"
            outside.write_text("outside")
            (root/"infrastructure/link").symlink_to(outside)
            result=self.refresh(root)
            self.assertNotEqual(result.returncode,0)
            self.assertIn("must not be symlinks",result.stderr)

    def test_snapshot_rejects_target_symlink_without_touching_its_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.project(folder)
            self.assertEqual(self.refresh(root).returncode,0)
            outside=Path(folder)/"outside.txt"
            outside.write_text("preserve")
            (root/".work/jenkins-ci/source/link").symlink_to(outside)
            self.assertNotEqual(self.refresh(root).returncode,0)
            self.assertEqual(outside.read_text(),"preserve")

    def test_optimized_python_still_rejects_external_smoke_target_before_network(self):
        script=ROOT/"infrastructure/smoke-legacy-runtime.py"
        code=(
            "import runpy,sys; from unittest.mock import patch; "
            f"sys.argv=[{str(script)!r},'--base-url','https://example.invalid/']; "
            "p=patch('urllib.request.build_opener',side_effect=RuntimeError('NETWORK_REACHED')); p.start(); "
            f"runpy.run_path({str(script)!r},run_name='__main__')"
        )
        result=subprocess.run([sys.executable,"-O","-c",code],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn("Only local lab endpoints",result.stderr)
        self.assertEqual(result.stderr.rstrip().splitlines()[-1], "RuntimeError: Only local lab endpoints are supported")

    def test_optimized_python_rejects_corrupt_runtime_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.project(folder)
            script=root/"infrastructure/prepare-legacy-runtime.py"
            shutil.copy2(ROOT/"infrastructure/prepare-legacy-runtime.py",script)
            archive=root/".work/glassfish-runtime/glassfish-4.1.zip"
            archive.parent.mkdir(parents=True)
            archive.write_bytes(b"corrupted archive")
            result=subprocess.run([sys.executable,"-O",script],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn("archive hash changed",result.stderr)

    def provenance_case(self, root, repository_id):
        cache=root/".work/m2"
        artifact=cache/"org/eclipse/persistence/example/2.3.2/example-2.3.2.jar"
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"artifact")
        (artifact.parent/"_remote.repositories").write_text(f"{artifact.name}>{repository_id}=\n")
        for relative in [
            "org/primefaces/maven-jsf-plugin/1.3.0/maven-jsf-plugin-1.3.0.jar",
            "org/primefaces/themes/ui-lightness/1.0.10/ui-lightness-1.0.10.jar",
        ]:
            path=cache/relative
            path.parent.mkdir(parents=True)
            path.write_bytes(b"rebuilt artifact")
        workspace=root/".work/build"
        war=workspace/"source/target/cargo-tracker.war"
        war.parent.mkdir(parents=True)
        war.write_bytes(b"war")
        evidence=root/"notes/evidence/test"
        (evidence/"surefire-reports").mkdir(parents=True)
        (evidence/"surefire-reports/TEST-example.xml").write_text('<testsuite tests="24" failures="0" errors="0" skipped="0"/>')
        result=subprocess.run([sys.executable,ROOT/"infrastructure/record-legacy-provenance.py",root,workspace,evidence],capture_output=True,text=True)
        return result,evidence

    def test_provenance_recognizes_maven_repository_context_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            result,evidence=self.provenance_case(Path(folder),"eclipselink-https-1cdd05d87b5b7b2778b3776d9980c1a6d57a5697")
            self.assertEqual(result.returncode,0,result.stderr)
            manifest=json.loads((evidence/"dependency-provenance.json").read_text())
            self.assertTrue(manifest["artifacts"][0]["origin"].startswith("https://download.eclipse.org/"))

    def test_provenance_refuses_to_invent_unknown_download_origin(self):
        with tempfile.TemporaryDirectory() as folder:
            result,evidence=self.provenance_case(Path(folder),"unknown-repository")
            self.assertNotEqual(result.returncode,0)
            self.assertIn("No recognized download origin",result.stderr)
            self.assertFalse((evidence/"dependency-provenance.json").exists())

    def test_failed_domain_run_preserves_junit_report(self):
        spec=importlib.util.spec_from_file_location("baseline_under_test",ROOT/"ci/baseline.py")
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            work=root/"work"
            reports=work/"source/target/surefire-reports"
            reports.mkdir(parents=True)
            (work/"source/pom.xml").write_text("<skipTests>true</skipTests>")
            (reports/"TEST-failure.xml").write_text('<testsuite tests="1" failures="1"/>')
            with mock.patch.object(module,"WORK",work),mock.patch.object(module,"RESULTS",root/"results"),mock.patch.object(module,"mvn",side_effect=RuntimeError("build failed")):
                with self.assertRaisesRegex(RuntimeError,"build failed"):
                    module.domain()
            self.assertTrue((root/"results/domain/TEST-failure.xml").exists())

if __name__=="__main__":
    unittest.main()
