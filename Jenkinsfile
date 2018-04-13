pipeline {
    agent any
    parameters {
        text(
            defaultValue: 'test.PPMTestCase.test_neer_firefox',
            description: 'The tests to run against the stack',
            name: 'test')
    }

    environment {
        PPM_TEST_STACK = '${ env.JOB_NAME }-${ env.BUILD_ID }'
        PPM_TEST_ARTIFACTS = 'artifacts'
        PPM_TEST_TEST = '${ params.test }'
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
                sh("./test.sh $PPM_TEST_TEST")
            }
        }
    }

    post {
        always {
            // Collect logs and such
            archiveArtifacts artifacts: '${PPM_TEST_ARTIFACTS}/*', fingerprint: true

            // Clean up Docker and stack
            sh("docker-compose -p $PPM_TEST_STACK down -v --remove-orphans")
            sh("docker-compose -p $PPM_TEST_STACK rm -v -f -s")

            // Purge workspace
            deleteDir()
        }
    }
}