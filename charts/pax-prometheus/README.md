## Como testar para desenvolver

```shell
helm template -n batata --values ./values.yaml $(find .dev -type f | sed 's/^/--values /' | tr '\n' ' ') default .
```