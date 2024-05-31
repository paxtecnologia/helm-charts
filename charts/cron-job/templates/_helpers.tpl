{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
labels AppVersion
*/}}
{{- define "labels.AppVersion" -}}
{{- if .Values.app.version -}}
app.kubernetes.io/version: {{ .Values.app.version | quote }}
{{- end -}}
{{- end -}}

{{/*
labels kiali
*/}}
{{- define "labels.kiali" -}}
app: {{ include "common.names.name" . }}
{{- if .Values.app.version }}
version: {{ .Values.app.version | quote }} 
{{- end -}}
{{- end -}}
