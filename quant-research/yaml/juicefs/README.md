# fluid-eks-juicefs
The objective of this repo is to test the performance and scalability of fluid with JuiceFS runtime on amazon eks

## 1.amazon eks cluster provision

- pre-requisite
  - provision an ec2
  - install eksctl on the ec2
    ```sh
    curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
    sudo mv -v /tmp/eksctl /usr/local/bin
    eksctl version
    ```
  - install kubectl on the ec2
    ```sh
    aws sts get-caller-identity
    curl --silent --location -o /usr/local/bin/kubectl \
    https://s3.us-west-2.amazonaws.com/amazon-eks/1.31.3/2024-12-12/bin/linux/amd64/kubectl
    chmod +x /usr/local/bin/kubectl
    kubectl version --client
    ```
- provision eks cluster
  ```sh
  eksctl create cluster -f f6.yaml

  #wait till the cluster been provisioned, takes around 15 minutes

  aws eks update-kubeconfig --region us-west-2 --name f6
  ```
## 2. fluid-csi plugins docker image customization
- fluid-csi plugins docker file customization and docker image generation
  dockfile.csi could be acquired per link.
  ```sh
  docker build -f dockerfile.csi . #注意要运行这个命令的前提是docker app需要运行起来
  ```
  到docker app中找到生成的image记录，拿到tag的value
- pull the image to ECR
  ```sh
  docker images

  docker tag 41531aa365b3 135709585800.dkr.ecr.us-west-2.amazonaws.com/fluid/csiplugins:latest

  aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 135709585800.dkr.ecr.us-west-2.amazonaws.com/fluid/csiplugins

  docker push 135709585800.dkr.ecr.us-west-2.amazonaws.com/fluid/csiplugins:latest
  ```

## 3.fluid installation

-  install helm
   ```sh
   curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
   chmod 700 get_helm.sh
   ./get_helm.sh
   ```
-  install fluid
   ```sh
   helm repo add fluid https://fluid-cloudnative.github.io/charts

   helm repo update

   helm upgrade --install fluid fluid/fluid -n fluid-system \
       --set csi.kubelet.kubeConfigFile="/var/lib/kubelet/kubeconfig" \
       --set csi.kubelet.certDir="/etc/  kubernetes/pki" \
       --set csi.plugins.imageName="csiplugins" \
       --set csi.plugins.imagePrefix="135709585800.dkr.ecr.us-west-2.amazonaws.com/fluid" \
       --set csi.plugins.imageTag="latest"
   ```

- check fluid has been successfully installed
  ```sh
  kubectl get pod -n=fluid-system #all pods shoud be running
  ```

## 4.fluid juicefsruntime to cache data from s3 bucket
- create secret juicefs-secret
  ```sh
  # Edit jfs-secret.yaml to configure your JuiceFS settings:
  # - name: JuiceFS filesystem name
  # - metaurl: Redis connection string for metadata storage
  # - storage: Storage type (s3)
  # - bucket: S3 bucket URL
  # - access-key: AWS access key
  # - secret-key: AWS secret key
  kubectl apply -f jfs-secret.yaml -n fluid-system
  ```
- create dataset, juicefsruntime pod. pvc will be auto-created. 
  ```sh
  kubectl apply -f jfs-dataset.yaml -n fluid-system
  kubectl apply -f jfs-runtime.yaml -n fluid-system
  ```
- check the status of the above
  ```sh
  # Check secret status
  kubectl get secret juicefs-secret -n fluid-system

  # Check Dataset status
  kubectl get dataset jfs-dataset -n fluid-system
  
  # Check JuiceFSRuntime status
  kubectl get juicefsruntime jfs-dataset -n fluid-system
  
  # Check PVC status
  kubectl get pvc jfs-dataset -n fluid-system
  ```

## 5.create an app to read data from fluid juicefsruntime data cache
- make sure that the plugins container of the csi-nodeplugin-fluid pod has aws-cli installed
  ```sh
  kubectl exec -it csi-nodeplugin-fluid-xxxxx -c plugins -n fluid-system -- /bin/sh
  apk add --no-cache aws-cli
  aws --version
  ```
- create jfs-reader-pod
  ```sh
  #run the pod
  kubectl apply -f jfs-reader-pod.yaml -n fluid-system
  
  #check the status of the pod
  kubectl describe pod jfs-reader-pod -n fluid-system
  ```

## 6.delete resources
```sh
#delete the app pod
kubectl delete pod jfs-reader-pod -n fluid-system

# Delete PVC first
kubectl delete pvc jfs-dataset -n fluid-system

# Delete JuiceFSRuntime if it exists
kubectl delete juicefsruntime jfs-dataset -n fluid-system

# Delete Dataset
kubectl delete dataset jfs-dataset -n fluid-system

# Delete Secret
kubectl delete secret juicefs-secret -n fluid-system
```


