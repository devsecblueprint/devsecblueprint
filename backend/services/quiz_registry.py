"""
Quiz Registry Module

Server-side storage for quiz definitions. Contains quiz questions, correct answers,
and explanations. This module is never exposed to the frontend to maintain quiz integrity.

Requirements: 2.1, 2.3, 2.4
"""

QUIZ_REGISTRY = {
    "prerequisites": {
        "passing_score": 70,
        "questions": [
            {
                "id": "q1",
                "correct_answer": "C",
                "explanation": "DevSecOps workflows rely heavily on version control systems like Git for managing source code, pull requests, branching strategies, and triggering automated pipeline builds.",
            },
            {
                "id": "q2",
                "correct_answer": "B",
                "explanation": "DevSecOps professionals frequently operate in Linux environments and must be comfortable navigating the command line, managing processes, and automating tasks using Bash scripting.",
            },
            {
                "id": "q3",
                "correct_answer": "C",
                "explanation": "DevSecOps involves scripting, Infrastructure as Code, APIs, and automation. Understanding programming concepts enables secure and effective automation.",
            },
            {
                "id": "q4",
                "correct_answer": "B",
                "explanation": "Understanding IP addressing, DNS, firewalls, and protocols like HTTP/HTTPS is fundamental to configuring and securing cloud and on-prem environments.",
            },
            {
                "id": "q5",
                "correct_answer": "B",
                "explanation": "Security fundamentals include encryption, authentication, access control, and understanding common threats such as malware and phishing.",
            },
            {
                "id": "q6",
                "correct_answer": "C",
                "explanation": "DevSecOps extends DevOps by integrating security into automation and collaboration practices. Without DevOps foundations, DevSecOps concepts will not make sense.",
            },
            {
                "id": "q7",
                "correct_answer": "B",
                "explanation": "Continuous Integration and Continuous Delivery pipelines are where security tools and automation are integrated into the development lifecycle.",
            },
            {
                "id": "q8",
                "correct_answer": "C",
                "explanation": "Cloud knowledge allows you to build scalable DevSecOps solutions by leveraging managed services, identity systems, and automation capabilities provided by cloud platforms.",
            },
            {
                "id": "q9",
                "correct_answer": "B",
                "explanation": "The Prerequisites section ensures learners have the foundational understanding necessary before diving into deeper DevSecOps and Cloud Security Development topics.",
            },
        ],
    },
    "secure-sdlc": {
        "passing_score": 70,
        "questions": [
            {
                "id": "q1",
                "correct_answer": "B",
                "explanation": "Secure SDLC (SSDLC) embeds security practices throughout the entire software development lifecycle, from planning to deployment and maintenance. This proactive approach helps identify and mitigate security vulnerabilities early in the development process.",
            },
            {
                "id": "q2",
                "correct_answer": "C",
                "explanation": "Threat modeling is a structured approach to identify potential security threats and vulnerabilities in a system's design. It helps teams understand attack vectors and prioritize security controls before implementation begins.",
            },
            {
                "id": "q3",
                "correct_answer": "A",
                "explanation": "Static Application Security Testing (SAST) analyzes source code without executing it to identify security vulnerabilities. It's most effective when integrated early in the development process, allowing developers to fix issues before they reach production.",
            },
            {
                "id": "q4",
                "correct_answer": "D",
                "explanation": "Dynamic Application Security Testing (DAST) tests running applications to identify security vulnerabilities by simulating attacks. Unlike SAST, DAST doesn't require access to source code and can identify runtime and environment-specific issues.",
            },
            {
                "id": "q5",
                "correct_answer": "B",
                "explanation": "Security code reviews should be performed continuously throughout development, not just at the end. Regular reviews help catch security issues early when they're easier and less expensive to fix, and they promote security awareness among the development team.",
            },
        ],
    },
}


def get_quiz(module_id: str) -> dict | None:
    """
    Retrieve quiz definition for a module.

    This function provides server-side access to quiz questions, correct answers,
    and explanations. The quiz registry is never exposed to the frontend to prevent
    answer leakage.

    Args:
        module_id: Module identifier (e.g., "secure-sdlc")

    Returns:
        Quiz definition dict containing:
            - passing_score: Minimum percentage required to pass (int)
            - questions: List of question dicts with id, correct_answer, explanation
        Returns None if module_id is not found in the registry.

    Requirements: 2.3, 2.4
    """
    return QUIZ_REGISTRY.get(module_id)
