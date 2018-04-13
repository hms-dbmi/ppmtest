pipeline {
    agent any
    parameters {
        text(
            defaultValue: '',
            description: 'The tests to run against the stack',
            name: 'PPM_TEST_TEST')
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
                sh("./test.sh { params.PPM_TEST_TEST }")
            }
        }
    }

    post {
        always {
            // Clean up Docker and stack
            sh("docker-compose down -v --remove-orphans")
            sh("docker-compose rm -v -f -s")

            // Purge workspace
            deleteDir()
        }
    }
}