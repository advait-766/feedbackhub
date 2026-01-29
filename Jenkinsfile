pipeline {
    agent any

    environment {
        APP_NAME      = "feedbackhub"
        AWS_REGION   = "ap-south-1"

        // ===== AWS / DEPLOY CONFIG =====
        ECR_REGISTRY = "650532568136.dkr.ecr.ap-south-1.amazonaws.com"
        ECR_REPO     = "650532568136.dkr.ecr.ap-south-1.amazonaws.com/feedbackhub"

        EC2_USER = "ec2-user"
        EC2_HOST = "3.110.85.212"
        SSH_KEY  = "/var/lib/jenkins/.ssh/feedback.pem"
    }

    stages {

        stage("Checkout Source") {
            steps {
                git branch: "main",
                    url: "https://github.com/advait-766/feedbackhub.git"
            }
        }

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

        stage("SAST – Semgrep") {
            steps {
                sh '''
                echo "[SEMGREP] Running static analysis..."
                # 1. Run Semgrep using the absolute path to the binary in your venv
		/home/v2077/Desktop/feedbackhub/app/venv/bin/semgrep --config auto --json --output semgrep.json || true
                '''
            }
        }

        stage("Build Docker Image") {
            steps {
                sh '''
                echo "[BUILD] Building Docker image..."
                docker build -t $APP_NAME:latest .
                '''
            }
        }

        stage("Container Scan – Trivy") {
            steps {
                sh '''
                echo "[TRIVY] Scanning container image..."
                trivy image $APP_NAME:latest --format json > trivy.json || true
                '''
            }
        }

        stage("AI Risk Gate") {
    	    steps {
        	sh '''
        	# 1. Define base directory to avoid typing it every time
        	APP_DIR="/home/v2077/Desktop/feedbackhub"
        	PYTHON_BIN="$APP_DIR/venv/bin/python"
        
        	# 2. Enter the directory
        	cd $APP_DIR
        
        	# 3. Clean and Scan (Skip venv to avoid scanning thousands of library files)
        	rm -f trivy.json semgrep.json
        	trivy fs --skip-dirs venv --severity CRITICAL,HIGH --format json --output trivy.json .
        
        	# 4. Extract Features (Using FULL path to the script)
        	echo "[AI] Extracting features..."
        	FEATURES=$($PYTHON_BIN $APP_DIR/ai-risk-engine/extract_features.py)
        	echo "[AI] Features: $FEATURES"
        
        	# 5. Evaluate Risk (Using FULL path to the script)
        	echo "[AI] Evaluating risk..."
        	$PYTHON_BIN $APP_DIR/ai-risk-engine/model_predict.py $FEATURES
        	'''
   	   }
	}

        stage("Login to AWS ECR") {
            steps {
                withCredentials([
                    [$class: 'AmazonWebServicesCredentialsBinding',
                     credentialsId: 'aws-ecr-creds']
                ]) {
                    sh '''
                    echo "[AWS] Logging into ECR..."
                    aws ecr get-login-password --region $AWS_REGION \
                    | docker login --username AWS --password-stdin $ECR_REGISTRY
                    '''
                }
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

        stage("Deploy to EC2") {
            steps {
                sh '''
                echo "[DEPLOY] Deploying to EC2..."
                ssh -i /var/lib/jenkins/.ssh/feedback.pem ec2-user@$EC2_HOST"
    		# Authenticate with ECR (Make sure this line is there!)
    		aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 650532568136.dkr.ecr.ap-south-1.amazonaws.com &&
    		# Pull the NEW image specifically
    		docker pull 650532568136.dkr.ecr.ap-south-1.amazonaws.com/feedbackhub:latest &&
    		docker stop feedbackhub || true &&
    		docker rm feedbackhub || true &&
    		docker run -d --name feedbackhub -p 80:5000 650532568136.dkr.ecr.ap-south-1.amazonaws.com/feedbackhub:latest
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
