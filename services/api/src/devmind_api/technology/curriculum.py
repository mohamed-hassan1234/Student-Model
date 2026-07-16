from enum import StrEnum


class TechnologyTopic(StrEnum):
    HTML = "html"
    CSS = "css"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    REACT = "react"
    NODEJS = "nodejs"
    EXPRESS = "express"
    MONGODB = "mongodb"
    GIT = "git"
    GITHUB = "github"
    SOFTWARE_ENGINEERING = "software_engineering"


SUPPORTED_TOPICS: tuple[TechnologyTopic, ...] = tuple(TechnologyTopic)


def classify_question(question: str) -> TechnologyTopic | None:
    text = question.lower()
    keyword_map: dict[TechnologyTopic, tuple[str, ...]] = {
        TechnologyTopic.HTML: ("html", "semantic", "element", "doctype"),
        TechnologyTopic.CSS: ("css", "selector", "flexbox", "grid", "style"),
        TechnologyTopic.JAVASCRIPT: ("javascript", "js", "promise", "async", "function"),
        TechnologyTopic.TYPESCRIPT: ("typescript", "type", "interface", "generic"),
        TechnologyTopic.REACT: ("react", "component", "hook", "jsx", "state"),
        TechnologyTopic.NODEJS: ("node", "node.js", "npm", "runtime"),
        TechnologyTopic.EXPRESS: ("express", "middleware", "route handler"),
        TechnologyTopic.MONGODB: ("mongodb", "document", "collection", "index"),
        TechnologyTopic.GIT: ("git", "commit", "branch", "merge", "rebase"),
        TechnologyTopic.GITHUB: ("github", "pull request", "actions", "repository"),
        TechnologyTopic.SOFTWARE_ENGINEERING: ("test", "architecture", "design", "refactor"),
    }
    for topic, keywords in keyword_map.items():
        if any(keyword in text for keyword in keywords):
            return topic
    return None
