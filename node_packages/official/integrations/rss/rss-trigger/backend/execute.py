from typing import Any, Dict, List
import httpx
import xml.etree.ElementTree as ET
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Fetch and parse RSS feed.
    """
    resolved_config = context.resolve_config()
    url = resolved_config.get("url")
    
    if not url:
        raise ValueError("Feed URL is required")
        
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code != 200:
             raise RuntimeError(f"Failed to fetch feed: {resp.status_code}")
        xml_content = resp.text

    # Basic XML Parsing
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise RuntimeError(f"Failed to parse XML: {e}")
    
    # Check for RSS (channel/item) or Atom (entry)
    items = []
    feed_meta = {}
    
    # RSS 2.0
    channel = root.find("channel")
    if channel is not None:
        feed_meta["title"] = channel.findtext("title")
        feed_meta["description"] = channel.findtext("description")
        
        for item in channel.findall("item"):
            items.append({
                "title": item.findtext("title"),
                "link": item.findtext("link"),
                "description": item.findtext("description"),
                "pubDate": item.findtext("pubDate"),
                "guid": item.findtext("guid")
            })
    else:
        # Try Atom
        # Namespace handling is annoying in ET, ignoring for simplicty if possible or handle wildcard
        # For now, just basic RSS 2.0 support is mandated by "MVP".
        pass
        
    # Return 1 item with list of rows (like Sheets Read)
    # OR fan out?
    # "Read" nodes usually return List[Items].
    
    output_items = []
    for i in items:
        output_items.append(WorkflowItem(json=i))
        
    return output_items
