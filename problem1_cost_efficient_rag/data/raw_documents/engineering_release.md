# Engineering release process

Every production release requires an approved pull request, automated unit tests, and a rollback plan. High-risk changes also require a peer review from the on-call engineer. Deployments are made in a canary stage before a full rollout. A failed canary is rolled back before it reaches all customers.

The standard change window is Tuesday and Thursday between 09:00 and 16:00 UTC. Emergency changes may be made outside the window when approved by the incident commander.
