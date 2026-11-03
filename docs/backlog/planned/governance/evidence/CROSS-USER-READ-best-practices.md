# Cross-user READ in a per-user-isolated gateway: comparative analysis

Governance backlog evidence, 2026-10-15. Question (operator): planes are off-limits for WRITE; is a hard read deny optimal when we want studies across users, resource-usage search, or aggregated stats?

## 1. How established systems do it

| System | Isolation unit | Cross-tenant READ: who, how | Safeguards | Lesson |
|---|---|---|---|---|
| **Kubernetes** [1][2][3][4] | Namespace: a workload "only has access to its own resources, such as ConfigMaps and Secrets" [2]; "The Pod and the ConfigMap must be in the same namespace" [4]. | API only: a ClusterRole lets a user "run `kubectl get pods --all-namespaces`"; `view` is "read-only access to see most objects" but "does not allow viewing Secrets" (privilege escalation) [1]. | "Permissions are purely additive" [1]; audit records who, what, when at the API server [3]. | Cross-namespace read is a principal's binding, never a pod reading another namespace; read-only still excludes credentials. |
| **AWS** [5]-[11] | Account/OU. | `SecurityAudit`: "read security configuration metadata" [5]; `ViewOnlyAccess`: "view resources and basic metadata" [6]; neither reads object contents. Org trail "logs all events for all AWS accounts"; members cannot delete it [7]. CloudTrail Lake: SQL across "multiple Regions and accounts" [8]. Lake Formation column/row/cell filters "apply only to read operations" [10]. | `ExternalId` [9] against the confused deputy, "an entity that doesn't have permission... can coerce a more-privileged entity" [11]. | Metadata-read and content-read are different roles; analytics runs on a copied, filtered store. |
| **GitLab / GitHub** [12]-[16] | Project/org. | GitLab auditor: "read-only access to all groups, projects, and other resources" [12]. GitHub security manager: "Read access on all repositories in the organization" [13]; enterprise audit streaming covers "all of the organizations in your enterprise" [14]. | Job token "valid only while the job is running", "same access level as the user that triggered the pipeline", other projects only via allowlist [15]; `GITHUB_TOKEN` "limited to the repository that contains your workflow" [16]. | A named read-only role for people; jobs never inherit it. |
| **Postgres RLS** [17] | Row. | Policies "restrict, on a per-user basis, which rows can be returned" and can be "specific to commands, or to roles": a reporting role gets its own policy. | "default-deny policy... no rows are visible". | Cross-tenant read = a distinct role with an explicit policy on the same store. |
| **HIPAA** [18][19][20] | Patient record. | Research under IRB waiver: "no more than a minimal risk", "adequate plan to protect the identifiers", "will not be reused or disclosed" [20]. | "limit protected health information to the minimum necessary" [18]; name "persons or classes of persons... who need access" and "the category or categories... to which access is needed" [19]. | Role x data category x condition, plus a protocol for identifiers. |
| **GDPR** [21][22] | Data subject. | Research/statistics "shall, in accordance with Article 89(1), not be considered to be incompatible with the initial purposes" [21]. | "limited to what is necessary" [21]; "pseudonymisation provided that those purposes can be fulfilled in that manner" [22]. | Studies are lawful, purpose-bound, minimised. |
| **Aggregation / DP** [23]-[26] | One user's contribution. | Google DP: "(ε, δ)-differentially private (DP) statistics" with "some bound on maximum number of contributions each user can make" [23]; Apple: data "randomized before being sent from the device" [24]. GA thresholds "prevent anyone viewing a report... from inferring the identity" [25]; Viva "minimum aggregation threshold", "at least five" [26]. | Opt-out from row-level outputs [26]. | Aggregates need a k-threshold; row-level needs opt-in. |
| **Break-glass** [27][28][29] | Customer content. | Access Transparency logs "the actions that Google personnel take when accessing Customer Data" with "the reason for the action" [27]; Access Approval: "Access is granted only after the Access Approval request is approved" [28]. Azure Lockbox: JIT, "access for the duration specified", "logged in Customer Lockbox request logs" [29]. | Justification + approval + time-bound + audit. | Privileged content read = reason + expiry + log, even for the operator. |
| **Observability** [30]-[34] | Tenant label. | Mimir federation is opt-in (`-tenant-federation.enabled`, `tenant-1|tenant-2` in `X-Scope-OrgID`) [30]; results carry `__tenant_id__` [31]. Loki: "data for tenant A are isolated from tenant B"; "Only query endpoints support multi-tenant calls" [32]. OTel `headers_setter` sets `X-Scope-OrgID` [33]. Grafana orgs isolate dashboards and data sources; Viewer role [34]. | Auth proxy sets the tenant; federation off by default. | Cross-tenant read is a query-time flag with per-tenant labels; never cross-tenant write. |
| **Datadog** [35][36][37] | Organization. | Child orgs "do not have access to each other's data" [35]; "A source organization exposes data to a destination organization through an organization connection" [36]; "queried at render time, not copied"; "Data access controls within the source org still apply" [37]. | "Org Connection Write permission" [36]. | Per-source consent; "Query performance may differ... for large aggregations across many orgs" [37]. |
| **Vault** [38][39][40] | Namespace, "a mini-Vault instance" [38]. | Only explicit `read`/`list` on a path; "Policies are deny by default"; `deny` "always takes precedence" [39]. | Audit devices "record all API requests and responses"; if none can log, "Vault refuses to service the corresponding API request" [40]. | No "everything readable" role; an unlogged read must fail. |
| **AI agents** [41]-[50] | The principal's scope. | MCP: servers "MUST NOT accept any tokens that were not explicitly issued for the MCP server"; start from "low-risk discovery/read operations" [41]. OWASP LLM06: actions "executed on downstream systems in the context of that specific user"; "Implement authorization in downstream systems rather than relying on an LLM" [42]; LLM01 [43]. Lethal trifecta: private data + untrusted content + external communication, "an attacker can easily trick it" [44]. ADK: "agents only perform actions that the user could have performed themselves" [45]. LangGraph memory namespaces are keyed by user IDs [46]. | Anthropic sandbox: "read and write access to the current working directory, but blocking... outside of it"; "effective sandboxing requires both filesystem and network isolation" [47]; Claude Code prompt-free reads only "within the working directory and additional directories" [48]; Codex: "write permissions limited to the active workspace", "network access turned off" [49]. | Every vendor fences a run to its principal's directory; wider reads are the human's grant, not the run's (confused deputy [50][11]). |

Pattern: nobody loosens the data plane; "no implicit trust" comes from "location" [51]. All of them name a read-only principal role, serve cross-tenant reads through the API layer with a tenant label, scope jobs and runs to one principal, audit privileged reads with a reason (time-bound approval for content), and release statistics only above a threshold or with noise.

## 2. Re-assessment for AbstractGateway

The two halves do not conflict: the run's hard deny and the principal's cross-user read live in different layers.

**(a) Keep the hard DENY for run tools (files, shell, workspace) on other planes, `auth/` and the audit log, read and write, whatever posture or the admin switch says.** A run is the lethal trifecta by construction: private data, untrusted content (web, files, another user's output) and a way out [44]. A run acting for Alice that can `cat` Bob's plane is the confused deputy [50][11]: Bob's data leaves under Alice's authority after one injected line, and no per-lane check turns red. Vendors fence runs to their principal's directory [47][48][49], pods to their namespace [2][4], CI jobs to their project [15][16]. No study needs the run to read raw planes.

**(b) Cross-user READ is a PRINCIPAL privilege, exercised through gateway APIs, never through the data plane.**
- One explicit role, `auditor`, grantable per tenant by an admin to humans and digital users, modelled on GitLab's auditor and `view` [12][1]: read-only, never credentials. Split as AWS does [5][6]: `auditor:metadata` (ledgers: workflow, tools, model, tokens, duration, status) and `auditor:content` (transcripts, artifacts). `analyst` sees aggregates only.
- Endpoints with `tenant` + `users[]` filters, every row labelled `user_id` (Mimir's `__tenant_id__` [31]): `GET /study/runs` (metadata), `GET /study/search?resource=` (which runs used a tool, model, skill, file), `GET /study/aggregate` (counts, sums, percentiles per workflow/model/day).
- Content reads of another plane take the break-glass shape: `purpose` is required; the audit log records actor, target plane, purpose, response hash; if the audit append fails, the read fails [40]. Optional per-user `study_opt_in` [26] and time-boxed grants [29].
- Aggregates: system-defined k-threshold (default 5 [26]) below which a cell is withheld; per-user contribution bounding; DP noise [23] only if stats leave the tenant.
- A study is an artifact: `POST /study/export` writes the result into the requester's plane with a ledger entry (query, filters, purpose, row count); data is read at query time, never copied as raw planes [37]; the export is pseudonymised by default [22].
- A run may call these endpoints as a tool only if its principal holds the role and its authorization object (1023) lists the tool; rows, never paths; the file deny stays.

**(c) Defaults.** Admins: `auditor:metadata` on their tenant's planes (1020's "read-only outside own runtime"); `auditor:content` only with purpose + audit; never credentials; never a run on another plane. Digital users: no cross-plane role; their creator may grant `analyst` or a tenant-bounded `auditor`; their runs get the tool only through their own authorization object. Users: nothing cross-plane; k-anonymous aggregates include everyone (statistics are a compatible purpose [21]); content reads are opt-in.

**(d) "Nothing is deleted, history stays accessible"**: an archived plane is a read-only mount reachable through the same study endpoints with `state=archived`, under the same role/purpose/audit rules; archiving never widens access. The audit log is append-only, readable only via `GET /audit` by `auditor` (members see but cannot delete the org trail [7]); retention is a tenant setting with a long default (CloudTrail Lake: up to 10 years [8]).

**Trade-offs.** Performance: cross-plane queries scan many ledgers; index metadata into a gateway-home catalog labelled by `user_id`, keep content reads lazy [37]. Privacy: metadata already reveals behaviour (what Bob asked, when), hence thresholds, purpose, audit, opt-in. Consent: a cross-user study is research, lawful under Art. 5(1)(b)/89 and HIPAA's waiver logic only with minimisation, pseudonymisation and a recorded protocol [20][21][22]; store the purpose beside the export. Complexity: one role, five endpoints, one catalog, against the alternative every reference system rejects: runs reading planes.

## References

1. Kubernetes RBAC: https://kubernetes.io/docs/reference/access-authn-authz/rbac/
2. Kubernetes multi-tenancy: https://kubernetes.io/docs/concepts/security/multi-tenancy/
3. Kubernetes auditing: https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/
4. Kubernetes ConfigMap: https://kubernetes.io/docs/concepts/configuration/configmap/
5. AWS SecurityAudit: https://docs.aws.amazon.com/aws-managed-policy/latest/reference/SecurityAudit.html
6. AWS ViewOnlyAccess: https://docs.aws.amazon.com/aws-managed-policy/latest/reference/ViewOnlyAccess.html
7. CloudTrail organization trail: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html
8. CloudTrail Lake: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake.html
9. AWS delegated administrator: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_delegate_policies.html
10. Lake Formation filters: https://docs.aws.amazon.com/lake-formation/latest/dg/data-filtering.html
11. AWS confused deputy: https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html
12. GitLab auditor users: https://docs.gitlab.com/administration/auditor_users/
13. GitHub security managers: https://docs.github.com/en/organizations/managing-peoples-access-to-your-organization-with-roles/managing-security-managers-in-your-organization
14. GitHub audit streaming: https://docs.github.com/en/enterprise-cloud@latest/admin/monitoring-activity-in-your-enterprise/reviewing-audit-logs-for-your-enterprise/streaming-the-audit-log-for-your-enterprise
15. GitLab job token: https://docs.gitlab.com/ci/jobs/ci_job_token/
16. GITHUB_TOKEN: https://docs.github.com/en/actions/concepts/security/github_token
17. PostgreSQL row security: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
18. 45 CFR 164.502(b): https://www.law.cornell.edu/cfr/text/45/164.502
19. 45 CFR 164.514: https://www.law.cornell.edu/cfr/text/45/164.514
20. 45 CFR 164.512(i): https://www.law.cornell.edu/cfr/text/45/164.512
21. GDPR Art. 5: https://gdpr-info.eu/art-5-gdpr/
22. GDPR Art. 89: https://gdpr-info.eu/art-89-gdpr/
23. Google differential privacy: https://github.com/google/differential-privacy
24. Apple local DP: https://machinelearning.apple.com/research/learning-with-privacy-at-scale
25. GA data thresholds: https://support.google.com/analytics/answer/9383630
26. Viva minimum group size: https://learn.microsoft.com/en-us/viva/insights/advanced/setup-maint/privacy-settings
27. Google Access Transparency: https://docs.cloud.google.com/assured-workloads/access-transparency/docs/overview
28. Google Access Approval: https://docs.cloud.google.com/assured-workloads/access-approval/docs/overview
29. Azure Customer Lockbox: https://learn.microsoft.com/en-us/azure/security/fundamentals/customer-lockbox-overview
30. Mimir tenant federation: https://grafana.com/docs/mimir/latest/manage/secure/authentication-and-authorization/
31. Cortex `__tenant_id__` proposal: https://cortexmetrics.io/docs/proposals/cross-tenant-query-federation/
32. Loki multi-tenancy: https://grafana.com/docs/loki/latest/operations/multi-tenancy/
33. OpenTelemetry headers_setter: https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/extension/headerssetterextension/README.md
34. Grafana organizations: https://grafana.com/docs/grafana/latest/administration/organization-management/ ; roles: https://grafana.com/docs/grafana/latest/administration/roles-and-permissions/
35. Datadog multi-org: https://docs.datadoghq.com/account_management/multi_organization/ ; RBAC: https://docs.datadoghq.com/account_management/rbac/
36. Datadog cross-org visibility: https://docs.datadoghq.com/account_management/org_settings/cross_org_visibility/
37. Datadog cross-org sharing: https://docs.datadoghq.com/getting_started/access_for_enterprises/sharing_across_organizations/
38. Vault namespaces: https://developer.hashicorp.com/vault/docs/enterprise/namespaces
39. Vault policies: https://developer.hashicorp.com/vault/docs/concepts/policies
40. Vault audit devices: https://developer.hashicorp.com/vault/docs/audit
41. MCP security practices: https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices
42. OWASP LLM06:2025 Excessive Agency: https://genai.owasp.org/llmrisk/llm062025-excessive-agency/
43. OWASP LLM01 Prompt Injection: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
44. Willison, lethal trifecta: https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/
45. Google ADK safety: https://adk.dev/safety/
46. LangGraph memory: https://docs.langchain.com/oss/python/langgraph/memory
47. Anthropic sandboxing post: https://www.anthropic.com/engineering/claude-code-sandboxing
48. Claude Code permissions: https://code.claude.com/docs/en/permissions
49. OpenAI Codex approvals: https://learn.chatgpt.com/docs/agent-approvals-security
50. Hardy 1988, DOI only: https://doi.org/10.1145/54289.871709
51. NIST SP 800-207: https://csrc.nist.gov/pubs/sp/800/207/final
