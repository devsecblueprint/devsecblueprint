---
module_id: software-supply-chain-security
passing_score: 80
---

## Question 1

Why must security teams treat software delivery as a connected chain of trust?

A. Every stage uses the same security tool
B. Unverified assumptions and weaknesses can propagate across handoffs from source to deployment
C. Only the deployment platform can introduce risk
D. A container registry automatically validates every upstream system

**Correct Answer:** B

**Explanation:** Each stage consumes software or evidence from the previous stage. Trust is not automatic, and an untrusted dependency, compromised build, or substituted artifact can invalidate every later assumption.

---

## Question 2

What is the primary difference between direct and transitive dependencies?

A. Direct dependencies are always secure, while transitive dependencies are vulnerable
B. Direct dependencies are declared by the project, while transitive dependencies are required by other dependencies
C. Direct dependencies come from private registries only
D. Transitive dependencies do not become part of the application

**Correct Answer:** B

**Explanation:** Teams select direct dependencies, but those packages can pull in additional transitive dependencies. Both become part of the application’s attack surface.

---

## Question 3

Why should a project commit and enforce a lockfile or equivalent resolution record?

A. It guarantees that every dependency is free of vulnerabilities
B. It prevents developers from reviewing package changes
C. It helps the same commit resolve the same dependency set during later builds
D. It replaces the need for Software Composition Analysis

**Correct Answer:** C

**Explanation:** Repeatable dependency resolution keeps the built dependency set aligned with the one reviewed and scanned. It does not prove that those dependencies are safe.

---

## Question 4

What is the most accurate description of an SBOM?

A. A guarantee that an artifact contains no exploitable code
B. A structured inventory of components associated with a software artifact
C. A cryptographic signature proving who built an artifact
D. A deployment policy that blocks unapproved images

**Correct Answer:** B

**Explanation:** An SBOM records component information. It supports inventory and incident response, but it does not prove security, integrity, provenance, or authorization.

---

## Question 5

Why should an SBOM be associated with an immutable artifact digest?

A. The digest allows the SBOM to replace vulnerability scanning
B. The digest proves that every SBOM field is complete
C. The association identifies the exact artifact the inventory describes
D. The association makes the artifact publicly accessible

**Correct Answer:** C

**Explanation:** A digest ties the inventory to specific content. Without that relationship, teams may use an SBOM that describes a different build or release.

---

## Question 6

What does a valid artifact signature prove when verification uses an approved identity?

A. The artifact is vulnerability-free
B. The application meets every business requirement
C. The artifact matches the signed content and was signed by the expected identity
D. The build environment was not compromised

**Correct Answer:** C

**Explanation:** Signing provides integrity and signer authenticity. It does not independently prove vulnerability status, build security, or deployment authorization.

---

## Question 7

What additional question does build provenance answer beyond artifact signing?

A. How much the artifact costs to operate
B. Where and how the artifact was produced and which source was used
C. Whether every component has an open-source license
D. Whether the artifact will run without defects

**Correct Answer:** B

**Explanation:** Provenance connects an artifact to its source, build platform, workflow, inputs, and build invocation. A signature alone does not describe that history.

---

## Question 8

Why should a validated artifact be promoted between environments instead of rebuilt?

A. Rebuilding always produces a smaller artifact
B. Promotion preserves the identity that the tests, scans, SBOM, signature, and provenance describe
C. Rebuilding prevents developers from changing source code
D. Promotion removes the need for deployment controls

**Correct Answer:** B

**Explanation:** A rebuild creates a different artifact. Promoting the already validated digest keeps all retained evidence connected to what eventually runs.

---

## Question 9

Which is the best policy for verifying a keyless signature in CI/CD?

A. Accept any signature recorded in a transparency log
B. Verify only that a signature file exists
C. Require the expected artifact digest, certificate issuer, and approved workflow identity
D. Trust every signer from the same source-control organization

**Correct Answer:** C

**Explanation:** Verification must compare the signature to explicit identity and issuer expectations for the exact artifact. Signature presence alone is not authorization.

---

## Question 10

What is the correct way to handle an urgent release that cannot satisfy a blocking control?

A. Add `|| true` to the control so the pipeline succeeds
B. Delete the failed scan result
C. Record an approved exception with an owner, rationale, compensating controls, review cadence, expiry, and remediation target
D. Change the control to reporting mode without documenting the decision

**Correct Answer:** C

**Explanation:** Exceptions are legitimate when they are explicit, authorized, owned, monitored, and time-bound. They do not make the failed condition pass or close its underlying finding. Silently neutralizing a control manufactures false assurance.

---
