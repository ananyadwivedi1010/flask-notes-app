variable "aws_region" {
  default = "eu-north-1"
}

variable "instance_type" {
  default = "t3.micro"
}

variable "key_name" {
  description = "notes-app-key"
  type        = string
  default     = "notesapp-key"
}