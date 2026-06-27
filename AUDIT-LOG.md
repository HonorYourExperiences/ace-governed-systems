# Audit Log

**Purpose:** Running record of all significant actions processed by the runtime monitor. Each entry is automatically appended by the `audit-processor` workflow when an issue labeled `audit` is opened or labeled.

**Format per entry:**
```
## Audit: <title>
- **Issue:** #<number>
- **Action:** <action_type>
- **Allowed:** true | false
- **Reason:** <reason>
- **Source:** <source>
- **Timestamp:** <ISO 8601>
```

---

*(No audit events yet — entries will appear here automatically when audit-labeled issues are filed.)*
