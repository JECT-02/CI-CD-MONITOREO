terraform {
  required_version = ">= 1.0"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_image" "app" {
  name = "rollback-exp-app:latest"
  build {
    context = "."
    dockerfile = "Dockerfile"
    tag       = ["rollback-exp-app:latest"]
  }
}

resource "docker_container" "app" {
  name  = var.container_name
  image = docker_image.app.name
  ports {
    internal = 8080
    external = var.host_port
  }
  env = var.container_env
  healthcheck {
    test         = ["CMD", "curl", "-f", "http://localhost:8080/health"]
    interval     = "5s"
    timeout      = "2s"
    retries      = 3
    start_period = "5s"
  }
}
