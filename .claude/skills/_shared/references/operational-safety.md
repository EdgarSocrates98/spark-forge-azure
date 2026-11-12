# SparkForge skill contract: operational safety

Operational Azure skills may explain or prepare a change, but the default
path is read-only. Collection is allowed only when the skill explicitly
documents the artifact and the required operator scope. Mutating Azure
commands, destructive Delta/Iceberg maintenance, deletion, RBAC/policy
writes, and production deploys require explicit confirmation from the
operator with subscription, resource, action, and rollback/retention scope.

Before recommending a write:

- separate declared configuration from observed configuration;
- identify the runtime and the authorization layer involved;
- record unresolved cross-subscription, resource-policy, Key Vault, or
  Azure Policy evidence;
- provide a reversible change or a concrete `git revert`/restore procedure;
- validate data correctness and service health after the change.

Never turn `AuthorizationPermissionMismatch`/`403` into “add permission”
without preserving `denied_by`. RBAC de controle não avalia ACL POSIX do
ADLS, grants do Unity Catalog nem secret scopes do Key Vault; report those
as separate unresolved authorization layers when not observed.
