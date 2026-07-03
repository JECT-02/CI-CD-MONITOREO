variable "container_name" {
  description = "Nombre del contenedor para identificar la corrida"
  type        = string
  default     = "rollback-exp-estable"
}

variable "host_port" {
  description = "Puerto en el host para mapear al puerto 8080 del contenedor"
  type        = number
  default     = 8080
}

variable "container_env" {
  description = "Variables de entorno para el contenedor (lista de strings 'KEY=value')"
  type        = list(string)
  default     = []
}
