# IaC (Terraform)

Simple Terraform setup for the data lake components.

## Folder Setup
Create variable folders like:
```
tf-vars/
  dev/
    <component-name>/
      param-component.tfvars
    params-env.tfvars
```
Copy an existing sample and adjust values.

## State (Temporary)
Terraform state is stored locally for now. We will move to an S3/Dynamo backend later once cost and security are settled.

## Prerequisites
- Terraform installed (check with: `terraform version`)
- export AWS_PROFILE to the AWS Profile
- AWS credentials configured (`aws sts get-caller-identity` should work)
- Proper IAM permissions to create required resources

## Basic Commands

```sh
./tf-wrapper.sh dev <component-name> init
./tf-wrapper.sh dev <component-name> plan
./tf-wrapper.sh dev <component-name> apply
./tf-wrapper.sh dev <component-name> destroy
```

### What Each Command Does
- init: Prepares `.terraform` directory and providers
- plan: Shows what will be created/changed
- apply: Applies the plan (auto-approve in wrapper)
- destroy: Removes the component’s resources

## Example
```sh
./tf-wrapper.sh dev datalake init
./tf-wrapper.sh dev datalake plan
./tf-wrapper.sh dev datalake apply
```

## Tips
- Edit `params-env.tfvars` for shared env values
- Edit `<component>/param-component.tfvars` for component-specific settings
- Re-run `plan` after changes to confirm impact
- Commit only `.tf` and `.tfvars` you intend to share (never credentials)

## Cleanup
```sh
./tf-wrapper.sh dev datalake destroy
```

More components can be added the same way. Open an issue if something feels unclear.