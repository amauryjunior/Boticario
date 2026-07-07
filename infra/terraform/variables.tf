variable "project_id" {
  type        = string
  description = "ID do projeto GCP."
}

variable "region" {
  type        = string
  default     = "southamerica-east1"
  description = "Região principal (dados de negócio)."
}

variable "vertex_location" {
  type        = string
  default     = "us-central1"
  description = "Região do Vertex AI/Gemini (valide disponibilidade do modelo)."
}

variable "db_tier" {
  type        = string
  default     = "db-custom-2-7680"
  description = "Tier do Cloud SQL (2 vCPU / 7,5 GB)."
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "Senha do usuário de aplicação do Postgres."
}

variable "jwt_secret" {
  type        = string
  sensitive   = true
  description = "Segredo de assinatura do JWT."
}

variable "api_image" {
  type        = string
  description = "Imagem do serviço de API (Artifact Registry)."
  default     = "us-docker.pkg.dev/cloudrun/container/hello" # placeholder até o 1º build
}

variable "agents_image" {
  type        = string
  description = "Imagem do serviço de agentes."
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "analysis_engine" {
  type        = string
  default     = "adk"
  description = "Motor de análise em produção: adk | heuristic."
}
