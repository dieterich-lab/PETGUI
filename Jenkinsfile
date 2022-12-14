pipeline {
    agent any
    stages {
        stage('Prepare venv') {
            steps {
                sh '''
                    python3 -m venv venv
                    . ./venv/bin/activate
                    pip install -r requirements_dev.txt
                '''
            }

        }
        stage('Linting') {
            steps {
                sh '''
                    . ./venv/bin/activate
                    flake8 hello.py --max-line-length 140

                '''
            }
        }
        stage('Testing') {
            steps {
                sh '''true
                #    . ./venv/bin/activate
                #    export PYTHONPATH=$(pwd)
                #    pytest --junitxml results.xml tests
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
