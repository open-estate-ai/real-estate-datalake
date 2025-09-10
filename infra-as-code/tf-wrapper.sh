#!/bin/bash
# this is a wrapper command for the terraform with predefined commands.

# example command
# ./tf-wrapper.sh dev sample-scraper-lambda init
# ./tf-wrapper.sh dev sample-scraper-lambda plan
# ./tf-wrapper.sh dev sample-scraper-lambda apply

# Pre-requisites
# ??

# optional
# export TF_LOG=warn

export env=$1
export component=$2
action=$3
src_dir=./tf-real-estate-datalake

if [[ -z ${env} ]]; then
    echo env not defined
    exit 2
fi

if [[ -z ${src_dir} ]]; then
    echo service not defined
    exit 2
fi

# Remove temp dir
rm -r "${src_dir}/../temp" 2>/dev/null

case $action in
    init)
    rm -rf "${src_dir}"/.terraform*
    # terraform -chdir="${src_dir}" "${action}" -upgrade=true -reconfigure -compact-warnings -backend-config="../tf-vars/${env}/${component}/backend.tf"
    terraform -chdir="${src_dir}" "${action}" -upgrade=true -reconfigure -compact-warnings -backend-config="path=../tf-vars/${env}/${component}/terraform.tfstate"
    ;;
    apply)
    terraform -chdir="${src_dir}" "${action}" -auto-approve --var-file="../tf-vars/${env}/${component}/param-component.tfvars" --var-file="../tf-vars/${env}/params-env.tfvars" ${4} ${5}
    ;;
    plan|destroy)
    terraform -chdir="${src_dir}" "${action}" --var-file="../tf-vars/${env}/${component}/param-component.tfvars" --var-file="../tf-vars/${env}/params-env.tfvars" ${4}
    ;;
    force-unlock)
    terraform -chdir="${src_dir}" "${action}" ${4}
    ;;
    output)
    terraform -chdir="${src_dir}" "${action}" -raw ${4}
    ;;
    import)
    terraform -chdir="${src_dir}" "${action}" --var-file="../tf-vars/${env}/${component}/param-component.tfvars" --var-file="../tf-vars/${env}/params-env.tfvars" -generate-config-out="./tf-import-configs/generated.tf"
    ;;
    *)

    echo "action should be any one of the below" >&2
    echo "init, plan, apply, destroy, force-unlock, output, import" >&2
    exit 1
    ;;
esac
