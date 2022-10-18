{{/*
Expand the name of the chart.
*/}}
{{- define "ms-generic.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "ms-generic.fullname" -}}
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
Create chart name and version as used by the chart label.
*/}}
{{- define "ms-generic.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "ms-generic.labels" -}}
helm.sh/chart: {{ include "ms-generic.chart" . }}
{{ include "ms-generic.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ms-generic.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ms-generic.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "ms-generic.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "ms-generic.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}



{{/*
Create ConfigMap injectFile name
*/}}
{{- define "ms-generic.names.injectFile.name" -}}
{{- $configMapName :=  regexReplaceAll "\\W+" .name "-" }}
{{- printf "%s-%s-helm" (include "common.names.fullname" .context) $configMapName -}}
{{- end }}

{{/*
Create secretProviderClass secretName name
*/}}
{{- define "ms-generic.names.secretProviderClass.secretName.name" -}}
{{- printf "%s-secretProvider-%s" (include "common.names.fullname" .context) .provider -}}
{{- end }}


