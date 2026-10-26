pipeline {
    agent { label 'ai-modernization-baseline' }
    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10', artifactNumToKeepStr: '5'))
    }
    stages {
        stage('Load local source snapshot') {
            steps {
                deleteDir()
                sh 'cp -a /lab-source/. .'
            }
        }
        stage('Setup tooling checks') {
            steps { sh 'python3 -m unittest discover -s tests -v' }
        }
        stage('Recover pinned sources') {
            steps { sh 'python3 ci/baseline.py sources' }
        }
        stage('Recover dependencies and package') {
            steps { sh 'python3 ci/baseline.py package' }
        }
        stage('Domain tests') {
            steps { sh 'python3 ci/baseline.py domain' }
        }
        stage('GlassFish integration and workflow checks') {
            steps { sh 'python3 ci/baseline.py runtime' }
        }
    }
    post {
        always {
            junit testResults: 'ci-results/domain/TEST-*.xml,ci-results/integration/TEST-*.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'ci-results/**,notes/evidence/**', allowEmptyArchive: true, fingerprint: true
        }
    }
}
