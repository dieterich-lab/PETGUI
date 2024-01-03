pipeline {
    agent any
    stages {
        stage('Prepare venv') {
            steps {
                sh '''
                    python3 -m venv venv
                    . ./venv/bin/activate
                    pip3 install pipenv
		            pipenv install .
                '''
            }

        }
        stage('Testing') {
            steps {
                sh '''true
                   . ./venv/bin/activate
                   pipenv shell
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
