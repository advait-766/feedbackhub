pipeline {
    agent any

    environment {
        APP_NAME   = "feedbackhub"
        AWS_REGION = "ap-south-1"

        // ===== AWS / DEPLOY CONFIG =====
        ECR_REPO = "650532568136.dkr.ecr.ap-south-1.amazonaws.com/feedbackhub"
        EC2_USER = "feed"
        EC2_HOST = "13.204.79.240"
        SSH_KEY  = "feedback.pem"
    }

    stages {

        /* ============================
           SOURCE
        ============================ */
        stage("Checkout Source") {
            steps {
                git branch: "main",
                    url: "https://github.com/advait-766/feedbackhub.git"
            }
        }

        /* ============================
           SECRETS SCAN
        ============================ */
        stage("Secrets Scan – Gitleaks") {
            steps {
                sh '''
                echo "[GITLEAKS] Scanning for secrets..."
                gitleaks detect \
                  --source . \
                  --report-format json \
                  --report-path gitleaks.json || true
                '''
            }
        }

        /* ============================
           STATIC ANALYSIS
        ============================ */
        stage("SAST – Semgrep") {
            steps {
                sh '''
                echo "[SEMGREP] Running static analysis..."
                semgrep --config auto --json > semgrep.json || true
                '''
            }
        }

        /* ============================
           BUILD
        ============================ */
        stage("Build Docker Image") {
            steps {
                sh '''
                echo "[BUILD] Building Docker image..."
                docker build -t $APP_NAME:latest .
                '''
            }
        }

        /* ============================
           CONTAINER SECURITY
        ============================ */
        stage("Container Scan – Trivy") {
            steps {
                sh '''
                echo "[TRIVY] Scanning container image..."
                trivy image $APP_NAME:latest --format json > trivy.json || true
                '''
            }
        }

        /* ============================
           AI SECURITY GATE
        ============================ */
        stage("AI Risk Gate") {
            steps {
                sh '''
                echo "[AI] Extracting features..."
                FEATURES=$(/var/lib/jenkins/venvs/ai-env/bin/python ai-risk-engine/extract_features.py)
		echo "[AI] Features: $FEATURES"
                /var/lib/jenkins/venvs/ai-env/bin/python ai-risk-engine/model_predict.py $FEATURES
                '''
            }
        }

        /* ============================
           PUSH TO AWS ECR
        ============================ */
        stage("Login to AWS ECR") {
            steps {
                sh '''
                echo "[AWS] Logging into ECR..."
                aws ecr get-login-password --region $AWS_REGION \
                | docker login --username AWS --password-stdin $ECR_REPO
                '''
            }
        }

        stage("Push Image to ECR") {
            steps {
                sh '''
                echo "[AWS] Pushing image to ECR..."
                docker tag $APP_NAME:latest $ECR_REPO:latest
                docker push $ECR_REPO:latest
                '''
            }
        }

        /* ============================
           DEPLOY TO EC2
        ============================ */
        stage("Deploy to EC2") {
            steps {
                sh '''
                echo "[DEPLOY] Deploying to EC2..."
                ssh -o StrictHostKeyChecking=no -i $SSH_KEY $EC2_USER@$EC2_HOST "
                    docker pull $ECR_REPO:latest &&
                    docker stop feedbackhub || true &&
                    docker rm feedbackhub || true &&
                    docker run -d \
                      --name feedbackhub \
                      -p 80:5000 \
                      $ECR_REPO:latest
                "
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline completed successfully — AI approved deployment."
        }
        failure {
            echo "❌ Pipeline stopped — security risk detected or deployment failed."
        }
    }
}
