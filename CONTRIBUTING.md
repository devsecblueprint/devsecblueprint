# **Contributing to The DevSec Blueprint**

We are thrilled to have you contribute to **The DevSec Blueprint**, Our goal is to create a welcoming and collaborative environment where all contributors can have a meaningful impact. Below, we’ve outlined some important guidelines to ensure that your contributions are effective, respectful, and aligned with the project’s goals.

## **Collaboration Guidelines**

### **Encourage Effective and Respectful Collaboration**

Collaboration is key to the success of any open-source project. We strive to maintain a respectful, productive, and inclusive environment for all contributors, regardless of their experience level. By collaborating effectively, we can build a stronger, more cohesive community and achieve the best outcomes for the project.

Please make sure to adhere to our [`Code of Conduct`](CODE_OF_CONDUCT.md) to ensure that all interactions within the community remain respectful, inclusive, and constructive.

### **Your First Contribution**

Unsure where to begin contributing? You can start by looking through [help wanted](https://github.com/devsecblueprint/devsecblueprint/issues?q=state%3Aopen%20label%3A%22help%20wanted%22)

Never contributed to open source before? Here are a couple of friendly tutorials:

- <http://www.firsttimersonly.com/>
- <https://egghead.io/courses/how-to-contribute-to-an-open-source-project-on-github>

### **How to Contribute**

#### **1. Suggestions for New Projects or Documents**

We love hearing your ideas for new projects or additional documentation! If you have suggestions for expanding or improving the project, please direct them to the **`#suggestions`** channel on our [Discord server](https://discord.com/invite/enMmUNq8jc). This allows the moderators and community managers to discuss your idea with you.

### **2. Improvements to Existing Content**

We welcome contributions to improve existing codebases and projects! This includes:

- Fixing typos or grammatical errors.
- Addressing bugs or issues.
- Updating code to align with the latest technologies or best practices.

These contributions help ensure that **The DevSec Blueprint** remains up-to-date and effective for all learners.

### **3. Submitting Pull Requests**

When submitting a pull request:

1. Ensure that your code follows the existing style and guidelines in the repository.
2. Include a clear and concise **summary** of the changes you made, explaining why they are necessary or beneficial.
3. **Ensure the PR title follows the correct format**:  
   The title should be in the format:  
   `type(scope): summary`  
   Where:

   - **type**: The type of change (e.g., `build`, `fix`, `docs`, `ci`, `feat`)
   - **scope** (optional): A specific area or module affected (e.g., `projects`, `typo`, `workflow`, `blueprint`, `security`)
   - **summary**: A short description of the change (e.g., "add user login feature", "fix typo in README").

   Example titles:

   - `feat(projects): integrate new task management system`
   - `fix(typo): correct spelling mistake on home page`
   - `docs: update README with new instructions`

   **Note**: The PR title should be clear and provide context for the changes made. It should help the reviewer understand the scope and purpose of the change quickly.

4. Submit the pull request and also **post it in the `#dsb-contributors` channel** on [Discord server](https://discord.com/invite/enMmUNq8jc). This helps the community stay informed about your changes, and allows our team to review and provide feedback.

Here’s the updated installation instructions in Markdown format:

## Installation Instructions

If you're looking to contribute to the core documentation website, follow these steps:

### Prerequisites

1. Ensure you have **Node.js** and **npm** installed on your local machine.

#### Steps to Get Started

1. Create a file named `.env` in the root directory of the project and add the following environment variables:

   ```env
   GOOGLE_ANALYTICS_ID=test
   GOOGLE_TAG_MANAGER_ID=test
   ```

2. Install dependencies and start the development server by running the following commands:

   ```bash
   npm install
   npm run start
   ```

3. Once the commands have executed successfully, the UI should load on your local machine.

## Communication and Collaboration

Collaboration is key to our success! If you have questions or need guidance, don’t hesitate to reach out in the appropriate Discord channels. We’re here to help and support you throughout the process.

## Thank You

We truly appreciate your contributions. By working together, we can continue improving this project and making it more useful for everyone. Happy coding!
