# CONTRACT.yaml 服务片段

# 服务定义
provides:
  - id: "{{service_id_1}}"
    name: "{{service_name_1}}"
    description: "{{service_desc_1}}"
    endpoint: "inbox"
    format: "json"
    schema:
      type: object
      properties: {}

  - id: "{{service_id_2}}"
    name: "{{service_name_2}}"
    description: "{{service_desc_2}}"
    endpoint: "inbox"
    format: "json"

consumes:
  - service: "{{consumed_service_1}}"
    provider: "{{provider_1}}"
    purpose: "{{purpose_1}}"

  - service: "{{consumed_service_2}}"
    provider: "{{provider_2}}"
    purpose: "{{purpose_2}}"

# 通信协议
interaction_protocols:
  request:
    format: intent-based
    description: "接收基于意图的请求，通过 inbox 处理"
  response:
    format: structured
    description: "返回结构化的执行结果"