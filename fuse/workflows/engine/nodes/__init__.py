# Trigger nodes
from fuse.workflows.engine.nodes.triggers.manual import ManualTriggerNode
from fuse.workflows.engine.nodes.triggers.whatsapp import WhatsAppTriggerNode
from fuse.workflows.engine.nodes.triggers.schedule import ScheduleTriggerNode
from fuse.workflows.engine.nodes.triggers.webhook import WebhookTriggerNode
from fuse.workflows.engine.nodes.triggers.email import EmailTriggerNode
from fuse.workflows.engine.nodes.triggers.form import FormTriggerNode
from fuse.workflows.engine.nodes.triggers.rss import RSSFeedTriggerNode

# Action nodes
from fuse.workflows.engine.nodes.actions.http_request import HTTPRequestNode
from fuse.workflows.engine.nodes.actions.code import CodeNode, JSCodeNode
from fuse.workflows.engine.nodes.actions.whatsapp import WhatsAppActionNode
from fuse.workflows.engine.nodes.actions.discord import DiscordSendNode
from fuse.workflows.engine.nodes.actions.email import EmailNode
from fuse.workflows.engine.nodes.actions.slack import SlackNode
from fuse.workflows.engine.nodes.actions.google_sheets import GoogleSheetsReadNode, GoogleSheetsWriteNode
from fuse.workflows.engine.nodes.actions.data import DataTransformNode, DataSetNode, DataStoreNode
from fuse.workflows.engine.nodes.actions.utility import NoOpNode

# Logic nodes
from fuse.workflows.engine.nodes.logic.if_node import IfNode
from fuse.workflows.engine.nodes.logic.switch import SwitchNode
from fuse.workflows.engine.nodes.logic.merge import MergeNode
from fuse.workflows.engine.nodes.logic.loop import LoopNode
from fuse.workflows.engine.nodes.logic.delay import DelayNode
from fuse.workflows.engine.nodes.logic.parallel import ParallelNode
from fuse.workflows.engine.nodes.logic.pause import PauseNode

# AI nodes
from fuse.workflows.engine.nodes.ai.llm import LLMNode
from fuse.workflows.engine.nodes.ai.agent import AgentNode

# This ensures all nodes are registered when this package is imported
__all__ = [
    # Triggers
    "ManualTriggerNode",
    "WhatsAppTriggerNode",
    "ScheduleTriggerNode",
    "WebhookTriggerNode",
    "EmailTriggerNode",
    "FormTriggerNode",
    "RSSFeedTriggerNode",
    # Actions
    "HTTPRequestNode",
    "CodeNode",
    "JSCodeNode",
    "WhatsAppActionNode",
    "DiscordSendNode",
    "EmailNode",
    "SlackNode",
    "GoogleSheetsReadNode",
    "GoogleSheetsWriteNode",
    "DataTransformNode",
    "DataSetNode",
    "DataStoreNode",
    "NoOpNode",
    # Logic
    "IfNode",
    "SwitchNode",
    "MergeNode",
    "LoopNode",
    "DelayNode",
    "ParallelNode",
    "PauseNode",
    # AI
    "LLMNode",
    "AgentNode",
]
