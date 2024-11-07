# k8s-cfg-base

Versão 1.0.0 é incompativel com as anteriores

## Como testar para desenvolver

```shell
helm template -n batata --values ./values.yaml $(find .dev -type f | sed 's/^/--values /' | tr '\n' ' ') default .
```