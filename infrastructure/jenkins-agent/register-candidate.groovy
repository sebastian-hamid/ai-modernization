import jenkins.model.Jenkins
import hudson.model.Node
import hudson.slaves.DumbSlave
import hudson.slaves.JNLPLauncher
import hudson.slaves.RetentionStrategy
import hudson.plugins.git.GitSCM
import hudson.plugins.git.BranchSpec
import hudson.plugins.git.UserRemoteConfig
import hudson.triggers.SCMTrigger
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition
import groovy.json.JsonOutput
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import java.nio.file.attribute.PosixFilePermissions

def j = Jenkins.get()
def root = j.rootDir
def seed = new File(root, 'ai-modernization-candidate-bootstrap')
def nodeName = 'ai-modernization-candidate'
def jobName = 'ai-modernization-candidate'
def repository = 'https://github.com/sebastian-hamid/ai-modernization.git'
def branch = '*/main'
def scriptPath = 'candidate/cargotracker/Jenkinsfile'
def node = j.getNode(nodeName)
def item = j.getItem(jobName)

if (item != null && (!(item instanceof WorkflowJob) ||
        !item.getDescription()?.startsWith('AI Modernization candidate CI'))) {
    throw new IllegalStateException('Refusing to replace an unrelated existing candidate job')
}
if (node != null && (!(node instanceof DumbSlave) ||
        node.getRemoteFS() != '/home/jenkins/agent' ||
        node.getNumExecutors() != 1 || node.getMode() != Node.Mode.EXCLUSIVE ||
        node.getLabelString() != nodeName ||
        !node.getNodeDescription()?.startsWith('Isolated Java 25 candidate CI builds'))) {
    throw new IllegalStateException('Refusing to reuse an unrelated existing candidate node')
}
if (!seed.isDirectory() && !seed.mkdirs()) {
    throw new IllegalStateException('Could not create candidate bootstrap directory')
}
if (node == null) {
    node = new DumbSlave(nodeName, '/home/jenkins/agent', new JNLPLauncher(true))
    node.setNodeDescription('Isolated Java 25 candidate CI builds; no Docker socket or build secrets')
    node.setNumExecutors(1)
    node.setMode(Node.Mode.EXCLUSIVE)
    node.setLabelString(nodeName)
    node.setRetentionStrategy(new RetentionStrategy.Always())
    j.addNode(node)
}
def temporarySecret = Files.createTempFile(seed.toPath(), 'agent-secret-', '.tmp',
        PosixFilePermissions.asFileAttribute(PosixFilePermissions.fromString('rw-------')))
Files.writeString(temporarySecret, node.toComputer().getJnlpMac())
Files.move(temporarySecret, new File(seed, 'agent-secret').toPath(),
        StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE)

def scm = new GitSCM(
        [new UserRemoteConfig(repository, null, null, null)],
        [new BranchSpec(branch)],
        false,
        [],
        null,
        null,
        [])
def definition = new CpsScmFlowDefinition(scm, scriptPath)
definition.setLightweight(true)

def job = item ?: j.createProject(WorkflowJob, jobName)
job.setDescription('AI Modernization candidate CI from public GitHub SCM; isolated Java 25 agent.')
job.setDefinition(definition)
job.removeTrigger(SCMTrigger.class)
job.addTrigger(new SCMTrigger('H/15 * * * *'))
job.save()

if (job.getLastBuild() == null) {
    job.scheduleBuild2(0)
}
new File(seed, 'status.json').text = JsonOutput.toJson([
        job: jobName, node: nodeName, repository: repository, branch: branch,
        scriptPath: scriptPath, pollSchedule: 'H/15 * * * *',
        credentialConfigured: false, controllerExecutorsUnchanged: j.getNumExecutors(),
        configuredAt: new Date().format("yyyy-MM-dd'T'HH:mm:ssXXX")
])
println('AI modernization candidate SCM job and isolated Java 25 agent configured; no GitHub credential configured.')
