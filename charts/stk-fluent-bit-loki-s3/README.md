




### S3 Buckets
O Loki precisa de 2 buckets: chunks e ruler

```shell
aws s3api create-bucket --bucket  <YOUR CHUNK BUCKET NAME e.g. `loki-aws-dev-chunks`> --region <S3 region your account is on, e.g. `eu-west-2`> --create-bucket-configuration LocationConstraint=<S3 region your account is on, e.g. `eu-west-2`> \
aws s3api create-bucket --bucket  <YOUR RULER BUCKET NAME e.g. `loki-aws-dev-ruler`> --region <S3 REGION your account is on, e.g. `eu-west-2`> --create-bucket-configuration LocationConstraint=<S3 REGION your account is on, e.g. `eu-west-2`>
```

```yaml
loki:
  loki:
    storage_config:
      aws:
        region: <S3 BUCKET REGION> # for example, eu-west-2
        bucketnames: <CHUNK BUCKET NAME> # Your actual S3 bucket name, for example, loki-aws-dev-chunks
  ruler:
    enable_api: true
    storage:
      type: s3
      s3:
        region: <S3 BUCKET REGION> # for example, eu-west-2
        bucketnames: <RULER BUCKET NAME> # Your actual S3 bucket name, for example, loki-aws-dev-ruler
  storage:
    bucketNames:
      chunks: "<CHUNK BUCKET NAME>" # Your actual S3 bucket name (loki-aws-dev-chunks)
      ruler: "<RULER BUCKET NAME>" # Your actual S3 bucket name (loki-aws-dev-ruler)
    s3:
      region: <S3 BUCKET REGION> # for example, eu-west-2
```

### IAM Policy e Role

Criar uma policy: LokiS3AccessPolicy

Incluir essas permissões: 
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "LokiStorage",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::< CHUNK BUCKET NAME >",
                "arn:aws:s3:::< CHUNK BUCKET NAME >/*",
                "arn:aws:s3:::< RULER BUCKET NAME >",
                "arn:aws:s3:::< RULER BUCKET NAME >/*"
            ]
        }
    ]
}
```

Loki precisa de uma IAM role: LokiServiceAccountRole

Incluir essa configuração:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::< ACCOUNT ID >:oidc-provider/oidc.eks.<INSERT REGION>.amazonaws.com/id/< OIDC ID >"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "oidc.eks.<INSERT REGION>.amazonaws.com/id/< OIDC ID >:sub": "system:serviceaccount:loki:loki",
                    "oidc.eks.<INSERT REGION>.amazonaws.com/id/< OIDC ID >:aud": "sts.amazonaws.com"
                }
            }
        }
    ]
}
```

Vinclular no EKS serviceAccount
```yaml
 serviceAccount:
    create: true
    annotations:
      "eks.amazonaws.com/role-arn": "arn:aws:iam::<Account ID>:role/LokiServiceAccountRole"
```
