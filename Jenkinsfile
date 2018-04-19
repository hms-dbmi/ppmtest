pipeline {
    agent any
    parameters {
        text(
            defaultValue: 'test.PPMTestCase.test_neer_firefox',
            description: 'The tests to run against the stack',
            name: 'test')
    }

    environment {
        COMPOSE_PROJECT_NAME = "${ env.JOB_NAME }-${ env.BUILD_ID }"
    }

    stages {
        stage ('Checkout') {
            steps {
                // Get app code
                checkout scm
            }
        }

        stage ('Setup') {
            steps {
                sh("./setup.sh")
            }
        }

        stage ('Test') {
            steps {
                sh("./test.sh ${ params.test }")
            }
        }
    }

    post {

        always {

            // Get artifacts
            sh("./artifacts.sh")

            // Collect logs and such
            archiveArtifacts artifacts: '*.log', fingerprint: true

            // Cleanup
            sh("./cleanup.sh")

            // Purge workspace
            deleteDir()
        }
    }
}