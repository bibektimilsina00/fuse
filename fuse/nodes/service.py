import os
import json
import shutil
import logging
from typing import List, Optional, Dict, Any
from fastapi import UploadFile, HTTPException

from fuse.workflows.engine.nodes.registry import NodeRegistry
from fuse.nodes.schemas import NodeCreateRequest, NodeUpdateRequest

logger = logging.getLogger(__name__)

class NodeManagementService:
    def __init__(self):
        # We need to know where custom nodes are stored
        # By convention, NodeRegistry looks in 'node_packages'.
        # We will enforce creating new nodes in `node_packages/custom/`
        self.base_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "node_packages"
        )
        self.custom_path = os.path.join(self.base_path, "custom")
        
        # Ensure custom directory exists
        os.makedirs(self.custom_path, exist_ok=True)

    def list_nodes(self) -> List[Dict[str, Any]]:
        """List all available nodes with detailed metadata."""
        # Ensure registry is initialized
        if not NodeRegistry._nodes:
            NodeRegistry.initialize()
            
        nodes = []
        for node_id, package in NodeRegistry._nodes.items():
            manifest = package.manifest
            is_custom = "custom" in package.path  # Simple heuristic
            
            nodes.append({
                "id": node_id,
                "name": manifest.get("name", node_id),
                "version": manifest.get("version", "1.0.0"),
                "category": manifest.get("category", "unknown"),
                "description": manifest.get("description", ""),
                "manifest": manifest,
                "is_custom": is_custom,
                "path": package.path,
                "has_icon": manifest.get("icon_svg") is not None
            })
        return nodes

    def get_node(self, node_id: str) -> Dict[str, Any]:
        """Get details of a specific node, including code if custom."""
        if not NodeRegistry._nodes:
            NodeRegistry.initialize()
            
        package = NodeRegistry.get_node(node_id)
        if not package:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
            
        manifest = package.manifest
        is_custom = "custom" in package.path
        
        code = None
        if is_custom:
            try:
                code_path = os.path.join(package.path, "backend", "execute.py")
                if os.path.exists(code_path):
                    with open(code_path, "r") as f:
                        code = f.read()
            except Exception as e:
                logger.warning(f"Could not read code for custom node {node_id}: {e}")
        
        return {
            "id": node_id,
            "manifest": manifest,
            "code": code,
            "is_custom": is_custom,
            "path": package.path
        }

    def create_node(self, request: NodeCreateRequest) -> Dict[str, Any]:
        """Create a new custom node package."""
        node_id = request.manifest.id
        
        if NodeRegistry.get_node(node_id):
            raise HTTPException(status_code=400, detail=f"Node {node_id} already exists")
            
        # Sanitize folder name
        safe_name = node_id.replace(".", "-").lower()
        node_dir = os.path.join(self.custom_path, safe_name)
        
        if os.path.exists(node_dir):
             raise HTTPException(status_code=400, detail=f"Node directory for {node_id} already exists")
             
        try:
            # maintain structure:
            # node-name/
            #   manifest.json
            #   backend/
            #     execute.py
            #   frontend/
            #     icon.svg
            
            os.makedirs(os.path.join(node_dir, "backend"))
            os.makedirs(os.path.join(node_dir, "frontend"))
            
            # Write manifest.json
            manifest_path = os.path.join(node_dir, "manifest.json")
            with open(manifest_path, "w") as f:
                json.dump(request.manifest.dict(), f, indent=2)
                
            # Write execute.py
            code_path = os.path.join(node_dir, "backend", "execute.py")
            with open(code_path, "w") as f:
                f.write(request.code)
                
            # Create empty init
            with open(os.path.join(node_dir, "backend", "__init__.py"), "w") as f:
                f.write("")
                
            # Reload registry to pick up new node
            NodeRegistry.initialize()
            
            return self.get_node(node_id)
            
        except Exception as e:
            # Cleanup on failure
            if os.path.exists(node_dir):
                shutil.rmtree(node_dir)
            logger.error(f"Failed to create node: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create node: {str(e)}")

    def update_node(self, node_id: str, request: NodeUpdateRequest) -> Dict[str, Any]:
        """Update an existing custom node."""
        package = NodeRegistry.get_node(node_id)
        if not package:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
            
        if "custom" not in package.path:
            raise HTTPException(status_code=403, detail="Only custom nodes can be modified")
            
        try:
            if request.manifest:
                # Update manifest.json
                # Be careful not to change ID if possible, or handle rename
                manifest_path = os.path.join(package.path, "manifest.json")
                with open(manifest_path, "w") as f:
                    # Merge? Or replace? Assuming replace for now but should preserve some fields maybe
                    json.dump(request.manifest.dict(), f, indent=2)
            
            if request.code:
                code_path = os.path.join(package.path, "backend", "execute.py")
                with open(code_path, "w") as f:
                    f.write(request.code)

            # Reload registry
            NodeRegistry.initialize()
            
            return self.get_node(node_id)
            
        except Exception as e:
            logger.error(f"Failed to update node: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update node: {str(e)}")

    def delete_node(self, node_id: str):
        """Delete a custom node."""
        package = NodeRegistry.get_node(node_id)
        if not package:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
            
        if "custom" not in package.path:
            raise HTTPException(status_code=403, detail="Only custom nodes can be deleted")
            
        try:
            shutil.rmtree(package.path)
            NodeRegistry.initialize()
            return {"status": "success", "message": f"Node {node_id} deleted"}
        except Exception as e:
            logger.error(f"Failed to delete node: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete node: {str(e)}")

    async def upload_icon(self, node_id: str, file: UploadFile):
        """Upload an SVG icon for the node."""
        package = NodeRegistry.get_node(node_id)
        if not package:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
            
        if "custom" not in package.path:
            raise HTTPException(status_code=403, detail="Only custom nodes can accept icon uploads via API")
            
        if not file.filename.endswith(".svg"):
             raise HTTPException(status_code=400, detail="Only .svg files are supported")
             
        try:
            icon_path = os.path.join(package.path, "frontend", "icon.svg")
            os.makedirs(os.path.dirname(icon_path), exist_ok=True)
            
            content = await file.read()
            with open(icon_path, "wb") as f:
                f.write(content)
                
            NodeRegistry.initialize()
            return {"status": "success", "message": "Icon updated"}
        except Exception as e:
            logger.error(f"Failed to upload icon: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload icon: {str(e)}")

node_management_service = NodeManagementService()
