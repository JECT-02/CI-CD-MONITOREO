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
  name = "rollback-exp-f2-puerto:latest"
  build {
    context    = "."
    dockerfile = "Dockerfile"
    tag        = ["rollback-exp-f2-puerto:latest"]
  }
}

resource "docker_container" "app" {
  name  = "rollback-exp-f2-puerto"
  image = docker_image.app.name
  ports {
    internal = 8081
    external = 8081
  }
  env = []
}
