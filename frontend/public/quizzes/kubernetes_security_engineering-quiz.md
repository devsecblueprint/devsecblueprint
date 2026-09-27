---
module_id: kubernetes-security-engineering
passing_score: 80
---

## Question 1

Why is a secure container image not sufficient to secure a Kubernetes workload?

A. Kubernetes does not run container images
B. The cluster can still grant excessive identity, host, network, secret, or deployment privileges
C. A secure image cannot be stored in a registry
D. Kubernetes automatically removes all image security controls

**Correct Answer:** B

**Explanation:** Kubernetes adds authorization, workload configuration, networking, admission, secrets, and runtime boundaries. Unsafe configuration at any of those layers can undermine a secure image.

---

## Question 2

Why should east-west protection combine NetworkPolicy, mTLS, and service authorization?

A. They all provide exactly the same protection
B. NetworkPolicy restricts reachability, mTLS authenticates and encrypts peers, and authorization controls what an authenticated workload may access
C. mTLS replaces the need for workload identity
D. Service authorization automatically encrypts every connection

**Correct Answer:** B

**Explanation:** These controls protect different layers. NetworkPolicy constrains network paths, mTLS provides authenticated encryption, and service authorization decides whether an authenticated caller may access the destination.

---

## Question 3

Which RBAC design best follows least privilege for one application namespace?

A. Bind `cluster-admin` to the default service account
B. Use wildcard resources and verbs in a ClusterRoleBinding
C. Use a dedicated service account with a minimal Role and RoleBinding
D. Share one administrator identity across every workload

**Correct Answer:** C

**Explanation:** A dedicated identity with namespaced, explicitly required permissions limits blast radius and improves attribution.

---

## Question 4

Which security-context combination is the strongest general starting point for an ordinary application container?

A. Privileged mode with host networking
B. Root user with every Linux capability
C. Non-root execution, no privilege escalation, dropped capabilities, and a read-only root filesystem
D. A writable hostPath mounted from the worker node

**Correct Answer:** C

**Explanation:** These settings reduce runtime authority and make container compromise less useful. Workload-specific exceptions should be tested, justified, and governed.

---

## Question 5

What must be true for a Kubernetes `NetworkPolicy` to enforce traffic restrictions?

A. The container image must be signed
B. The cluster network implementation must support and enforce NetworkPolicy
C. Every Pod must run as root
D. The namespace must contain a ClusterRoleBinding

**Correct Answer:** B

**Explanation:** A valid NetworkPolicy object does not create enforcement when the installed CNI or network implementation does not support it.

---

## Question 6

What is the distinction between RBAC and admission policy?

A. RBAC decides whether an identity may perform an action; admission evaluates whether the proposed resource is acceptable
B. RBAC scans images while admission stores secrets
C. Admission authenticates users while RBAC encrypts etcd
D. There is no distinction

**Correct Answer:** A

**Explanation:** Authorization to create a Pod does not mean every possible Pod configuration is safe. Admission policy evaluates the proposed object before it is persisted, creating a shared enforcement boundary for requests from pipelines, humans, controllers, and other API clients.

---

## Question 7

Why is base64 encoding insufficient protection for a Kubernetes Secret?

A. Kubernetes cannot decode base64
B. Base64 changes the value permanently
C. Base64 is reversible encoding and provides no confidentiality
D. Base64 prevents the Secret from being mounted

**Correct Answer:** C

**Explanation:** Anyone who can read the encoded value can recover the original. Secrets need encryption, least-privilege access, controlled delivery, rotation, and auditing.

---

## Question 8

What is the main advantage of cloud workload identity over a static cloud access key stored in Kubernetes?

A. It grants every workload administrator access
B. It provides short-lived, scoped credentials based on workload identity
C. It eliminates the need for cloud authorization
D. It converts Kubernetes namespaces into cloud accounts

**Correct Answer:** B

**Explanation:** Workload identity avoids long-lived, copyable credentials and can bind cloud access to a specific namespace and service account.

---

## Question 9

Which evidence source is most likely to detect an unexpected shell launched inside a running application container?

A. A Kubernetes API audit record
B. A runtime-behavior detection
C. An SBOM
D. A source-control commit log

**Correct Answer:** B

**Explanation:** API audit logs record requests handled by the API server, while runtime detection observes process, file, system-call, and network behavior inside running workloads.

---

## Question 10

Which approach best introduces and operates a blocking admission policy safely?

A. Enable it in production without testing and permit every request if the webhook fails
B. Exclude every existing namespace permanently
C. Test it in CI, measure violations in audit or warning mode, remediate, enforce progressively, and explicitly test the webhook’s failure behavior
D. Disable RBAC before applying it

**Correct Answer:** C

**Explanation:** Progressive rollout reveals compatibility problems before enforcement. Testing the webhook’s failure behavior also makes the security-versus-availability decision explicit instead of leaving it as an unexamined default.

---
