pipeline {
    agent any
    stages {
        stage('Prepare venv') {
            steps {
                sh '''
                    pip3 install pipenv
		            pipenv install
                '''
            }

        }
        stage('Testing') {
            steps {
                sh '''true
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
