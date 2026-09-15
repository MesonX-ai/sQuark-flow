"""LLM Provider Service - Bedrock Integration for Agentic Workflows."""
import json
import logging
from typing import Optional, Dict, Any, AsyncIterator
from datetime import datetime
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class BedrockLLMProvider:
    """Bedrock LLM Provider using Claude 3.5 Sonnet (cost-effective & high-performance)."""

    # Model IDs for different providers
    CLAUDE_3_5_SONNET = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    CLAUDE_3_OPUS = "anthropic.claude-3-opus-20240229-v1:0"
    CLAUDE_3_SONNET = "anthropic.claude-3-sonnet-20240229-v1:0"

    # Pricing (AWS Bedrock - per 1M tokens, January 2025)
    PRICING = {
        CLAUDE_3_5_SONNET: {"input": 3.0, "output": 15.0},  # Most cost-effective
        CLAUDE_3_OPUS: {"input": 15.0, "output": 75.0},
        CLAUDE_3_SONNET: {"input": 3.0, "output": 15.0},
    }

    def __init__(self, region: str = "us-east-2"):
        """Initialize Bedrock client."""
        self.region = region
        self.model_id = self.CLAUDE_3_5_SONNET  # Default to cost-effective model
        
        try:
            self.client = boto3.client(
                "bedrock-runtime",
                region_name=region,
                # Credentials loaded from environment or ~/.aws/credentials
            )
            logger.info(f"✅ Bedrock LLM Provider initialized (region: {region})")
        except ClientError as e:
            logger.error(f"❌ Failed to initialize Bedrock client: {e}")
            raise

    async def invoke_llm(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """
        Invoke Claude via Bedrock and return structured response.

        Args:
            system_prompt: System context for the LLM
            user_message: User input/query
            temperature: Model temperature (0.0-1.0)
            max_tokens: Maximum tokens in response

        Returns:
            {
                "output": "Generated text response",
                "input_tokens": 123,
                "output_tokens": 456,
                "cost_usd": 0.005,
                "model": "claude-3-5-sonnet",
                "timestamp": "2025-01-15T10:30:00Z"
            }
        """
        try:
            # Prepare the request
            request_body = {
                "anthropic_version": "bedrock-2023-06-01",
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": user_message,
                    }
                ],
                "temperature": temperature,
            }

            # Call Bedrock
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json",
            )

            # Parse response
            response_body = json.loads(response["body"].read().decode("utf-8"))

            # Extract output
            output_text = response_body["content"][0]["text"]
            input_tokens = response_body.get("usage", {}).get("input_tokens", 0)
            output_tokens = response_body.get("usage", {}).get("output_tokens", 0)

            # Calculate cost
            pricing = self.PRICING[self.model_id]
            cost_usd = (
                (input_tokens * pricing["input"]) / 1_000_000
                + (output_tokens * pricing["output"]) / 1_000_000
            )

            logger.info(
                f"✅ LLM invocation successful | Model: {self.model_id} "
                f"| Input: {input_tokens} | Output: {output_tokens} | Cost: ${cost_usd:.6f}"
            )

            return {
                "output": output_text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost_usd": cost_usd,
                "model": self.model_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        except ClientError as e:
            logger.error(f"❌ Bedrock invocation failed: {e}")
            # Fallback to mock response for testing
            return self._mock_response(user_message)
        except Exception as e:
            logger.error(f"❌ Unexpected error in LLM invocation: {e}")
            return self._mock_response(user_message)

    def _mock_response(self, user_message: str) -> Dict[str, Any]:
        """Generate mock response when Bedrock is unavailable (for testing/development)."""
        logger.warning("⚠️  Bedrock unavailable - using mock response")
        return {
            "output": f"[MOCK] Processed your request: {user_message[:100]}...",
            "input_tokens": 50,
            "output_tokens": 100,
            "total_tokens": 150,
            "cost_usd": 0.0005,
            "model": self.model_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "is_mock": True,
        }

    async def stream_llm(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream Claude response via Bedrock.

        Yields:
            {"chunk": "token or partial content", "input_tokens": 123, "cost_usd": 0.001}
        """
        try:
            request_body = {
                "anthropic_version": "bedrock-2023-06-01",
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}],
                "temperature": temperature,
            }

            # Use invoke_model_with_response_stream for streaming
            response = self.client.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json",
            )

            input_tokens = 0
            output_tokens = 0
            accumulated_output = ""

            for event in response["body"]:
                if "chunk" in event:
                    chunk_data = json.loads(event["chunk"]["bytes"].decode("utf-8"))

                    if chunk_data["type"] == "content_block_delta":
                        delta = chunk_data.get("delta", {})
                        if "text" in delta:
                            chunk_text = delta["text"]
                            accumulated_output += chunk_text
                            yield {
                                "chunk": chunk_text,
                                "type": "content",
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                            }

                    elif chunk_data["type"] == "message_start":
                        msg = chunk_data.get("message", {})
                        usage = msg.get("usage", {})
                        input_tokens = usage.get("input_tokens", 0)

                    elif chunk_data["type"] == "message_delta":
                        usage = chunk_data.get("delta", {}).get("usage", {})
                        output_tokens = usage.get("output_tokens", 0)

            # Calculate final cost
            pricing = self.PRICING[self.model_id]
            cost_usd = (
                (input_tokens * pricing["input"]) / 1_000_000
                + (output_tokens * pricing["output"]) / 1_000_000
            )

            logger.info(
                f"✅ LLM stream completed | Tokens: {input_tokens}+{output_tokens} | Cost: ${cost_usd:.6f}"
            )

            yield {
                "type": "complete",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost_usd,
                "model": self.model_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        except ClientError as e:
            logger.error(f"❌ Bedrock stream failed: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

    def set_model(self, model_id: str):
        """Switch to different model (for A/B testing or cost optimization)."""
        if model_id in self.PRICING:
            self.model_id = model_id
            logger.info(f"✅ Model switched to: {model_id}")
        else:
            logger.warning(f"⚠️  Model {model_id} not supported")


# Singleton instance
_bedrock_provider: Optional[BedrockLLMProvider] = None


async def get_bedrock_provider(region: str = "us-east-2") -> BedrockLLMProvider:
    """Get or create Bedrock provider singleton."""
    global _bedrock_provider
    if _bedrock_provider is None:
        _bedrock_provider = BedrockLLMProvider(region=region)
    return _bedrock_provider
