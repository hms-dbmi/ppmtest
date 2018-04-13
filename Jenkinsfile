pipeline {
    agent any
    parameters {
        text(
            defaultValue: '',
            description: 'The tests to run against the stack',
            name: 'PPM_TEST_TEST')
        text(
            defaultValue: 'artifacts',
            description: 'The directory to collect output artifacts in',
            name: 'PPM_TEST_ARTIFACTS')
    }

    stages {
        stage ('Checkout') {
            steps {
                git url: 'https://github.com/b32147/ppmtest.git'
            }
        }

        stage ('Setup') {
            steps {
                sh("./setup.sh")
            }
        }

        stage ('Test') {
            steps {
                sh("./test.sh ${ params.PPM_TEST_TEST } ${JOB_NAME}-${BUILD_ID}")
            }
        }
    }

    post {
        always {
            // Collect logs and such
            archiveArtifacts artifacts: '${PPM_TEST_ARTIFACTS}/*', fingerprint: true

            // Clean up Docker and stack
            sh("docker-compose -p ${JOB_NAME}-${BUILD_ID} down -v --remove-orphans")
            sh("docker-compose -p ${JOB_NAME}-${BUILD_ID} rm -v -f -s")

            // Purge workspace
            deleteDir()
        }
    }
}