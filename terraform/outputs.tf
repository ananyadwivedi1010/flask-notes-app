output "instance_public_ip" {
  value = aws_instance.notes_app_server.public_ip
}