import jenkins.model.Jenkins
import hudson.model.Node
import hudson.slaves.DumbSlave
import hudson.slaves.JNLPLauncher
import hudson.slaves.RetentionStrategy
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition
import groovy.json.JsonOutput
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import java.nio.file.attribute.PosixFilePermissions

def j = Jenkins.get()
def seed = new File(j.rootDir, 'ai-modernization-bootstrap')
def name = 'ai-modernization-baseline'
def node = j.getNode(name)
def item = j.getItem(name)
// Validate ownership before changing any existing job/node or writing its secret.
if (item != null && (!(item instanceof WorkflowJob) ||
        !item.getDescription()?.startsWith('Recovered Cargo Tracker baseline'))) {
    throw new IllegalStateException('Refusing to replace an unrelated existing job')
}
if (node != null && (!(node instanceof DumbSlave) ||
        node.getRemoteFS() != '/home/jenkins/agent' ||
        node.getNumExecutors() != 1 || node.getMode() != Node.Mode.EXCLUSIVE ||
        node.getLabelString() != name ||
        !node.getNodeDescription()?.startsWith('Isolated Java 8 baseline builds'))) {
    throw new IllegalStateException('Refusing to reuse an unrelated existing node')
}
if (node == null) {
    node = new DumbSlave(name, '/home/jenkins/agent', new JNLPLauncher(true))
    node.setNodeDescription('Isolated Java 8 baseline builds; Java 21 remoting; no Docker socket')
    node.setNumExecutors(1)
    node.setMode(Node.Mode.EXCLUSIVE)
    node.setLabelString(name)
    node.setRetentionStrategy(new RetentionStrategy.Always())
    j.addNode(node)
} else {
    assert node.getLabelString().contains(name): 'Unexpected pre-existing node'
}
def temporarySecret = Files.createTempFile(seed.toPath(), 'agent-secret-', '.tmp',
        PosixFilePermissions.asFileAttribute(PosixFilePermissions.fromString('rw-------')))
Files.writeString(temporarySecret, node.toComputer().getJnlpMac())
Files.move(temporarySecret, new File(seed, 'agent-secret').toPath(),
        StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE)
def job = item ?: j.createProject(WorkflowJob, name)
job.setDescription('Recovered Cargo Tracker baseline from a local source snapshot. Application source pinned to 57fc7b32d2597e43b5e0d454e707e0146de5258a. SCM-triggered execution pending review/commit.')
job.setDefinition(new CpsFlowDefinition(new File(seed, 'Jenkinsfile').text, true))
job.save()
def previousExecutors = j.getNumExecutors()
j.setNumExecutors(0)
j.save()
if (job.getLastBuild() == null) { job.scheduleBuild2(0) }
new File(seed, 'status.json').text = JsonOutput.toJson([job:name, node:name, previousControllerExecutors:previousExecutors, controllerExecutors:0, configuredAt:new Date().format("yyyy-MM-dd'T'HH:mm:ssXXX")])
println('AI modernization baseline job and isolated agent configured; controller execution disabled.')
