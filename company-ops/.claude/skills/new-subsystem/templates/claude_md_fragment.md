# CLAUDE.md Agent 团队片段

## Agent 团队配置

本子系统根据任务类型动态组建 Agent 协作团队：

| 角色 | 职责 | 技能 | 触发条件 |
|------|------|------|----------|
| {{role_1}} | {{role_1_desc}} | {{role_1_skills}} | {{role_1_trigger}} |
| {{role_2}} | {{role_2_desc}} | {{role_2_skills}} | {{role_2_trigger}} |
| {{role_3}} | {{role_3_desc}} | {{role_3_skills}} | {{role_3_trigger}} |

### 团队协作示例

```
任务: {{example_task}}
├── {{role_a}} (主导) - {{role_a_action}}
├── {{role_b}} - {{role_b_action}}
└── {{role_c}} - {{role_c_action}}
```

---

## 决策权限

| 决策类型 | 权限级别 | 金额限制 | 说明 |
|----------|----------|----------|------|
| {{decision_1}} | {{auth_1}} | {{limit_1}} | {{note_1}} |
| {{decision_2}} | {{auth_2}} | {{limit_2}} | {{note_2}} |
| {{decision_3}} | {{auth_3}} | {{limit_3}} | {{note_3}} |

### 权限标识

| 标识 | 含义 |
|------|------|
| ✅ 自主 | 可自行决定，无需人工确认 |
| ⚠️ 确认 | 需要人工确认后才能执行 |
| ❌ 禁止 | 不能自行决定，必须人工审批 |