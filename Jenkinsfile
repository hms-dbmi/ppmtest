pipeline {
    agent any
    options {
        disableConcurrentBuilds()
    }

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
            sh("mkdir artifacts")
            sh("./artifacts.sh $(pwd)/artifacts  || exit 0")

            dir('artifacts') {
                archiveArtifacts artifacts: '*', fingerprint: true
            }

            // Cleanup
            sh("./cleanup.sh")

            // Purge workspace
            deleteDir()
        }
    }
}