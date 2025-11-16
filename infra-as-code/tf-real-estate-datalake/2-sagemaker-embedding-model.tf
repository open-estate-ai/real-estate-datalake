module "sagemaker_embedding_model" {
  source = "../tf-modules/sagemaker"
  # common vars
  region         = var.resource_region
  env            = var.env
  component_name = var.component_name

  # module specific vars
  sagemaker_image_uri  = "763104351884.dkr.ecr.us-east-1.amazonaws.com/huggingface-pytorch-inference:1.13.1-transformers4.26.0-cpu-py39-ubuntu20.04"
  embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"
}
