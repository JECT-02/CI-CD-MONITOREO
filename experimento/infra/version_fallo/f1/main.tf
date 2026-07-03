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
  name = "rollback-exp-f1-sintaxis:latest"
  build {
    context    = "."
    dockerfile = "Dockerfile"
    tag        = ["rollback-exp-f1-sintaxis:latest"]
  }
}

resource "docker_container" "app" {
  name  = "rollback-exp-f1-sintaxis"
  image = docker_image.app.name
  ports {
    internal = 8080
    external = 8080
  }
  env = []
}
