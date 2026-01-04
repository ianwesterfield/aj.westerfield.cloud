"""
title: Capture Training Data
author: AJ
version: 0.1.0
required_open_webui_version: 0.4.0
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iY3VycmVudENvbG9yIj48cGF0aCBkPSJNMTIgMkM2LjQ4IDIgMiA2LjQ4IDIgMTJzNC40OCAxMCAxMCAxMCAxMC00LjQ4IDEwLTEwUzE3LjUyIDIgMTIgMnptLTEgMTdIOVYxM2gydjZoLTJ2LTZ6bTQgMGgtMnYtNGgydjR6bTAtNmgtMlY5aDJ2NHoiLz48L3N2Zz4=

Capture Training Data Action for AJ.

Allows users to rate and flag conversations for training data extraction.
Stores to Qdrant for later extraction into training datasets.
"""

import os
import json
import httpx
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


# Orchestrator URL
ORCHESTRATOR_API_URL = os.getenv("ORCHESTRATOR_API_URL", "http://orchestrator_api:8004")


class Action:
    """
    Training Data Capture Action.
    
    Adds a button below messages to rate and flag conversations
    for training data extraction.
    """
    
    class Valves(BaseModel):
        """Configuration for the training capture action."""
        orchestrator_url: str = Field(
            default="http://orchestrator_api:8004",
            description="URL of the orchestrator API"
        )
        enable_workspace_capture: bool = Field(
            default=True,
            description="Include workspace state in captures"
        )
    
    def __init__(self):
        self.valves = self.Valves()
    
    async def action(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__=None,
        __event_call__=None,
        __model__: Optional[dict] = None,
    ) -> dict:
        """
        Main action handler - captures training data with user rating.
        
        Flow:
        1. Show rating modal to user
        2. Collect rating + training type + optional tags
        3. Send to orchestrator for Qdrant storage
        """
        # Get the message content
        message_content = body.get("content", "")
        message_id = body.get("id", "")
        
        # Get conversation history to find the user prompt
        messages = body.get("messages", [])
        
        # Find the user prompt that preceded this response
        user_prompt = ""
        for i, msg in enumerate(messages):
            if msg.get("id") == message_id:
                # Look backwards for the user message
                for j in range(i - 1, -1, -1):
                    if messages[j].get("role") == "user":
                        user_prompt = messages[j].get("content", "")
                        break
                break
        
        # If we couldn't find it in messages, try to get from body
        if not user_prompt:
            user_prompt = body.get("user_message", "")
        
        # Show status
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": "📊 Opening training capture form..."}
            })
        
        # Request rating from user
        if __event_call__:
            rating_response = await __event_call__({
                "type": "input",
                "data": {
                    "title": "📊 Rate This Response",
                    "message": "How helpful was this response? (1-5)",
                    "placeholder": "Enter a number 1-5"
                }
            })
            
            # Parse rating
            try:
                rating = int(rating_response) if rating_response else 3
                rating = max(1, min(5, rating))  # Clamp to 1-5
            except (ValueError, TypeError):
                rating = 3
            
            # Request training type
            training_type_response = await __event_call__({
                "type": "input",
                "data": {
                    "title": "📚 Training Type",
                    "message": "What type of training example is this?\n\n1 = Good Example\n2 = Edge Case\n3 = Hard Negative (wrong approach)\n4 = Knowledge Example\n5 = Just Feedback",
                    "placeholder": "Enter 1-5"
                }
            })
            
            # Map to training type
            type_map = {
                "1": "good_example",
                "2": "edge_case", 
                "3": "hard_negative",
                "4": "knowledge_graph",
                "5": "feedback"
            }
            training_type = type_map.get(training_type_response, "feedback")
            
            # Request optional tags
            tags_response = await __event_call__({
                "type": "input",
                "data": {
                    "title": "🏷️ Tags (Optional)",
                    "message": "Add comma-separated tags (e.g., powershell, windows, error, permission)",
                    "placeholder": "Leave empty or enter tags"
                }
            })
            
            # Parse tags
            tags = []
            if tags_response:
                tags = [t.strip().lower() for t in tags_response.split(",") if t.strip()]
        else:
            # Fallback defaults
            rating = 3
            training_type = "feedback"
            tags = []
        
        # Show saving status
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": "💾 Saving to training database..."}
            })
        
        # Build capture payload
        capture_payload = {
            "session_id": body.get("session_id", body.get("chat_id", "")),
            "message_id": message_id,
            "timestamp": datetime.utcnow().isoformat(),
            "user_prompt": user_prompt,
            "model_response": message_content,
            "rating": rating,
            "training_type": training_type,
            "tags": tags,
            "model_id": __model__.get("id", "") if __model__ else "",
            "user_id": __user__.get("id", "") if __user__ else "",
        }
        
        # Send to orchestrator
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.valves.orchestrator_url}/api/training/capture",
                    json=capture_payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Show success notification
                    if __event_emitter__:
                        await __event_emitter__({
                            "type": "notification",
                            "data": {
                                "type": "success",
                                "content": f"✅ Saved as {training_type} (rating: {rating}/5)"
                            }
                        })
                    
                    return {
                        "content": f"📊 **Training Data Captured**\n\n"
                                   f"- **Rating**: {'⭐' * rating}{'☆' * (5-rating)}\n"
                                   f"- **Type**: {training_type.replace('_', ' ').title()}\n"
                                   f"- **Tags**: {', '.join(tags) if tags else 'None'}\n"
                                   f"- **ID**: `{result.get('vector_id', 'N/A')[:8]}...`"
                    }
                else:
                    error_detail = response.text[:200]
                    if __event_emitter__:
                        await __event_emitter__({
                            "type": "notification",
                            "data": {
                                "type": "error",
                                "content": f"Failed to save: {response.status_code}"
                            }
                        })
                    return {"content": f"❌ Failed to save training data: {error_detail}"}
                    
        except httpx.TimeoutException:
            if __event_emitter__:
                await __event_emitter__({
                    "type": "notification",
                    "data": {"type": "error", "content": "Timeout connecting to orchestrator"}
                })
            return {"content": "❌ Timeout saving training data"}
            
        except Exception as e:
            if __event_emitter__:
                await __event_emitter__({
                    "type": "notification",
                    "data": {"type": "error", "content": f"Error: {str(e)[:50]}"}
                })
            return {"content": f"❌ Error saving training data: {str(e)}"}
