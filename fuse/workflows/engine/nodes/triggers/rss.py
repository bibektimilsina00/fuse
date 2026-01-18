from typing import Any, Dict
import feedparser
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class RSSFeedTriggerNode(BaseNode):
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="rss.read",
            label="RSS Feed",
            type="trigger",
            description="Triggers when new items are found in an RSS feed.",
            category="Trigger",
            inputs=[
                NodeInput(name="url", type="string", label="Feed URL", required=True),
                NodeInput(name="check_interval", type="number", label="Check Interval (min)", default=15)
            ],
            outputs=[
                NodeOutput(name="title", type="string", label="Title"),
                NodeOutput(name="link", type="string", label="Link"),
                NodeOutput(name="summary", type="string", label="Summary"),
                NodeOutput(name="published", type="string", label="Published Date")
            ],
            trigger_group="app"
        )

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Dict[str, Any]:
        # In a real environment, the scheduler handles the polling and deduplication.
        # This execution method simulates fetching the latest item for immediate run/test.
        url = context.get("node_config", {}).get("url")
        if not url:
            return {}
            
        feed = feedparser.parse(url)
        if not feed.entries:
            return {}
            
        latest = feed.entries[0]
        return {
            "title": latest.get("title", ""),
            "link": latest.get("link", ""),
            "summary": latest.get("summary", ""),
            "published": latest.get("published", "")
        }
