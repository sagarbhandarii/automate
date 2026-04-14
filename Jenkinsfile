pipeline {
    agent any

    triggers {
        githubPush()
    }

    options {
        timestamps()
        ansiColor('xterm')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build & Test') {
            steps {
                sh '''
                    set -euxo pipefail
                    mkdir -p artifacts/reports artifacts/logs

                    python3 -m pip install --upgrade pip
                    if [ -f requirements.txt ]; then
                      pip3 install -r requirements.txt
                    fi
                    pip3 install pytest

                    pytest tests --junitxml=artifacts/reports/junit.xml 2>&1 | tee artifacts/logs/test.log
                '''
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'artifacts/reports/junit.xml'
            archiveArtifacts artifacts: 'artifacts/**/*', allowEmptyArchive: true, fingerprint: true
        }
    }
}
