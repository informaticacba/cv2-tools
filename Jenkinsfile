pipeline {
    environment {
        // This registry is important for removing the image after the tests
        registry = "fernaperg/cv2tools"
    }
    agent any
    stages {
        stage("Test") {
            steps {
                script {
                    // Building the Docker image
                    dockerImage = docker.build registry + ":$BUILD_NUMBER"

                    try {
                        dockerImage.inside() {
                            // Extracting the PROJECTDIR environment variable from inside the container
                            def PROJECTDIR = sh(script: 'echo \$PROJECTDIR', returnStdout: true).trim()

                            // Copying the project into our workspace
                            echo "PROJECTDIR directory is $PROJECTDIR"
                            echo "WORKSPACE directory is $WORKSPACE"
                            echo "Test folder: $WORKSPACE$PROJECTDIR/test"
                            echo "cp -r '$PROJECTDIR/test' '$WORKSPACE'"
                            sh "cp -r '$PROJECTDIR/test' '$WORKSPACE'"

                            // Running the tests inside the new directory
                            dir("$WORKSPACE/test") {
                                sh "python -m unittest"
                            }
                        }

                    } finally {
                        // Removing the docker image
                        sh "docker rmi $registry:$BUILD_NUMBER"
                    }
                }
            }
        }
    }
}