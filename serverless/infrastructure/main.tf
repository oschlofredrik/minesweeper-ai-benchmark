terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "tilts-terraform-state"
    key    = "serverless/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  default     = "production"
}

variable "project_name" {
  description = "Project name"
  default     = "tilts"
}

# DynamoDB Tables
resource "aws_dynamodb_table" "games" {
  name         = "${var.project_name}-${var.environment}-games"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  
  attribute {
    name = "id"
    type = "S"
  }
  
  attribute {
    name = "model_name"
    type = "S"
  }
  
  attribute {
    name = "created_at"
    type = "S"
  }
  
  global_secondary_index {
    name            = "model-created-index"
    hash_key        = "model_name"
    range_key       = "created_at"
    projection_type = "ALL"
  }
  
  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_dynamodb_table" "leaderboard" {
  name         = "${var.project_name}-${var.environment}-leaderboard"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "model_name"
  
  attribute {
    name = "model_name"
    type = "S"
  }
  
  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# S3 Bucket for game data
resource "aws_s3_bucket" "data" {
  bucket = "${var.project_name}-data-${var.environment}"
  
  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data_lifecycle" {
  bucket = aws_s3_bucket.data.id
  
  rule {
    id     = "archive-old-games"
    status = "Enabled"
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}

resource "aws_s3_bucket_versioning" "data_versioning" {
  bucket = aws_s3_bucket.data.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# SQS Queue for evaluations
resource "aws_sqs_queue" "evaluation" {
  name                      = "${var.project_name}-evaluation-${var.environment}"
  visibility_timeout_seconds = 960  # 16 minutes
  message_retention_seconds = 86400  # 24 hours
  
  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-lambda-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy-${var.environment}"
  role = aws_iam_role.lambda_execution.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:*"
        ]
        Resource = [
          aws_dynamodb_table.games.arn,
          "${aws_dynamodb_table.games.arn}/*",
          aws_dynamodb_table.leaderboard.arn,
          "${aws_dynamodb_table.leaderboard.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.data.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.evaluation.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Outputs
output "dynamodb_games_table" {
  value = aws_dynamodb_table.games.name
}

output "dynamodb_leaderboard_table" {
  value = aws_dynamodb_table.leaderboard.name
}

output "s3_bucket_name" {
  value = aws_s3_bucket.data.id
}

output "sqs_queue_url" {
  value = aws_sqs_queue.evaluation.url
}

output "lambda_role_arn" {
  value = aws_iam_role.lambda_execution.arn
}