# Trigger nodes
from src.workflows.engine.nodes.triggers.manual import ManualTriggerNode
from src.workflows.engine.nodes.triggers.whatsapp import WhatsAppTriggerNode
from src.workflows.engine.nodes.triggers.schedule import ScheduleTriggerNode
from src.workflows.engine.nodes.triggers.webhook import WebhookTriggerNode
from src.workflows.engine.nodes.triggers.email import EmailTriggerNode
from src.workflows.engine.nodes.triggers.form import FormTriggerNode
from src.workflows.engine.nodes.triggers.rss import RSSFeedTriggerNode

# Action nodes
from src.workflows.engine.nodes.actions.http_request import HTTPRequestNode
from src.workflows.engine.nodes.actions.code import CodeNode, JSCodeNode
from src.workflows.engine.nodes.actions.whatsapp import WhatsAppActionNode
from src.workflows.engine.nodes.actions.discord import DiscordSendNode
from src.workflows.engine.nodes.actions.email import EmailNode
from src.workflows.engine.nodes.actions.slack import SlackNode
from src.workflows.engine.nodes.actions.google_sheets import GoogleSheetsReadNode, GoogleSheetsWriteNode
from src.workflows.engine.nodes.actions.data import DataTransformNode, DataSetNode, DataStoreNode
from src.workflows.engine.nodes.actions.utility import NoOpNode

# Logic nodes
from src.workflows.engine.nodes.logic.if_node import IfNode
from src.workflows.engine.nodes.logic.switch import SwitchNode
from src.workflows.engine.nodes.logic.merge import MergeNode
from src.workflows.engine.nodes.logic.loop import LoopNode
from src.workflows.engine.nodes.logic.delay import DelayNode
from src.workflows.engine.nodes.logic.parallel import ParallelNode
from src.workflows.engine.nodes.logic.pause import PauseNode

# AI nodes
from src.workflows.engine.nodes.ai.llm import LLMNode
from src.workflows.engine.nodes.ai.agent import AgentNode

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
