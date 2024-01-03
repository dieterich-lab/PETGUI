pipeline {
    agent any
    stages {
        stage('Prepare venv') {
            steps {
                sh '''
                    python3 -m venv venv
                    . ./venv/bin/activate
                    sudo apt-get install sshpass
		            pipenv install
                '''
            }

        }
        stage('Testing') {
            steps {
                sh '''true
                   . ./venv/bin/activate
                   export PYTHONPATH=$(pwd)
                   pytest --junitxml results.xml tests
                '''
            }
        }
    }
    post {
        always {
            junit 'results.xml'

        }
    }
}
