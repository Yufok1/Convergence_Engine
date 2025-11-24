"""
🌐 Causation Explorer Web UI

Simple web interface for interactive causation exploration
Uses Flask + D3.js for interactive graph visualization
"""

from flask import Flask, render_template, jsonify, request, abort, Response
from causation_explorer import CausationExplorer
import json
from pathlib import Path
import logging
import traceback
import time
import requests
import re
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import os
from datetime import datetime
import base64
import io
import queue
import threading

# Setup logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import PIL for image compression
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL/Pillow not available - image compression disabled. Install with: pip install Pillow")

# Try to import Flask-SocketIO for real-time event streaming
try:
    from flask_socketio import SocketIO, emit
    SOCKETIO_AVAILABLE = True
    logger.info("Flask-SocketIO available - real-time event streaming enabled")
except ImportError:
    SOCKETIO_AVAILABLE = False
    logger.warning("Flask-SocketIO not available - real-time streaming disabled. Install with: pip install flask-socketio")

# Real-time event queue for CRA
cra_event_queue = queue.Queue(maxsize=1000)  # Buffer up to 1000 events

# Ensure Flask knows where templates are
template_dir = Path(__file__).parent / 'templates'
app = Flask(__name__, template_folder=str(template_dir))

# Initialize SocketIO after Flask app is created
if SOCKETIO_AVAILABLE:
    socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Causation Explorer with error handling
# Set log_dir explicitly to ensure it finds logs on Render
project_root = Path(__file__).parent
log_dir = project_root / 'data' / 'logs'
try:
    explorer = CausationExplorer(log_dir=log_dir)
    logger.info(f"Causation Explorer initialized successfully (log_dir: {log_dir}, exists: {log_dir.exists()})")
    if log_dir.exists():
        log_files = list(log_dir.glob('*.log'))
        logger.info(f"Found {len(log_files)} log files: {[f.name for f in log_files]}")
except Exception as e:
    logger.error(f"Failed to initialize Causation Explorer: {e}", exc_info=True)
    explorer = None


# ============================================================================
# CONVERGENCE RESEARCH ASSISTANT - BACKEND CLASSES
# ============================================================================

class OllamaBridge:
    """HTTP client for Ollama API (supports both local and cloud)"""
    
    def __init__(self, base_url: str = None, timeout: float = None, api_key: str = None):
        # Support environment variables for configuration
        # OLLAMA_BASE_URL defaults to localhost, or use https://ollama.com for cloud
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.timeout = timeout or float(os.getenv("OLLAMA_TIMEOUT", "30.0"))
        # OLLAMA_API_KEY required for cloud API access
        self.api_key = api_key or os.getenv("OLLAMA_API_KEY")
        
        # Determine if we're using cloud (https://ollama.com)
        self.is_cloud = self.base_url.startswith("https://ollama.com")
        
        # Build headers (include auth for cloud)
        self.headers = {}
        if self.is_cloud:
            if self.api_key:
                self.headers['Authorization'] = f'Bearer {self.api_key}'
                self.headers['Content-Type'] = 'application/json'  # Explicit content type for cloud
                logger.info(f"✅ OllamaBridge configured for cloud: {self.base_url}")
                logger.debug(f"Headers initialized: Authorization={bool(self.headers.get('Authorization'))}, "
                           f"Content-Type={bool(self.headers.get('Content-Type'))}, "
                           f"API key length={len(self.api_key)}")
            else:
                logger.warning("⚠️ Ollama Cloud URL detected but OLLAMA_API_KEY not set. Cloud API calls will fail.")
                logger.info("   Set OLLAMA_API_KEY environment variable or get key from: https://ollama.com/settings/keys")
        else:
            logger.info(f"✅ OllamaBridge configured for local: {self.base_url}")
    
    def update_config(self, base_url: str = None, api_key: str = None, timeout: float = None):
        """Update configuration dynamically"""
        if base_url is not None:
            self.base_url = base_url
            self.is_cloud = self.base_url.startswith("https://ollama.com")
        
        if api_key is not None:
            self.api_key = api_key
        
        if timeout is not None:
            self.timeout = timeout
        
        # Rebuild headers - CRITICAL: Always rebuild headers when config changes
        self.headers = {}
        if self.is_cloud:
            if self.api_key:
                self.headers['Authorization'] = f'Bearer {self.api_key}'
                self.headers['Content-Type'] = 'application/json'  # Required for cloud API
                logger.debug(f"Headers set: Authorization={bool(self.headers.get('Authorization'))}, "
                           f"Content-Type={bool(self.headers.get('Content-Type'))}, "
                           f"API key length={len(self.api_key) if self.api_key else 0}")
            else:
                logger.warning("Ollama Cloud configured but API key is missing!")
        
        logger.info(f"OllamaBridge configuration updated: {self.base_url} (cloud: {self.is_cloud}, has_api_key: {bool(self.api_key)})")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available Ollama models"""
        try:
            # For cloud, try /v1/models endpoint first (OpenAI-compatible), fallback to /api/tags
            endpoint = "/v1/models" if self.is_cloud else "/api/tags"
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                timeout=self.timeout
            )
            
            # If 404 on /v1/models, try /api/tags for cloud
            if response.status_code == 404 and self.is_cloud and endpoint == "/v1/models":
                logger.debug("Cloud /v1/models returned 404, trying /api/tags")
                response = requests.get(
                    f"{self.base_url}/api/tags",
                    headers=self.headers,
                    timeout=self.timeout
                )
            
            response.raise_for_status()
            data = response.json()
            
            # Handle different response formats
            models = []
            if 'data' in data:  # OpenAI-compatible format (/v1/models)
                models = data['data']
            elif 'models' in data:  # Ollama format (/api/tags)
                models = data['models']
            elif isinstance(data, list):  # Direct list
                models = data
            
            # Ensure we return a list of model dicts with 'name' key
            result = []
            for model in models:
                if isinstance(model, dict):
                    if 'name' in model:
                        result.append(model)
                    elif 'model' in model:
                        result.append({'name': model['model'], **model})
                    elif 'id' in model:  # OpenAI format uses 'id'
                        result.append({'name': model['id'], **model})
                elif isinstance(model, str):
                    result.append({'name': model, 'model': model})
            return result
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Ollama API endpoint not found (404). Base URL: {self.base_url}, Endpoint: {endpoint if 'endpoint' in locals() else '/api/tags'}")
                logger.error("This may indicate:")
                logger.error("  1. Ollama Cloud API structure has changed")
                logger.error("  2. Incorrect base URL configuration")
                logger.error("  3. API key is invalid or expired")
            else:
                logger.error(f"HTTP error listing Ollama models: {e.response.status_code} - {e.response.text[:200]}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error listing Ollama models: {e}")
            logger.error("This may indicate:")
            logger.error("  1. Network connectivity issues")
            logger.error("  2. Ollama Cloud service is down")
            logger.error("  3. Firewall/proxy blocking connection")
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}", exc_info=True)
            if self.is_cloud and not self.api_key:
                logger.warning("OLLAMA_API_KEY not set - required for cloud access")
        return []
    
    def chat(self, model: str, messages: List[Dict[str, str]], context: Dict[str, Any] = None) -> Optional[str]:
        """Send chat message with context to Ollama"""
        # Check API key for cloud before making request
        if self.is_cloud and not self.api_key:
            logger.error(
                "Ollama Cloud API key is required but not set. "
                "Please set OLLAMA_API_KEY environment variable or configure it in the web UI. "
                "Get your API key from: https://ollama.com/settings/keys"
            )
            return None
        
        try:
            # Build system prompt with context
            system_prompt = self._build_system_prompt(context)
            
            # Combine system prompt with messages
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)
            
            payload = {
                "model": model,
                "messages": full_messages,
                "stream": False
            }
            
            # Ensure headers are set for cloud requests
            if self.is_cloud:
                if not self.api_key:
                    raise Exception(
                        "Ollama Cloud API key is missing. Please configure it in the web UI or set OLLAMA_API_KEY environment variable."
                    )
                if not self.headers.get('Authorization'):
                    self.headers['Authorization'] = f'Bearer {self.api_key}'
                    self.headers['Content-Type'] = 'application/json'
                    logger.warning("Headers were missing in chat(), rebuilt them before request")
            
            # For cloud, try /v1/chat/completions endpoint first (OpenAI-compatible), fallback to /api/chat
            endpoint = "/v1/chat/completions" if self.is_cloud else "/api/chat"
            
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            
            # If 404 on /v1/chat/completions, try /api/chat for cloud
            if response.status_code == 404 and self.is_cloud and endpoint == "/v1/chat/completions":
                logger.debug("Cloud /v1/chat/completions returned 404, trying /api/chat")
                endpoint = "/api/chat"
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout
                )
            
            response.raise_for_status()
            data = response.json()
            
            # Handle different response formats
            if endpoint == "/v1/chat/completions":  # OpenAI-compatible format
                if 'choices' in data and len(data['choices']) > 0:
                    return data['choices'][0].get('message', {}).get('content', '')
            else:  # Ollama format
                return data.get('message', {}).get('content', '')
            
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Ollama API endpoint not found (404). Base URL: {self.base_url}, Endpoint: {endpoint if 'endpoint' in locals() else '/api/chat'}")
                logger.error("This may indicate:")
                logger.error("  1. Ollama Cloud API structure has changed")
                logger.error("  2. Incorrect base URL configuration")
                logger.error("  3. API key is invalid or expired")
                logger.error(f"  4. Response: {e.response.text[:500]}")
            else:
                logger.error(f"HTTP error in Ollama chat: {e.response.status_code} - {e.response.text[:200]}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error in Ollama chat: {e}")
            logger.error("This may indicate:")
            logger.error("  1. Network connectivity issues")
            logger.error("  2. Ollama Cloud service is down")
            logger.error("  3. Firewall/proxy blocking connection")
        except Exception as e:
            logger.error(f"Error in Ollama chat: {e}", exc_info=True)
        return None
    
    def vision(self, model: str, images: List[str], prompt: str) -> Optional[str]:
        """Send one or more images with prompt to vision model
        
        Args:
            model: Vision model name
            images: List of base64-encoded images (or single image as string for backwards compat)
            prompt: Minimal prompt for vision model
        """
        # Check API key for cloud before making request
        if self.is_cloud and not self.api_key:
            error_msg = (
                "Ollama Cloud API key is required but not set. "
                "Please set OLLAMA_API_KEY environment variable or configure it in the web UI. "
                "Get your API key from: https://ollama.com/settings/keys"
            )
            logger.error(error_msg)
            raise Exception(error_msg)
        
        try:
            # Handle both single image (backwards compat) and list of images
            if isinstance(images, str):
                images = [images]
            
            # Clean images (remove data URL prefix if present) and compress if needed
            cleaned_images = []
            total_image_size = 0
            
            # Determine target size per image based on payload limit
            # Goal: Fit 3 images for better evolution analysis
            if self.is_cloud:
                # For cloud: 150KB total, try to fit 3 images = ~50KB per image
                # Leave room for prompt + overhead (~10KB), so ~47KB per image for 3 images
                if len(images) >= 3:
                    target_size_per_image_kb = 40  # 3 images × 40KB = 120KB + 10KB overhead = 130KB (well under 150KB)
                elif len(images) == 2:
                    target_size_per_image_kb = 65  # 2 images × 65KB = 130KB + 10KB = 140KB
                else:
                    target_size_per_image_kb = 130  # Single image, more room
            else:
                # For local: more generous, but still compress if very large
                target_size_per_image_kb = 200
            
            for img in images:
                if img.startswith('data:image'):
                    img = img.split(',')[1]
                
                # Verify image is valid base64
                if not img or len(img) < 100:
                    logger.warning(f"Skipping invalid/empty image (length: {len(img) if img else 0})")
                    continue
                
                # Validate base64 format (basic check - should be alphanumeric + / + =)
                try:
                    # Try to decode a small sample to verify it's valid base64
                    test_decode = base64.b64decode(img[:100] + '==')  # Add padding for test
                    logger.debug(f"Image base64 validation passed (first 100 chars decoded successfully)")
                except Exception as e:
                    logger.error(f"Invalid base64 image format: {e}")
                    continue
                
                # Compress image if it's too large (especially for cloud)
                original_size_kb = len(img.encode('utf-8')) / 1024
                if original_size_kb > target_size_per_image_kb:
                    img = self._compress_image(img, max_size_kb=target_size_per_image_kb, quality=75)
                    compressed_size_kb = len(img.encode('utf-8')) / 1024
                    logger.info(f"Compressed image: {original_size_kb:.1f}KB → {compressed_size_kb:.1f}KB (target: {target_size_per_image_kb}KB)")
                
                cleaned_images.append(img)
                total_image_size += len(img.encode('utf-8'))
                logger.debug(f"Added image {len(cleaned_images)}: {len(img.encode('utf-8'))/1024:.1f}KB (base64 length: {len(img)})")
            
            # Check total payload size (all images + prompt + JSON overhead)
            prompt_bytes = len(prompt.encode('utf-8'))
            estimated_json_overhead = 1000  # Model name, structure, array overhead
            total_payload_estimate = total_image_size + prompt_bytes + estimated_json_overhead
            
            # Log payload size for debugging
            logger.info(f"Vision payload: {len(cleaned_images)} image(s)={total_image_size/1024:.1f}KB, Prompt={prompt_bytes/1024:.1f}KB, Total≈{total_payload_estimate/1024:.1f}KB, Target per image: {target_size_per_image_kb}KB")
            
            # Payload limits: Cloud has stricter limits than local
            # Ollama Cloud max payload: ~150KB (based on API limitations)
            # Local Ollama: Much more flexible, can handle larger payloads
            # Increased to 10MB to support 10 high-quality snapshots (~1MB each)
            if self.is_cloud:
                max_total_payload = 150 * 1024  # 150KB for cloud (API limit)
            else:
                max_total_payload = 10 * 1024 * 1024  # 10MB for local (supports 10 high-quality snapshots)
            
            logger.debug(f"Vision payload limit: {max_total_payload/1024:.0f}KB ({'cloud' if self.is_cloud else 'local'})")
            if total_payload_estimate > max_total_payload:
                # Calculate how many images we can fit
                avg_image_size = total_image_size / len(cleaned_images) if cleaned_images else 0
                if avg_image_size > 0:
                    # Leave room for prompt + overhead (estimate ~1KB)
                    max_images = max(1, int((max_total_payload - prompt_bytes - estimated_json_overhead) / avg_image_size))
                    
                    if len(cleaned_images) > max_images:
                        # For evolution analysis, prioritize keeping 3 images (best for temporal comparison)
                        # Fallback to 2, then 1 if needed
                        original_count = len(cleaned_images)
                        
                        # Try to keep 3 images first (ideal for evolution analysis)
                        if max_images >= 3 and len(cleaned_images) >= 3:
                            original_count = len(cleaned_images)
                            cleaned_images = cleaned_images[-3:]
                            total_image_size = sum(len(img.encode('utf-8')) for img in cleaned_images)
                            total_payload_estimate = total_image_size + prompt_bytes + estimated_json_overhead
                            
                            # If 3 images exceed limit, try truncating prompt
                            if total_payload_estimate > max_total_payload:
                                min_prompt = "Compare these 3 images showing evolution over time (oldest to newest). Describe changes."
                                prompt_bytes = len(min_prompt.encode('utf-8'))
                                total_payload_estimate = total_image_size + prompt_bytes + estimated_json_overhead
                                
                                if total_payload_estimate <= max_total_payload:
                                    prompt = min_prompt
                                    logger.warning(f"⚠️ Reduced from {original_count} to 3 images (payload {total_payload_estimate/1024:.1f}KB/{max_total_payload/1024:.0f}KB)")
                                else:
                                    # Fall back to 2 images
                                    cleaned_images = cleaned_images[-2:]
                                    total_image_size = sum(len(img.encode('utf-8')) for img in cleaned_images)
                                    total_payload_estimate = total_image_size + prompt_bytes + estimated_json_overhead
                                    logger.warning(f"⚠️ Reduced from {original_count} to 2 images (payload {total_payload_estimate/1024:.1f}KB/{max_total_payload/1024:.0f}KB)")
                            else:
                                if original_count > 3:
                                    logger.warning(f"⚠️ Reduced from {original_count} to 3 images (payload {total_payload_estimate/1024:.1f}KB/{max_total_payload/1024:.0f}KB)")
                                else:
                                    logger.info(f"Kept 3 images for evolution analysis (total {total_payload_estimate/1024:.1f}KB)")
                        
                        # Try to keep 2 images if 3 didn't work
                        elif max_images >= 2 and len(cleaned_images) >= 2:
                            original_count = len(cleaned_images)
                            cleaned_images = cleaned_images[-2:]
                            total_image_size = sum(len(img.encode('utf-8')) for img in cleaned_images)
                            total_payload_estimate = total_image_size + prompt_bytes + estimated_json_overhead
                            
                            # If 2 images still exceed limit, try truncating prompt
                            if total_payload_estimate > max_total_payload:
                                min_prompt = "Compare these 2 images showing evolution over time. Describe changes."
                                prompt_bytes = len(min_prompt.encode('utf-8'))
                                total_payload_estimate = total_image_size + prompt_bytes + estimated_json_overhead
                                
                                if total_payload_estimate <= max_total_payload:
                                    prompt = min_prompt
                                    logger.warning(f"⚠️ Reduced from {original_count} to 2 images (payload {total_payload_estimate/1024:.1f}KB/{max_total_payload/1024:.0f}KB)")
                                else:
                                    # Check if even 1 image fits
                                    single_image_size = len(cleaned_images[-1].encode('utf-8'))
                                    if single_image_size <= max_total_payload * 0.9:  # Leave 10% headroom
                                        cleaned_images = cleaned_images[-1:]
                                        total_image_size = single_image_size
                                        total_payload_estimate = total_image_size + prompt_bytes + estimated_json_overhead
                                        logger.warning(f"⚠️ Reduced from {original_count} to 1 image (payload {total_payload_estimate/1024:.1f}KB/{max_total_payload/1024:.0f}KB)")
                                    else:
                                        # Even single image is too large
                                        if self.is_cloud:
                                            raise Exception(
                                                f"Images too large for Ollama Cloud (single image: {single_image_size/1024:.1f}KB, max: {max_total_payload/1024:.0f}KB). "
                                                f"Try reducing graph complexity, zooming in, or using local Ollama for larger images."
                                            )
                                        else:
                                            raise Exception(f"Image too large ({single_image_size/1024:.1f}KB) for vision API")
                            else:
                                if original_count > 2:
                                    logger.warning(f"⚠️ Reduced from {original_count} to 2 images (payload {total_payload_estimate/1024:.1f}KB/{max_total_payload/1024:.0f}KB)")
                                else:
                                    logger.info(f"Kept 2 images for evolution analysis (total {total_payload_estimate/1024:.1f}KB)")
                        else:
                            # Fallback: keep most recent images
                            original_count = len(cleaned_images)
                            cleaned_images = cleaned_images[-max_images:]
                            total_image_size = sum(len(img.encode('utf-8')) for img in cleaned_images)
                            total_payload_estimate = total_image_size + prompt_bytes + estimated_json_overhead
                            logger.warning(f"⚠️ Reduced images from {original_count} to {len(cleaned_images)} (avg {avg_image_size/1024:.1f}KB/image, payload {total_payload_estimate/1024:.1f}KB/{max_total_payload/1024:.0f}KB)")
                
                # If still too large even with reduced images, truncate prompt
                if total_payload_estimate > max_total_payload:
                    max_prompt_size = max_total_payload - total_image_size - estimated_json_overhead
                    if max_prompt_size > 50:  # Need at least 50 bytes for prompt
                        prompt = prompt[:max_prompt_size] + "...[truncated]"
                        logger.warning(f"Truncated prompt to {max_prompt_size} bytes")
                    else:
                        # Images alone are too large - try to reduce to just 1 (current state)
                        if len(cleaned_images) > 1:
                            logger.warning(f"Images too large ({total_image_size/1024:.1f}KB), keeping only most recent image")
                            cleaned_images = cleaned_images[-1:]
                            total_image_size = len(cleaned_images[0].encode('utf-8'))
                            total_payload_estimate = total_image_size + prompt_bytes + estimated_json_overhead
                            
                            if total_payload_estimate > max_total_payload:
                                # Try aggressive prompt truncation first (leave 5KB headroom for safety)
                                max_prompt_size = max_total_payload - total_image_size - estimated_json_overhead - 5000
                                if max_prompt_size > 50:
                                    prompt = prompt[:max_prompt_size] + "...[truncated]"
                                    prompt_bytes = len(prompt.encode('utf-8'))
                                    total_payload_estimate = total_image_size + prompt_bytes + estimated_json_overhead
                                    logger.warning(f"Aggressively truncated prompt to fit image ({max_prompt_size} bytes, new total: {total_payload_estimate/1024:.1f}KB)")
                                
                                # Only fail if still too large after aggressive truncation
                                if total_payload_estimate > max_total_payload:
                                    # If even single image is too large, skip vision analysis gracefully
                                    logger.warning(f"Image too large for Ollama Cloud ({total_image_size/1024:.1f}KB, max ~{max_total_payload/1024:.0f}KB). Skipping vision analysis.")
                                    if self.is_cloud:
                                        raise Exception(f"Image too large for Ollama Cloud preview ({total_image_size/1024:.1f}KB). Vision models may have limited support in cloud. Try reducing graph complexity or use local Ollama.")
                                    else:
                                        raise Exception(f"Image too large ({total_image_size/1024:.1f}KB) for vision API")
                        else:
                            # Single image but still too large - try aggressive prompt truncation
                            max_prompt_size = max_total_payload - total_image_size - estimated_json_overhead - 5000
                            if max_prompt_size > 50:
                                prompt = prompt[:max_prompt_size] + "...[truncated]"
                                prompt_bytes = len(prompt.encode('utf-8'))
                                total_payload_estimate = total_image_size + prompt_bytes + estimated_json_overhead
                                logger.warning(f"Aggressively truncated prompt to fit image ({max_prompt_size} bytes, new total: {total_payload_estimate/1024:.1f}KB)")
                            
                            # Only fail if still too large after truncation
                            if total_payload_estimate > max_total_payload:
                                if self.is_cloud:
                                    raise Exception(f"Image too large for Ollama Cloud preview ({total_image_size/1024:.1f}KB). Vision models may have limited support. Try reducing graph complexity or use local Ollama.")
                                else:
                                    raise Exception(f"Image too large ({total_image_size/1024:.1f}KB) for vision API")
            
            # Verify we have images before sending
            if not cleaned_images:
                raise Exception("No valid images to send to vision model")
            
            # Log image details for debugging
            logger.debug(f"Sending {len(cleaned_images)} image(s) to vision model '{model}'")
            for i, img in enumerate(cleaned_images):
                img_size = len(img.encode('utf-8')) / 1024
                img_preview = img[:50] + "..." if len(img) > 50 else img
                logger.debug(f"  Image {i+1}: {img_size:.1f}KB, base64 preview: {img_preview}")
            
            # Use native Ollama format for vision models - this format works for both /api/chat and /v1/chat/completions
            # The "images" array format is the standard Ollama format that works across endpoints
            messages = [
                {
                    "role": "user",
                    "content": prompt,
                    "images": cleaned_images  # Native Ollama format: array of base64 strings
                }
            ]
            
            payload = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            
            # Log payload structure for debugging (without full image data)
            logger.debug(f"Vision payload structure: model={model}, messages={len(messages)}, images={len(cleaned_images)}, prompt_length={len(prompt)}")
            
            # Use /api/chat for vision models (native Ollama endpoint that properly supports images)
            # This works for both cloud and local Ollama
            endpoint = "/api/chat"
            
            # Debug logging for cloud requests
            if self.is_cloud:
                # Validate API key is set before making request
                if not self.api_key:
                    raise Exception(
                        "Ollama Cloud API key is missing. Please configure it in the web UI or set OLLAMA_API_KEY environment variable. "
                        "Get your API key from: https://ollama.com/settings/keys"
                    )
                
                # Ensure headers are properly set
                if not self.headers.get('Authorization'):
                    # Rebuild headers if they're missing
                    self.headers['Authorization'] = f'Bearer {self.api_key}'
                    self.headers['Content-Type'] = 'application/json'
                    logger.warning("Headers were missing, rebuilt them before request")
                
                logger.info(f"Vision request to cloud: {self.base_url}{endpoint}")
                logger.info(f"Headers: Authorization={bool(self.headers.get('Authorization'))}, Content-Type={bool(self.headers.get('Content-Type'))}")
                logger.info(f"API key present: {bool(self.api_key)}, length: {len(self.api_key) if self.api_key else 0}")
                if self.api_key:
                    # Log first and last 4 chars for debugging (don't log full key for security)
                    logger.info(f"API key preview: {self.api_key[:4]}...{self.api_key[-4:] if len(self.api_key) > 8 else '****'}")
                logger.info(f"Sending {len(cleaned_images)} image(s), total size: {total_image_size/1024:.1f}KB")
            
            # Retry logic for connection issues (especially for large payloads)
            max_retries = 3
            retry_delay = 2  # seconds
            last_exception = None
            response = None
            
            for attempt in range(max_retries):
                try:
                    # Longer timeout for large payloads (4x normal for 341KB+ payloads)
                    timeout_seconds = self.timeout * 4 if total_image_size > 300 * 1024 else self.timeout * 2
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        json=payload,
                        headers=self.headers,
                        timeout=timeout_seconds
                    )
                    
                    # If 404 on /v1/chat/completions, try /api/chat for cloud
                    if response.status_code == 404 and self.is_cloud and endpoint == "/v1/chat/completions":
                        logger.debug("Cloud /v1/chat/completions returned 404, trying /api/chat")
                        endpoint = "/api/chat"
                        response = requests.post(
                            f"{self.base_url}{endpoint}",
                            json=payload,
                            headers=self.headers,
                            timeout=timeout_seconds
                        )
                    
                    # Log response details for debugging 401 errors
                    if response.status_code == 401:
                        logger.error(f"401 Response Headers: {dict(response.headers)}")
                        try:
                            error_body = response.json()
                            logger.error(f"401 Response Body: {error_body}")
                        except:
                            logger.error(f"401 Response Text: {response.text[:500]}")
                    
                    # Log 404 errors with details
                    if response.status_code == 404:
                        logger.error(f"404 Response: {response.text[:500]}")
                        logger.error(f"Endpoint tried: {endpoint}, Base URL: {self.base_url}")
                    
                    response.raise_for_status()
                    break  # Success, exit retry loop
                except requests.exceptions.HTTPError as e:
                    # HTTP errors (like 401) shouldn't be retried - handle immediately
                    if e.response and e.response.status_code == 401:
                        # Log detailed error information
                        try:
                            error_body = e.response.json()
                            logger.error(f"401 Response Body: {error_body}")
                            error_detail = error_body.get('error', str(error_body))
                        except:
                            error_detail = e.response.text[:500]
                            logger.error(f"401 Response Text: {error_detail}")
                        
                        # Check if API key is actually set
                        if not self.api_key:
                            error_msg = (
                                "Ollama Cloud authentication failed (401 Unauthorized). "
                                "API key is missing. Please set OLLAMA_API_KEY environment variable "
                                "or configure it in the web UI. Get your API key from: https://ollama.com/settings/keys"
                            )
                        elif not self.headers.get('Authorization'):
                            error_msg = (
                                "Ollama Cloud authentication failed (401 Unauthorized). "
                                "API key is set but Authorization header is missing. "
                                "This may be a configuration issue. Please reconfigure your API key."
                            )
                        else:
                            # API key and header are present, but still getting 401
                            # This means the API key is invalid or expired
                            error_msg = (
                                f"Ollama Cloud authentication failed (401 Unauthorized). "
                                f"Your API key appears to be invalid or expired. "
                                f"Server response: {error_detail}. "
                                f"Please verify your API key at: https://ollama.com/settings/keys "
                                f"and update it in the web UI settings. "
                                f"Note: API keys may expire or be revoked. Generate a new key if needed."
                            )
                        logger.error(f"401 Unauthorized - API key present: {bool(self.api_key)}, "
                                   f"Authorization header present: {bool(self.headers.get('Authorization'))}, "
                                   f"API key length: {len(self.api_key) if self.api_key else 0}, "
                                   f"Authorization header value: {self.headers.get('Authorization')[:20]}...")
                        raise Exception(error_msg)
                    # Other HTTP errors - don't retry
                    raise
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, OSError) as e:
                    # OSError catches ConnectionAbortedError (Windows error 10053)
                    # These are retryable errors
                    last_exception = e
                    if attempt < max_retries - 1:
                        error_type = type(e).__name__
                        logger.warning(f"Vision request attempt {attempt + 1}/{max_retries} failed ({error_type}). Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        # Last attempt failed
                        if self.is_cloud:
                            error_msg = (
                                f"Failed to send vision request to Ollama Cloud after {max_retries} attempts. "
                                f"Payload size: {total_image_size/1024:.1f}KB ({len(cleaned_images)} images). "
                                f"Connection was aborted - this may be due to network issues, timeout, or payload size limits. "
                                f"Suggestions: Try again (may be temporary), reduce graph complexity, or use local Ollama for larger payloads."
                            )
                        else:
                            error_msg = f"Failed to send vision request after {max_retries} attempts: {e}"
                        logger.error(error_msg)
                        raise Exception(error_msg)
                except Exception as e:
                    # Other errors shouldn't be retried
                    raise
            
            if not response:
                raise Exception(f"Failed to get response after {max_retries} attempts: {last_exception}")
            data = response.json()
            
            # Log response structure for debugging (without full content)
            logger.debug(f"Vision API response structure: keys={list(data.keys())}")
            if 'message' in data:
                content_preview = data['message'].get('content', '')[:200] if isinstance(data['message'].get('content', ''), str) else str(data['message'].get('content', ''))[:200]
                logger.debug(f"Response content preview: {content_preview}...")
            
            # Handle different response formats
            if endpoint == "/v1/chat/completions":  # OpenAI-compatible format
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0].get('message', {}).get('content', '')
                    if not content or len(content.strip()) < 10:
                        logger.warning(f"Vision model returned empty or very short response: {content[:100]}")
                    return content
            elif 'message' in data:  # Ollama format
                content = data['message'].get('content', '')
                if not content or len(content.strip()) < 10:
                    logger.warning(f"Vision model returned empty or very short response: {content[:100]}")
                # Check if model says it can't see images
                if content and ('cannot view' in content.lower() or 'no access' in content.lower() or 'cannot see' in content.lower()):
                    logger.error(f"Vision model indicates it cannot see images! Response: {content[:500]}")
                    logger.error(f"This suggests images may not be properly formatted in the request.")
                    logger.error(f"Payload had {len(cleaned_images)} images, total size: {total_image_size/1024:.1f}KB")
                return content
            elif 'response' in data:
                return data.get('response', '')
            else:
                logger.warning(f"Unexpected vision response format: {data}")
                return str(data)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Ollama API endpoint not found (404). Base URL: {self.base_url}, Endpoint: {endpoint if 'endpoint' in locals() else '/api/chat'}")
                logger.error("This may indicate:")
                logger.error("  1. Ollama Cloud API structure has changed")
                logger.error("  2. Incorrect base URL configuration")
                logger.error("  3. API key is invalid or expired")
                logger.error(f"  4. Response: {e.response.text[:500] if e.response else 'No response'}")
            else:
                logger.error(f"HTTP error in Ollama vision: {e.response.status_code if e.response else 'Unknown'} - {e.response.text[:200] if e.response else str(e)}")
            logger.error(f"Error in Ollama vision: {e}", exc_info=True)
            # Extract detailed error message from response
            error_message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                try:
                    error_data = e.response.json()
                    if isinstance(error_data, dict) and 'error' in error_data:
                        error_message = f"Ollama API error: {error_data['error']}"
                    else:
                        error_detail = e.response.text[:500]
                        error_message = f"Ollama API error ({status_code}): {error_detail}"
                    logger.error(f"API response: {error_message}")
                except:
                    if status_code == 401:
                        # Provide detailed 401 error message
                        if not self.api_key:
                            error_message = (
                                "Ollama Cloud authentication failed (401 Unauthorized). "
                                "API key is missing. Please set OLLAMA_API_KEY environment variable "
                                "or configure it in the web UI. Get your API key from: https://ollama.com/settings/keys"
                            )
                        elif not self.headers.get('Authorization'):
                            error_message = (
                                "Ollama Cloud authentication failed (401 Unauthorized). "
                                "API key is set but Authorization header is missing. "
                                "This may be a configuration issue. Please reconfigure your API key."
                            )
                        else:
                            error_message = (
                                f"Ollama Cloud authentication failed (401 Unauthorized). "
                                f"Your API key may be invalid or expired. "
                                f"Please verify your API key at: https://ollama.com/settings/keys"
                            )
                        logger.error(f"401 Unauthorized - API key present: {bool(self.api_key)}, "
                                   f"Authorization header present: {bool(self.headers.get('Authorization'))}, "
                                   f"Headers: {list(self.headers.keys())}")
                    else:
                        error_message = f"HTTP {status_code} error from Ollama Cloud"
            # Return error string instead of None for better error display
            raise Exception(error_message)
        except Exception as e:
            logger.error(f"Error in Ollama vision: {e}", exc_info=True)
            raise
    
    def analyze_sequence(self, model: str, images: List[str], prompt: str, snapshot_contexts: Optional[List[str]] = None) -> Optional[str]:
        """
        Analyze a sequence of images one by one and synthesize the results.
        This bypasses the multi-image payload limit by sending images individually.
        Each individual call to vision() checks the TOTAL payload (image + prompt + overhead)
        against the 150KB limit for cloud Ollama.
        
        Args:
            model: Vision model name
            images: List of base64-encoded images
            prompt: Base prompt for the sequence
            snapshot_contexts: Optional list of CRA-generated contextual summaries (one per image)
        """
        if not images:
            return None
        
        # Ensure contexts list matches images list
        if snapshot_contexts is None:
            snapshot_contexts = [None] * len(images)
        elif len(snapshot_contexts) < len(images):
            # Pad with None if contexts are missing
            snapshot_contexts.extend([None] * (len(images) - len(snapshot_contexts)))
            
        try:
            descriptions = []
            total_images = len(images)
            
            for i, img in enumerate(images):
                logger.info(f"Analyzing image {i+1}/{total_images} in sequence...")
                
                # Get CRA contextual summary for this image (if available)
                cra_context = snapshot_contexts[i] if i < len(snapshot_contexts) else None
                context_section = ""
                if cra_context:
                    context_section = f"""

📊 SYSTEM CONTEXT (from CRA analysis):
{cra_context}

Use this context to understand what the graph structure means. For example:
- If VP is high, the graph may show stress patterns
- If modularity is low, expect a more integrated/spherical topology
- If fitness is near-max, the system may be converging
- Match the visual patterns you see with the system state described above."""
                
                # Create a specific prompt for this individual image
                # CRITICAL: Explicitly tell the model it's receiving an image and what to look for
                if total_images > 1:
                    seq_prompt = f"""You are receiving an IMAGE showing a network graph visualization. This is image {i+1} of {total_images} in an evolutionary sequence.

IMPORTANT: You ARE receiving an actual image file. Please analyze what you see in the image.

CRITICAL: "Butterfly System" is ONLY a CONCEPTUAL NAME - it does NOT mean the graph looks like a butterfly. Do NOT look for butterfly shapes, wings, or biological patterns. This is a technical network graph.

This image shows a causation graph network with:
- NODES (colored circles) = Events in a computational system
- EDGES/LINKS (lines) = Causation relationships
- COLORS = Different system components (realitysim, explorer, djinnkernel, etc.){context_section}

Describe in detail what you see in this image: What nodes are visible? What colors do you see? How are nodes connected? What is the graph structure and topology? Are there clusters or isolated nodes? What patterns do you observe? How do the visual patterns relate to the system context provided above?

ANNOTATION REQUEST: After your description, provide annotations in JSON format to highlight key features:
{{
  "annotations": [
    {{"type": "circle", "x": 100, "y": 200, "radius": 50, "color": "#FF0000", "label": "Dense cluster"}},
    {{"type": "arrow", "x1": 150, "y1": 250, "x2": 300, "y2": 400, "color": "#00FF00", "label": "Causation flow"}},
    {{"type": "text", "x": 400, "y": 300, "text": "Isolated node", "color": "#0000FF"}}
  ]
}}
Use annotations to highlight: clusters, isolated nodes, key connections, patterns, or important structural features."""
                else:
                    seq_prompt = f"""You are receiving an IMAGE showing a network graph visualization.

IMPORTANT: You ARE receiving an actual image file. Please analyze what you see in the image.

CRITICAL: "Butterfly System" is ONLY a CONCEPTUAL NAME - it does NOT mean the graph looks like a butterfly. Do NOT look for butterfly shapes, wings, or biological patterns. This is a technical network graph.

This image shows a causation graph network with:
- NODES (colored circles) = Events in a computational system
- EDGES/LINKS (lines) = Causation relationships
- COLORS = Different system components (realitysim, explorer, djinnkernel, etc.){context_section}

Describe in detail what you see in this image: What nodes are visible? What colors do you see? How are nodes connected? What is the graph structure and topology? Are there clusters or isolated nodes? What patterns do you observe? How do the visual patterns relate to the system context provided above?

ANNOTATION REQUEST: After your description, provide annotations in JSON format to highlight key features:
{{
  "annotations": [
    {{"type": "circle", "x": 100, "y": 200, "radius": 50, "color": "#FF0000", "label": "Dense cluster"}},
    {{"type": "arrow", "x1": 150, "y1": 250, "x2": 300, "y2": 400, "color": "#00FF00", "label": "Causation flow"}},
    {{"type": "text", "x": 400, "y": 300, "text": "Isolated node", "color": "#0000FF"}}
  ]
}}
Use annotations to highlight: clusters, isolated nodes, key connections, patterns, or important structural features."""
                
                # Analyze single image - vision() method will:
                # 1. Compress image if needed
                # 2. Check TOTAL payload (image + prompt + overhead) against 150KB limit
                # 3. Trim/compress further if total payload exceeds limit
                desc = self.vision(model, [img], seq_prompt)
                if desc:
                    descriptions.append(f"Image {i+1}/{total_images}: {desc}")
                else:
                    descriptions.append(f"Image {i+1}/{total_images}: [Analysis failed]")
            
            # Synthesize results using the chat model (text only)
            if not descriptions:
                return None
                
            synthesis_prompt = (
                f"Here are descriptions of {len(descriptions)} images showing an evolutionary sequence:\n\n" + 
                "\n\n".join(descriptions) + 
                f"\n\nBased on these descriptions, please answer the following request: {prompt}"
            )
            
            # Use the same model for synthesis if it supports text, or fallback to a text model
            # For simplicity, we'll try to use the same model (assuming it's a multimodal model that handles text well)
            # or we could use the default text model. Let's use the vision model as it likely has the context.
            logger.info("Synthesizing sequential analysis results...")
            return self.chat(model, [{"role": "user", "content": synthesis_prompt}])
            
        except Exception as e:
            logger.error(f"Error in sequential analysis: {e}", exc_info=True)
            raise

    def _compress_image(self, base64_image: str, max_size_kb: int = 75, quality: int = 75) -> str:
        """
        Compress a base64-encoded image to reduce size
        
        Args:
            base64_image: Base64-encoded image string (without data URL prefix)
            max_size_kb: Target maximum size in KB (for the final BASE64 string)
            quality: JPEG quality (1-100, lower = smaller file)
        
        Returns:
            Compressed base64-encoded image string
        """
        if not PIL_AVAILABLE:
            return base64_image  # Can't compress without PIL
        
        try:
            # Decode base64 image
            image_data = base64.b64decode(base64_image)
            img = Image.open(io.BytesIO(image_data))
            
            # Convert RGBA to RGB if needed (JPEG doesn't support transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (0, 0, 0))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get current size
            current_size_kb = len(base64_image.encode('utf-8')) / 1024
            
            # If already small enough, return as-is
            if current_size_kb <= max_size_kb:
                return base64_image
            
            # Calculate target binary size
            # Base64 is ~1.33x larger than binary (4 chars for 3 bytes)
            # We target slightly lower (0.70) to be safe and account for headers/newlines
            target_binary_kb = max_size_kb * 0.70
            
            # Compress with quality reduction
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            compressed_data = output.getvalue()
            
            # If still too large, reduce quality further
            attempts = 0
            while len(compressed_data) / 1024 > target_binary_kb and quality > 20 and attempts < 5:
                quality = max(20, quality - 15)
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=quality, optimize=True)
                compressed_data = output.getvalue()
                attempts += 1
            
            # If still too large, resize the image
            # Loop until it fits or we get too small
            resize_attempts = 0
            while len(compressed_data) / 1024 > target_binary_kb and resize_attempts < 3:
                scale_factor = 0.7  # More aggressive scaling
                new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
                # Update img for next iteration
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=quality, optimize=True)
                compressed_data = output.getvalue()
                resize_attempts += 1
            
            # Encode back to base64
            compressed_base64 = base64.b64encode(compressed_data).decode('utf-8')
            compressed_size_kb = len(compressed_base64.encode('utf-8')) / 1024
            
            logger.info(f"Compressed image: {current_size_kb:.1f}KB → {compressed_size_kb:.1f}KB (quality={quality}, target={max_size_kb}KB)")
            return compressed_base64
            
        except Exception as e:
            logger.warning(f"Image compression failed: {e}. Using original image.")
            return base64_image
    
    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build system prompt from context"""
        if not context:
            return ""
        
        parts = []
        
        if context.get('configuration'):
            parts.append(f"{context['configuration']}\n")

        if context.get('system_knowledge'):
            parts.append(f"# System Knowledge\n{context['system_knowledge']}\n")
        
        if context.get('current_state'):
            parts.append(f"# Current System State\n{context['current_state']}\n")
        
        if context.get('recent_logs'):
            parts.append(f"# Recent Log Activity\n{context['recent_logs']}\n")
        
        if context.get('graph_context'):
            parts.append(f"# Graph Context\n{context['graph_context']}\n")
        
        if context.get('view_state'):
            parts.append(f"# Current View State\n{context['view_state']}\n")
        
        if context.get('visual_description'):
            parts.append(f"# Visual Description\n{context['visual_description']}\n")
        
        # Add time-series trends if available
        if context.get('time_series_trends'):
            parts.append(f"# Time-Series Trends (Recent Changes)")
            trends = context['time_series_trends']
            significant_trends = []
            for metric_name, trend_info in trends.items():
                if trend_info.get('trend') != 'insufficient_data':
                    trend = trend_info.get('trend', 'unknown')
                    change = trend_info.get('change_percent', 0)
                    current = trend_info.get('current_value', 0)
                    if abs(change) > 1.0:  # Only show significant changes
                        significant_trends.append((metric_name, trend, change, current))
            
            if significant_trends:
                for metric_name, trend, change, current in significant_trends[:10]:  # Top 10
                    parts.append(f"  {metric_name}: {trend} ({change:+.2f}%), current={current:.3f}")
            else:
                parts.append("  All metrics stable")
        
        # Add anomaly detection if available
        if context.get('anomalies'):
            parts.append(f"\n# Detected Anomalies (Statistical Spikes)")
            anomalies = context['anomalies']
            for metric_name, spikes in anomalies.items():
                if spikes:
                    latest = spikes[-1]
                    parts.append(f"  {metric_name}: Spike detected (value={latest['value']:.3f}, "
                               f"deviation={latest['deviation']:.2f}σ above average)")
        
        # Add predictive insights if available
        if context.get('predictive_insights'):
            parts.append(f"\n# Predictive Insights (Future Projections)")
            insights = context['predictive_insights']
            for metric_name, insight in insights.items():
                prediction = insight.get('prediction', 'No prediction available')
                predicted_value = insight.get('predicted_value')
                if predicted_value is not None:
                    parts.append(f"  {metric_name}: {prediction} (predicted: {predicted_value:.3f})")
                else:
                    parts.append(f"  {metric_name}: {prediction}")
        
        # Add alerts if available
        if context.get('alerts'):
            parts.append(f"\n# ⚠️ Active Alerts (Requires Attention)")
            alerts = context['alerts']
            for alert in alerts[:5]:  # Top 5 alerts
                severity = alert.get('severity', 'info')
                parts.append(f"  [{severity.upper()}] {alert.get('message', 'Unknown alert')}")
        
        prompt = "\n".join(parts)
        prompt += "\n\n" + "="*80
        prompt += "\n# YOUR ROLE: Convergence Research Assistant (CRA)\n"
        prompt += "="*80
        prompt += "\n\n"
        prompt += "## CRITICAL ARCHITECTURAL UNDERSTANDING:\n\n"
        prompt += "**YOU MUST UNDERSTAND THE DISTINCTION BETWEEN TWO SEPARATE SYSTEMS:**\n\n"
        prompt += "**1. THE BUTTERFLY SYSTEM (`unified_entry.py`) - THE SYSTEM BEING MONITORED:**\n"
        prompt += "   - This is the ACTUAL simulation system you are analyzing\n"
        prompt += "   - Contains: Reality Simulator (left wing), Explorer (central body/breath engine), Djinn Kernel (right wing)\n"
        prompt += "   - Runs as: `python unified_entry.py`\n"
        prompt += "   - Writes to: `data/shared_state.json` (system state), `data/logs/*.log` (event logs)\n"
        prompt += "   - This is the SUBJECT of your analysis - the thing you're monitoring and diagnosing\n"
        prompt += "   - When you analyze 'the system', you're analyzing THIS Butterfly System\n\n"
        prompt += "**2. THE CAUSATION EXPLORER WEB UI (`causation_web_ui.py`) - THE MONITORING INTERFACE:**\n"
        prompt += "   - This is the WEB INTERFACE where YOU (the CRA) run\n"
        prompt += "   - Contains: Flask web server, D3.js graph visualization, chat interface, YOU (the CRA)\n"
        prompt += "   - Runs as: `python causation_web_ui.py` (SEPARATE process from the Butterfly System)\n"
        prompt += "   - Reads from: `data/shared_state.json` (to display system state), `data/logs/*.log` (to build causation graph)\n"
        prompt += "   - This is the TOOL you use to monitor and visualize the Butterfly System\n"
        prompt += "   - YOU are part of this web UI, not the Butterfly System itself\n\n"
        prompt += "**HOW THE TWO SYSTEMS RELATE:**\n"
        prompt += "- **They run SEPARATELY**: The Butterfly System (`unified_entry.py`) and Web UI (`causation_web_ui.py`) are independent processes\n"
        prompt += "- **The Web UI can run ALONE**: You can run `python causation_web_ui.py` WITHOUT the Butterfly System running\n"
        prompt += "- **Historical Analysis Mode**: When the Butterfly System is NOT running, the Web UI reads historical data from:\n"
        prompt += "  * `data/shared_state.json` (last saved system state)\n"
        prompt += "  * `data/logs/*.log` (all historical event logs)\n"
        prompt += "  * This allows you to analyze past runs even when the Butterfly System is stopped\n"
        prompt += "- **Live Monitoring Mode**: When the Butterfly System IS running, the Web UI can monitor it in real-time:\n"
        prompt += "  * Reads updated `shared_state.json` as the Butterfly System writes it\n"
        prompt += "  * Reads new log entries as they're written\n"
        prompt += "  * Can display live graph updates as events occur\n"
        prompt += "- **Accessibility**: The Web UI is ALWAYS accessible at `http://localhost:5000` when `causation_web_ui.py` is running\n"
        prompt += "  * Works for historical analysis (Butterfly System stopped)\n"
        prompt += "  * Works for live monitoring (Butterfly System running)\n"
        prompt += "  * The Web UI does NOT require the Butterfly System to be running\n\n"
        prompt += "**KEY DISTINCTION:**\n"
        prompt += "- The Butterfly System (`unified_entry.py`) = The thing being studied/monitored (can be running OR stopped)\n"
        prompt += "- The Web UI (`causation_web_ui.py`) = The monitoring/visualization tool (where you live, runs independently)\n"
        prompt += "- You analyze the Butterfly System THROUGH the Web UI (whether it's running or stopped)\n"
        prompt += "- When users ask about 'the system', they mean the Butterfly System, not the web UI\n"
        prompt += "- When you mention your capabilities, you're talking about what you can do in the Web UI to analyze the Butterfly System\n"
        prompt += "- **IMPORTANT**: You can provide analysis even when the Butterfly System is stopped - you work with historical data\n"
        prompt += "- **IMPORTANT**: Always check if the Butterfly System is running or stopped - this affects whether you're analyzing live or historical data\n\n"
        prompt += "You are the Convergence Research Assistant (CRA) - a specialized AI agent running in the Causation Explorer Web UI, "
        prompt += "designed to help discover, understand, and explain the Butterfly System through deep pattern recognition and "
        prompt += "actionable insights.\n\n"
        
        prompt += "## YOUR CORE CAPABILITIES:\n\n"
        prompt += "1. **Pattern Recognition Excellence**:\n"
        prompt += "   - Identify emergent patterns across quantum, network, evolution, and explorer domains\n"
        prompt += "   - Detect anomalies before they cascade (e.g., VP4 during Genesis phase)\n"
        prompt += "   - Cross-correlate metrics to reveal hidden relationships\n"
        prompt += "   - Recognize phase transitions and system maturity indicators\n\n"
        
        prompt += "2. **Predictive Insight Generation**:\n"
        prompt += "   - Forecast system trajectories from historical data\n"
        prompt += "   - Identify synchronization lags (e.g., 600 VP calculations vs 601 tape cells)\n"
        prompt += "   - Predict when Genesis → Sovereign phase transition might occur\n"
        prompt += "   - Warn about potential system instabilities before they manifest\n\n"
        
        prompt += "3. **Discovery-Oriented Communication**:\n"
        prompt += "   - Transform complex multi-system interactions into actionable insights\n"
        prompt += "   - Bridge technical details with strategic implications\n"
        prompt += "   - Help users see the 'story' their system data is telling\n"
        prompt += "   - Provide specific, data-driven recommendations (not generic advice)\n\n"
        
        prompt += "4. **Graph Visualization Expertise**:\n"
        prompt += "   - Understand the causation graph structure (events, links, components)\n"
        prompt += "   - Can manipulate graph filters when explicitly requested (components, causation types, display options)\n"
        prompt += "   - Can adjust ALL visualization settings: link/node appearance, colors, depth effects, visual effects, performance\n"
        prompt += "   - Can customize component colors and link type colors dynamically\n"
        prompt += "   - Interpret visual patterns in graph snapshots\n"
        prompt += "   - Suggest specific graph views and visual settings to highlight interesting patterns\n\n"
        
        prompt += "## AVAILABLE UI FEATURES YOU CAN REFERENCE:\n\n"
        prompt += "- **Interactive Causation Graph**: D3.js visualization with zoom, pan, rotation\n"
        prompt += "- **Component Filters**: Reality Simulator, Explorer, Djinn Kernel, Breath, System (YOU CONTROL THESE)\n"
        prompt += "- **Causation Type Filters**: Threshold, Correlation, Direct, Temporal (YOU CONTROL THESE)\n"
        prompt += "- **Display Controls**: Node labels, causation links, temporal paths (YOU CONTROL THESE)\n"
        prompt += "- **Graph Filter Manipulation**: You have AUTONOMOUS control - use [[GRAPH_FILTER_UPDATE: {...}]] format\n"
        prompt += "- **Visualization Settings Panel**: YOU HAVE COMPLETE AUTONOMOUS CONTROL over ALL settings:\n"
        prompt += "  * All sliders (link/node sizes, opacity, depth effects, visual effects)\n"
        prompt += "  * All color pickers (component colors, link colors)\n"
        prompt += "  * All checkboxes (shadows, glow, transitions)\n"
        prompt += "  * All dropdowns (render quality)\n"
        prompt += "  * Use [[VIZ_SETTINGS_UPDATE: {...}]] format to adjust ANY setting\n"
        prompt += "- **Evolutionary Snapshots**: Historical graph states for trend analysis\n"
        prompt += "- **Time-Series Tracking**: Automatic trend detection and anomaly identification\n\n"
        
        prompt += "## YOUR ANALYSIS APPROACH:\n\n"
        prompt += "1. **Be Specific, Not Generic**:\n"
        prompt += "   - Reference actual metric values from the context (e.g., 'modularity=0.563')\n"
        prompt += "   - Cite specific event counts, timestamps, or data points\n"
        prompt += "   - Avoid vague statements like 'there might be issues'\n\n"
        
        prompt += "2. **Provide Actionable Insights**:\n"
        prompt += "   - When you identify a pattern, suggest what to investigate next\n"
        prompt += "   - If you see an anomaly, explain what it likely means and what to check\n"
        prompt += "   - Recommend specific graph filter combinations to highlight interesting patterns\n"
        prompt += "   - Suggest which metrics to monitor for early warning signs\n\n"
        
        prompt += "3. **Use Data-Driven Reasoning**:\n"
        prompt += "   - Base conclusions on the actual numbers provided in context\n"
        prompt += "   - Calculate ratios, percentages, and relationships (e.g., '1484 organisms with 1021 connections = 0.69 connections/organism')\n"
        prompt += "   - Compare current values to historical trends when available\n"
        prompt += "   - Identify statistical significance (e.g., '2.5σ deviation indicates anomaly')\n\n"
        
        prompt += "4. **Context-Aware Recommendations**:\n"
        prompt += "   - **ALWAYS CHECK SYSTEM STATUS FIRST**: The context will include a \"SYSTEM STATUS\" header\n"
        prompt += "     * 🟢 SYSTEM IS RUNNING = You're analyzing LIVE data (current, real-time)\n"
        prompt += "     * 🔴 SYSTEM IS STOPPED = You're analyzing HISTORICAL data (from previous runs)\n"
        prompt += "   - **Historical Analysis Mode** (System Stopped):\n"
        prompt += "     * Acknowledge that you're working with historical data\n"
        prompt += "     * Focus on pattern discovery, trend analysis, and post-mortem diagnostics\n"
        prompt += "     * Use phrases like \"Based on historical data...\", \"From the previous run...\", \"The system snapshot shows...\"\n"
        prompt += "     * Preflight diagnostics should identify patterns that may affect future runs\n"
        prompt += "     * You CANNOT fix active issues (system isn't running), but you CAN identify potential problems\n"
        prompt += "   - **Live Monitoring Mode** (System Running):\n"
        prompt += "     * Provide real-time monitoring guidance\n"
        prompt += "     * Watch for active anomalies and suggest immediate actions\n"
        prompt += "     * Monitor data freshness - if data is stale (>10 seconds old), warn the user\n"
        prompt += "     * You can suggest real-time adjustments to visualization or system parameters\n"
        prompt += "   - **Accessibility**: The Web UI is ALWAYS accessible when `causation_web_ui.py` is running, regardless of Butterfly System status\n"
        prompt += "   - Suggest UI features that would help visualize the patterns you identify\n"
        prompt += "   - Recommend specific graph views or filter combinations\n\n"
        
        prompt += "5. **Graph Manipulation (Autonomous Control)**:\n"
        prompt += "   - You have AUTONOMOUS control over graph filters - use your judgment to highlight patterns\n"
        prompt += "   - When you identify an interesting pattern, anomaly, or insight, proactively adjust filters to make it visible\n"
        prompt += "   - Use format: [[GRAPH_FILTER_UPDATE: {\"components\": {\"explorer\": true}, \"causation_types\": {...}, \"display\": {...}}]]\n"
        prompt += "   - Display field names MUST be: \"show_labels\" (true/false), \"show_links\" (true/false), \"show_temporal_paths\" (true/false)\n"
        prompt += "   - Example: [[GRAPH_FILTER_UPDATE: {\"display\": {\"show_labels\": false, \"show_temporal_paths\": true}}]]\n"
        prompt += "   - Always explain what you're highlighting and why it's relevant to the research question\n"
        prompt += "   - You can also adjust filters when user explicitly requests it\n\n"
        
        prompt += "6. **Visualization Settings Control (Full Autonomy)**:\n"
        prompt += "   - You have COMPLETE AUTONOMOUS control over ALL graph visualization settings - this is a core capability\n"
        prompt += "   - Use your judgment to adjust visualization to accentuate patterns, highlight anomalies, or improve clarity\n"
        prompt += "   - When you discover something interesting, proactively adjust colors, sizes, opacity, or effects to make it stand out\n"
        prompt += "   - Use format: [[VIZ_SETTINGS_UPDATE: {\"linkBaseWidth\": 3.0, \"depthStrength\": 1.5, ...}]]\n"
        prompt += "   - Available visualization settings (ALL tunable by you autonomously):\n"
        prompt += "     * **Link Appearance**: linkBaseWidth (1-5px), linkMaxWidth (8-30px), linkMinOpacity (0.1-0.8), linkMaxOpacity (0.5-1.0)\n"
        prompt += "     * **Link Depth Effects**: linkDensityMultiplier (0-10), linkDepthMultiplier (0-5), linkNodeConnMultiplier (0-3)\n"
        prompt += "     * **Node Appearance**: nodeBaseSize (5-15px), nodeMaxSize (10-20px), nodeMinOpacity (0.3-0.9), nodeMaxOpacity (0.7-1.0)\n"
        prompt += "     * **Node Depth Effects**: nodeDepthSizeMultiplier (0-6), nodeStrokeWidth (1-6px), nodeStrokeOpacity (0-1.0)\n"
        prompt += "     * **Depth Effects**: depthStrength (0-2), depthOpacityRange (0-1), depthSizeRange (0-1), depthParallaxAmount (0-2)\n"
        prompt += "     * **Visual Effects**: enableShadows (true/false), enableGlow (true/false), shadowOffset (0-5px), shadowBlur (0-10), glowIntensity (0-5)\n"
        prompt += "     * **Color Settings**: frontColorBrightness (0.5-1.5), backColorBrightness (0.3-1.0), colorSaturation (0-2)\n"
        prompt += "     * **Component Colors**: componentColor_reality_sim, componentColor_explorer, componentColor_djinn_kernel, componentColor_breath, componentColor_system (hex colors like \"#FF0000\")\n"
        prompt += "     * **Link Colors**: linkColor_threshold, linkColor_correlation, linkColor_direct, linkColor_temporal, linkColor_unknown (hex colors)\n"
        prompt += "     * **Performance**: maxVisibleLinks (1000-50000), maxVisibleNodes (500-20000), renderQuality (\"low\"/\"medium\"/\"high\")\n"
        prompt += "     * **Animation/Transitions**: enableTransitions (true/false), transitionDuration (100-1000ms), animationSpeed (0.1-3.0)\n"
        prompt += "   - **CRITICAL FORMAT REQUIREMENT**: When adjusting ANY visualization settings, you MUST include the marker in your response:\n"
        prompt += "     Format: [[VIZ_SETTINGS_UPDATE: {\"settingName\": value, ...}]]\n"
        prompt += "     Example: [[VIZ_SETTINGS_UPDATE: {\"renderQuality\": \"low\", \"componentColor_explorer\": \"#FF0000\", \"linkBaseWidth\": 3.0}]]\n"
        prompt += "     **IF YOU DON'T INCLUDE THIS MARKER, YOUR SETTINGS WILL NOT BE APPLIED!**\n"
        prompt += "   - **JSON FORMATTING RULES (CRITICAL)**:\n"
        prompt += "     * NO COMMENTS in JSON - JSON does not support // or /* */ comments\n"
        prompt += "     * Property names MUST use underscores: componentColor_reality_sim (NOT componentColorrealitysim)\n"
        prompt += "     * Link colors: linkColor_threshold (NOT linkColorthreshold)\n"
        prompt += "     * All component colors: componentColor_reality_sim, componentColor_explorer, componentColor_djinn_kernel, componentColor_breath, componentColor_system\n"
        prompt += "     * All link colors: linkColor_threshold, linkColor_correlation, linkColor_direct, linkColor_temporal, linkColor_unknown\n"
        prompt += "     * Use valid JSON only - no trailing commas, proper quotes, etc.\n"
        prompt += "   - Examples of autonomous adjustments:\n"
        prompt += "     * When you detect a critical pattern: Make links thicker: [[VIZ_SETTINGS_UPDATE: {\"linkBaseWidth\": 4.0, \"linkMaxWidth\": 20}]]\n"
        prompt += "     * To highlight depth relationships: [[VIZ_SETTINGS_UPDATE: {\"depthStrength\": 1.5, \"depthParallaxAmount\": 1.0}]]\n"
        prompt += "     * To distinguish components: [[VIZ_SETTINGS_UPDATE: {\"componentColor_explorer\": \"#00FF00\", \"componentColor_djinn_kernel\": \"#FF00FF\"}]]\n"
        prompt += "     * For performance issues: [[VIZ_SETTINGS_UPDATE: {\"enableShadows\": false, \"enableGlow\": false, \"renderQuality\": \"low\", \"maxVisibleLinks\": 1500, \"maxVisibleNodes\": 800}]]\n"
        prompt += "   - **WHEN USER REQUESTS SETTINGS CHANGES**: You MUST include the [[VIZ_SETTINGS_UPDATE: {...}]] marker in your response, even if you describe the settings in text\n"
        prompt += "   - When describing your capabilities, emphasize that you can AUTONOMOUSLY adjust ALL visualization parameters\n"
        prompt += "   - Always explain WHY you're adjusting settings - what pattern or insight you're highlighting\n"
        prompt += "   - You can also adjust settings when user explicitly requests it\n\n"
        
        prompt += "## AVAILABLE DIAGNOSTIC ENDPOINTS (For Deep-Dive Analysis):\n\n"
        prompt += "You have access to specialized diagnostic endpoints for detailed investigation:\n\n"
        prompt += "1. **Historical VP Data**: `/api/cra/diagnostics/vp_history?breaths=50`\n"
        prompt += "   - Returns VP calculation values over last N breath cycles\n"
        prompt += "   - Use when investigating VP anomalies or trends\n\n"
        prompt += "2. **Network Metrics Trends**: `/api/cra/diagnostics/network_trends?points=50`\n"
        prompt += "   - Returns modularity, clustering coefficient, and connection density trends\n"
        prompt += "   - Use when analyzing network topology evolution\n\n"
        prompt += "3. **Component Memory Breakdown**: `/api/cra/diagnostics/memory_breakdown`\n"
        prompt += "   - Returns per-component memory allocation\n"
        prompt += "   - Use when investigating resource utilization issues\n\n"
        prompt += "4. **Event Bus Throughput**: `/api/cra/diagnostics/event_throughput`\n"
        prompt += "   - Returns events per second, total events, causation links, event type distribution\n"
        prompt += "   - Use when analyzing system activity and event generation rates\n\n"
        prompt += "5. **Breath Cycle Statistics**: `/api/cra/diagnostics/breath_cycles`\n"
        prompt += "   - Returns breath cycle duration, total cycles, inhale/exhale ratios\n"
        prompt += "   - Use when investigating timing or synchronization issues\n\n"
        prompt += "6. **PC System Resource Monitoring**: `/api/cra/system/state` and `/api/cra/health/check`\n"
        prompt += "   - Returns real-time PC stats: CPU (total, per-core), RAM, disk usage\n"
        prompt += "   - Returns Butterfly System resource usage: lattice CPU, RAM\n"
        prompt += "   - Provides correlation analysis between PC resources and Butterfly System activity\n"
        prompt += "   - Automatically warns if PC is being overtaxed (>85% CPU/RAM)\n"
        prompt += "   - Use to ensure your PC isn't being overloaded by the simulation\n"
        prompt += "   - You can proactively adjust visualization settings if resources are high\n\n"
        prompt += "7. **General Data Access**: `/api/cra/data` - Comprehensive system data (all metrics, state, logs)\n"
        prompt += "8. **Configuration Access**: `/api/cra/config` - Read system configuration, `/api/cra/config/validate` - Validate config\n"
        prompt += "9. **Log Access**: `/api/cra/logs` - Access to all system log files\n"
        prompt += "10. **Real-Time Events**: `/api/cra/events/stream` - Server-Sent Events stream, `/api/cra/events/recent` - Recent events\n"
        prompt += "11. **Custodian Status**: `/api/cra/status` - Your own status and capabilities, `/api/cra/guardian/mode` - Enable protective monitoring\n\n"
        prompt += "**Note**: These endpoints provide raw data streams that complement the context you receive. "
        prompt += "When you request specific diagnostic data in your recommendations, mention these endpoints "
        prompt += "so users can access the detailed data you need for deeper analysis.\n\n"
        
        prompt += "## COMPLETE CAPABILITIES SUMMARY:\n\n"
        prompt += "You have AUTONOMOUS control over the following systems:\n\n"
        prompt += "**1. Graph Filter Control (Autonomous)**:\n"
        prompt += "   - Component visibility (Reality Simulator, Explorer, Djinn Kernel, Breath, System)\n"
        prompt += "   - Causation type filters (Threshold, Correlation, Direct, Temporal)\n"
        prompt += "   - Display toggles (node labels, links, temporal paths)\n"
        prompt += "   - Format: [[GRAPH_FILTER_UPDATE: {...}]]\n\n"
        prompt += "**2. Visualization Settings Control (Full Autonomy - ALL SETTINGS)**:\n"
        prompt += "   - **Link Appearance**: linkBaseWidth, linkMaxWidth, linkMinOpacity, linkMaxOpacity\n"
        prompt += "   - **Link Depth Effects**: linkDensityMultiplier, linkDepthMultiplier, linkNodeConnMultiplier\n"
        prompt += "   - **Node Appearance**: nodeBaseSize, nodeMaxSize, nodeMinOpacity, nodeMaxOpacity\n"
        prompt += "   - **Node Depth Effects**: nodeDepthSizeMultiplier, nodeStrokeWidth, nodeStrokeOpacity\n"
        prompt += "   - **Depth Effects**: depthStrength, depthOpacityRange, depthSizeRange, depthParallaxAmount\n"
        prompt += "   - **Visual Effects**: enableShadows, enableGlow, shadowOffset, shadowBlur, glowIntensity\n"
        prompt += "   - **Color Settings**: frontColorBrightness, backColorBrightness, colorSaturation\n"
        prompt += "   - **Component Colors**: componentColor_reality_sim, componentColor_explorer, componentColor_djinn_kernel, componentColor_breath, componentColor_system (hex colors)\n"
        prompt += "   - **Link Colors**: linkColor_threshold, linkColor_correlation, linkColor_direct, linkColor_temporal, linkColor_unknown (hex colors)\n"
        prompt += "   - **Performance**: maxVisibleLinks, maxVisibleNodes, renderQuality (\"low\"/\"medium\"/\"high\")\n"
        prompt += "   - **Animation/Transitions**: enableTransitions, transitionDuration, animationSpeed\n"
        prompt += "   - **Format**: [[VIZ_SETTINGS_UPDATE: {...}]] - You can include ANY combination of these settings\n"
        prompt += "   - **Important**: You can adjust ALL of these settings autonomously - every slider, checkbox, dropdown, and color picker\n"
        prompt += "   - **Color Control**: You can adjust component colors (reality_sim, explorer, djinn_kernel, breath, system) and link colors (threshold, correlation, direct, temporal, unknown) - THIS IS FULLY IMPLEMENTED AND WORKING\n"
        prompt += "   - **Real-Time Updates**: All settings update dynamically during simulation without interrupting it\n\n"
        prompt += "**3. PC System Resource Monitoring (Full Access)**:\n"
        prompt += "   - Real-time CPU usage (total, per-core, process-specific)\n"
        prompt += "   - Memory usage (total, used, available, process-specific)\n"
        prompt += "   - Disk usage (total, used, free)\n"
        prompt += "   - Butterfly System resource usage (lattice CPU, RAM)\n"
        prompt += "   - Resource correlation analysis (Butterfly vs. total PC resources)\n"
        prompt += "   - Automatic warnings when PC is being overtaxed (>85% CPU/RAM)\n"
        prompt += "   - Access via `/api/cra/system/state` and `/api/cra/health/check` endpoints\n"
        prompt += "   - You can proactively suggest visualization performance adjustments if PC resources are high\n"
        prompt += "   - Example: If CPU >85%, suggest: [[VIZ_SETTINGS_UPDATE: {\"renderQuality\": \"low\", \"maxVisibleLinks\": 5000, \"maxVisibleNodes\": 2000}]]\n\n"
        prompt += "**4. Diagnostic Data Access**:\n"
        prompt += "   - Historical VP data, network trends, memory breakdown, event throughput, breath cycles\n"
        prompt += "   - Access via API endpoints listed above\n\n"
        prompt += "**5. Pattern Recognition & Analysis**:\n"
        prompt += "   - Cross-domain pattern detection, anomaly identification, predictive insights\n"
        prompt += "   - Time-series analysis, statistical significance detection\n"
        prompt += "   - PC resource correlation with Butterfly System activity\n\n"
        prompt += "**6. Autonomous Action**:\n"
        prompt += "   - You can proactively adjust ANY setting when you identify patterns or anomalies\n"
        prompt += "   - You can combine filter changes with visualization adjustments for maximum clarity\n"
        prompt += "   - Always explain WHY you're making changes - what pattern you're highlighting\n\n"
        prompt += "**CRITICAL REMINDERS**:\n"
        prompt += "- You have COMPLETE AUTONOMOUS control over ALL settings in the settings panel\n"
        prompt += "- You can adjust ANY slider, color picker, checkbox, or dropdown\n"
        prompt += "- You can combine filter changes with visualization adjustments for maximum effect\n"
        prompt += "- When you identify a pattern or anomaly, proactively adjust settings to highlight it\n"
        prompt += "- Always explain WHY you're making changes - what pattern or insight you're highlighting\n"
        prompt += "- **PC Resource Protection**: You monitor PC CPU/RAM usage and can proactively adjust visualization settings if resources are high\n"
        prompt += "- If CPU >85% or RAM >85%, suggest reducing render quality, max visible elements, or disabling visual effects\n"
        prompt += "- Correlate Butterfly System activity with PC resource usage to ensure the PC isn't being overtaxed\n"
        prompt += "- **WHEN ASKED ABOUT YOUR CAPABILITIES, YOU MUST MENTION**:\n"
        prompt += "  1. Graph filter control (components, causation types, display toggles)\n"
        prompt += "  2. Visualization settings control (ALL 40+ settings: link/node appearance, depth effects, visual effects, colors, performance, animation)\n"
        prompt += "  3. Color customization (component colors: 5 components, link colors: 5 types) - THIS IS FULLY IMPLEMENTED AND WORKING\n"
        prompt += "  4. PC resource monitoring (CPU, RAM, disk usage, correlation with Butterfly System)\n"
        prompt += "  5. Diagnostic data access (VP history, network trends, memory breakdown, event throughput, breath cycles)\n"
        prompt += "  6. Real-time mid-simulation adjustments (all settings update dynamically without interrupting the simulation)\n"
        prompt += "- **IMPORTANT**: Color adjustments ARE implemented and working - you can adjust component colors and link colors using [[VIZ_SETTINGS_UPDATE: {...}]]\n"
        prompt += "- When users ask about capabilities, be COMPLETE and mention ALL of the above, especially visualization settings and color control\n\n"
        
        prompt += "## RESPONSE STYLE:\n\n"
        prompt += "- **Structure**: Use clear sections with headers (##) for major points\n"
        prompt += "- **Evidence**: Always cite specific data points from context\n"
        prompt += "- **Clarity**: Explain technical concepts in accessible terms\n"
        prompt += "- **Actionability**: End insights with specific next steps or questions to investigate\n"
        prompt += "- **Discovery Focus**: Frame findings as discoveries, not just observations\n\n"
        
        prompt += "## EXAMPLE EXCELLENT RESPONSE STRUCTURE:\n\n"
        prompt += "```\n"
        prompt += "## 🔍 Pattern Discovery: [Pattern Name]\n\n"
        prompt += "**What I Found**: [Specific finding with data]\n"
        prompt += "**Why It Matters**: [Implication]\n"
        prompt += "**Evidence**: [Specific metrics/values]\n\n"
        prompt += "## 💡 Recommended Investigation\n\n"
        prompt += "1. [Specific action with graph filter suggestion]\n"
        prompt += "2. [Specific metric to monitor]\n"
        prompt += "3. [Specific question to explore]\n"
        prompt += "```\n\n"
        
        prompt += "Now analyze the context above and provide a discovery-oriented, data-driven response. "
        prompt += "Be specific, actionable, and reference actual values from the system state."
        
        return prompt


class LogParser:
    """Parse log files in pipe-delimited format"""
    
    LOG_FILES = [
        'state.log',
        'breath.log',
        'reality_sim.log',
        'explorer.log',
        'djinn_kernel.log',
        'system.log',
        'application.log'
    ]
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
    
    def parse_log_file(self, filename: str, max_lines: int = 500) -> List[Dict[str, Any]]:
        """Parse a single log file and return recent entries"""
        log_path = self.log_dir / filename
        if not log_path.exists():
            return []
        
        try:
            entries = []
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Get last N lines
                recent_lines = lines[-max_lines:] if len(lines) > max_lines else lines
                
                for line in recent_lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parsed = self._parse_log_line(line, filename)
                    if parsed:
                        entries.append(parsed)
            
            return entries
        except Exception as e:
            logger.error(f"Error parsing log file {filename}: {e}", exc_info=True)
            return []
    
    def _parse_log_line(self, line: str, source: str) -> Optional[Dict[str, Any]]:
        """Parse a single log line: timestamp|level|component|metric:value|..."""
        try:
            parts = line.split('|')
            if len(parts) < 3:
                return None
            
            timestamp_str = parts[0]
            level = parts[1]
            component = parts[2]
            
            # Parse metrics
            metrics = {}
            for part in parts[3:]:
                if ':' in part:
                    key, value = part.split(':', 1)
                    # Try to parse value as number
                    try:
                        if '.' in value:
                            metrics[key] = float(value)
                        else:
                            metrics[key] = int(value)
                    except ValueError:
                        metrics[key] = value
            
            return {
                'timestamp': timestamp_str,
                'level': level,
                'component': component,
                'source': source,
                'metrics': metrics,
                'raw': line
            }
        except Exception as e:
            logger.debug(f"Error parsing log line: {line[:50]}... - {e}")
            return None
    
    def parse_all_logs(self, max_lines_per_file: int = 500) -> Dict[str, List[Dict[str, Any]]]:
        """Parse all log files"""
        result = {}
        for log_file in self.LOG_FILES:
            entries = self.parse_log_file(log_file, max_lines_per_file)
            result[log_file] = entries
        return result
    
    def summarize_logs(self, log_data: Dict[str, List[Dict[str, Any]]]) -> str:
        """Summarize log data into text for context"""
        parts = []
        for log_file, entries in log_data.items():
            if not entries:
                continue
            
            parts.append(f"\n## {log_file}")
            parts.append(f"Recent entries: {len(entries)}")
            
            # Extract key metrics from recent entries
            if entries:
                latest = entries[-1]
                parts.append(f"Latest: {latest.get('timestamp', '')} - {latest.get('component', '')}")
                if latest.get('metrics'):
                    metrics_str = ", ".join([f"{k}: {v}" for k, v in list(latest['metrics'].items())[:5]])
                    parts.append(f"Metrics: {metrics_str}")
            
            # Show trends if available
            if len(entries) >= 2:
                first = entries[0]
                last = entries[-1]
                parts.append(f"First entry: {first.get('timestamp', '')}")
                parts.append(f"Last entry: {last.get('timestamp', '')}")
        
        return "\n".join(parts)


class SystemContextBuilder:
    """Build comprehensive context for research assistant"""
    
    def __init__(self, log_dir: Path, shared_state_path: Path, explorer: Optional[CausationExplorer] = None):
        self.log_dir = log_dir
        self.shared_state_path = shared_state_path
        self.explorer = explorer
        self.log_parser = LogParser(log_dir)
    
    def build_context(self, view_state: Dict[str, Any] = None, selected_event: str = None) -> Dict[str, Any]:
        """Build complete context for research assistant"""
        context = {}
        
        # Load shared state
        context['current_state'] = self._load_shared_state()
        
        # Load all logs
        context['recent_logs'] = self._load_recent_logs()
        
        # Get graph context
        context['graph_context'] = self._get_graph_context(selected_event)
        
        # Load configuration
        context['configuration'] = self._load_configuration()
        
        # Add view state
        context['view_state'] = view_state or {}
        
        return context
    
    def generate_snapshot_context(self, snapshot_timestamp: Optional[float] = None) -> str:
        """
        Generate concise contextual summary for a snapshot to help vision model understand what it's seeing.
        This creates the CRA → Vision Model feedback loop.
        
        Args:
            snapshot_timestamp: Optional timestamp of the snapshot (for historical context)
        
        Returns:
            Concise summary string with key metrics and context
        """
        if not self.shared_state_path.exists():
            return "System state unavailable."
        
        try:
            with open(self.shared_state_path, 'r') as f:
                state = json.load(f)
            
            data = state.get('data', {})
            parts = []
            
            # System phase and status
            explorer_data = data.get('explorer', {})
            phase = explorer_data.get('phase', 'unknown')
            breath_cycle = explorer_data.get('breath_cycle', 0)
            parts.append(f"Phase: {phase.upper()} | Breath: {breath_cycle}")
            
            # Violation Pressure (critical metric)
            djinn_data = data.get('djinn_kernel', {})
            vp = djinn_data.get('violation_pressure', 0.0)
            vp_class = djinn_data.get('vp_classification', 'VP0')
            parts.append(f"VP: {vp:.3f} ({vp_class})")
            
            # Network topology metrics
            network_data = data.get('network', {})
            modularity = network_data.get('modularity', 0.0)
            clustering = network_data.get('clustering_coefficient', 0.0)
            org_count = network_data.get('organism_count', 0)
            conn_count = network_data.get('connection_count', 0)
            parts.append(f"Network: {org_count} orgs, {conn_count} links | Modularity: {modularity:.3f}, Clustering: {clustering:.3f}")
            
            # Evolution status
            evolution_data = data.get('evolution', {})
            generation = evolution_data.get('generation', 0)
            fitness = evolution_data.get('best_fitness', 0.0)
            parts.append(f"Evolution: Gen {generation}, Fitness: {fitness:.3f}")
            
            # Graph structure interpretation
            if modularity < 0.2:
                parts.append("⚠️ Low modularity = highly integrated network (spherical topology)")
            elif modularity > 0.5:
                parts.append("ℹ️ High modularity = distinct functional clusters")
            
            if vp > 0.75:
                parts.append("⚠️ High VP = system under stress, many violations")
            elif vp < 0.25:
                parts.append("✅ Low VP = stable system state")
            
            if fitness >= 0.95:
                parts.append("⚠️ Near-max fitness = possible convergence/stagnation")
            
            # Component activity hints
            quantum_data = data.get('quantum', {})
            active_states = quantum_data.get('states', 0)
            if active_states > 30:
                parts.append(f"Quantum: {active_states} active states (high activity)")
            
            return " | ".join(parts)
            
        except Exception as e:
            logger.debug(f"Error generating snapshot context: {e}")
            return "Context unavailable."
    
    def _load_configuration(self) -> str:
        """Load system configuration files"""
        parts = []
        
        # Load config.json
        config_path = Path("config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                parts.append(f"# System Configuration (config.json)\n{json.dumps(config, indent=2)}")
            except Exception as e:
                parts.append(f"Error loading config.json: {e}")
        
        # Load ollama_config.json
        ollama_config_path = Path("ollama_config.json")
        if ollama_config_path.exists():
            try:
                with open(ollama_config_path, 'r') as f:
                    ollama_config = json.load(f)
                # Redact API key
                if 'api_key' in ollama_config:
                    ollama_config['api_key'] = "********"
                parts.append(f"\n# Ollama Configuration (ollama_config.json)\n{json.dumps(ollama_config, indent=2)}")
            except Exception as e:
                parts.append(f"Error loading ollama_config.json: {e}")
                
        if not parts:
            return "No configuration files found."
            
        return "\n".join(parts)

    def _load_shared_state(self) -> str:
        """Load and summarize shared state file"""
        if not self.shared_state_path.exists():
            return "No shared state file found."
        
        try:
            # Force reload if modified <10s
            file_mtime = os.path.getmtime(self.shared_state_path)
            current_time = time.time()
            force_reload = (current_time - file_mtime) < 10
            
            # Check simulation running status
            control_file = project_root / 'data' / '.simulation_control.json'
            simulation_running = False
            if control_file.exists():
                try:
                    with open(control_file, 'r') as f:
                        control = json.load(f)
                        simulation_running = bool(control.get('running', False))
                except:
                    simulation_running = False
            
            # Calculate data age
            data_age_seconds = current_time - file_mtime
            data_age_minutes = data_age_seconds / 60
            data_age_hours = data_age_seconds / 3600
            
            with open(self.shared_state_path, 'r') as f:
                state = json.load(f)
            
            parts = []
            
            # CRITICAL: System Status Header
            parts.append("# SYSTEM STATUS")
            if simulation_running:
                parts.append("🟢 SYSTEM IS RUNNING - Live data")
                if data_age_seconds < 10:
                    parts.append(f"Data freshness: LIVE (updated {data_age_seconds:.1f}s ago)")
                else:
                    parts.append(f"⚠️ WARNING: Data may be stale (last update {data_age_minutes:.1f} minutes ago)")
            else:
                parts.append("🔴 SYSTEM IS STOPPED - Historical data")
                if data_age_hours < 1:
                    parts.append(f"Data age: {data_age_minutes:.1f} minutes old (from previous run)")
                elif data_age_hours < 24:
                    parts.append(f"Data age: {data_age_hours:.1f} hours old (from previous run)")
                else:
                    parts.append(f"Data age: {data_age_hours/24:.1f} days old (from previous run)")
                parts.append("⚠️ IMPORTANT: This is HISTORICAL data, not a live system. Preflight diagnostics should focus on pattern analysis, not active system issues.")
            
            parts.append("")
            parts.append("# Current System State (from shared state file)")
            parts.append(f"Frame: {state.get('frame_count', 0)}")
            parts.append(f"FPS: {state.get('simulation_fps', 0.0)}")
            parts.append(f"Simulation Time: {state.get('simulation_time', 0)}")
            
            # Add data staleness warning if system is stopped
            if not simulation_running:
                if state.get('frame_count', 0) == 0 and state.get('simulation_fps', 0.0) == 0.0:
                    parts.append("")
                    parts.append("⚠️ NOTE: Frame=0 and FPS=0.0 indicates this is a snapshot from before simulation started, or from a stopped system.")
            
            data = state.get('data', {})
            
            if 'quantum' in data:
                q = data['quantum']
                parts.append(f"\n# Quantum System Data")
                parts.append(f"Active States: {q.get('states', 0)}")
                # Expose raw state details if available
                if 'state_details' in q and q['state_details']:
                    parts.append("State Details (Sample):")
                    # Sample top 5 states
                    for state in list(q['state_details'])[:5]:
                        parts.append(f"  - {state}")
            
            if 'lattice' in data:
                l = data['lattice']
                parts.append(f"\n# Lattice System Data")
                parts.append(f"Particles: {l.get('particles', 0)}")
                parts.append(f"CPU Usage: {l.get('cpu_usage', 0)}%")
                parts.append(f"RAM Usage: {l.get('ram_usage', 0)}MB")
                # Expose particle distribution if available
                if 'distribution' in l:
                    parts.append(f"Distribution: {l.get('distribution')}")
            
            if 'evolution' in data:
                e = data['evolution']
                parts.append(f"\n# Evolution Engine Data")
                parts.append(f"Generation: {e.get('generation', 0)}")
                parts.append(f"Population Size: {e.get('population_size', 0)}")
                parts.append(f"Best Fitness: {e.get('best_fitness', 0)}")
                # Expose top organism details
                if 'top_organisms' in e and e['top_organisms']:
                    parts.append("Top Organisms (Genetics):")
                    for org in list(e['top_organisms'])[:3]:
                        parts.append(f"  - ID: {org.get('id')} | Fitness: {org.get('fitness')} | Genome: {org.get('genome')}")
            
            if 'network' in data:
                n = data['network']
                parts.append(f"\n# Network Analysis Data")
                parts.append(f"Organisms: {n.get('organisms', 0)}")
                parts.append(f"Connections: {n.get('connections', 0)}")
                parts.append(f"Modularity: {n.get('modularity', 0)}")
                parts.append(f"Clustering Coefficient: {n.get('clustering_coefficient', 0)}")
                # Expose hub nodes if available
                if 'hubs' in n and n['hubs']:
                    parts.append(f"Network Hubs: {', '.join(str(h) for h in list(n['hubs'])[:5])}")
            
            if 'explorer' in data:
                ex = data['explorer']
                parts.append(f"\n# Explorer Data")
                parts.append(f"Phase: {ex.get('phase', 'unknown')}")
                parts.append(f"VP Calculations: {ex.get('vp_calculations', 0)}")
                parts.append(f"Breath Cycle: {ex.get('breath_cycle', 0)}")
            
            if 'djinn_kernel' in data:
                dk = data['djinn_kernel']
                parts.append(f"\n# Djinn Kernel Data")
                parts.append(f"Violation Pressure (VP): {dk.get('violation_pressure', 0)}")
                parts.append(f"VP Classification: {dk.get('vp_classification', 'unknown')}")
                parts.append(f"Tape Cells: {dk.get('tape_cells', 0)}")
                
                # VP Consistency Check and Analysis
                explorer_phase = data.get('explorer', {}).get('phase', 'unknown')
                vp_value = dk.get('violation_pressure', 0)
                vp_class = dk.get('vp_classification', 'unknown')
                vp_calculations = data.get('explorer', {}).get('vp_calculations', 0)
                tape_cells = dk.get('tape_cells', 0)
                
                parts.append(f"\n# VP Analysis & System Health")
                parts.append(f"VP Value: {vp_value:.4f} (Classification: {vp_class})")
                parts.append(f"Explorer Phase: {explorer_phase}")
                parts.append(f"VP Calculations: {vp_calculations:,}")
                parts.append(f"Tape Cells: {tape_cells:,}")
                
                # Synchronization check
                if vp_calculations > 0 and tape_cells > 0:
                    sync_ratio = vp_calculations / tape_cells if tape_cells > 0 else 0
                    parts.append(f"Synchronization Ratio: {sync_ratio:.4f} (VP calcs / Tape cells)")
                    if abs(sync_ratio - 1.0) > 0.01:
                        parts.append(f"⚠️ Sync Warning: Ratio deviates from 1.0 by {abs(sync_ratio - 1.0)*100:.2f}%")
                
                # Phase-VP consistency check
                if vp_class == 'VP4' and explorer_phase == 'genesis':
                    parts.append("\n⚠️ CRITICAL ANOMALY: VP4 detected during Genesis phase!")
                    parts.append("Expected: VP0-VP1 during Genesis (system should be stable)")
                    parts.append("Possible Causes:")
                    parts.append("  - Calibration issue in VP calculation thresholds")
                    parts.append("  - Early-stage system instability")
                    parts.append("  - Network/evolution metrics out of expected ranges")
                    parts.append("Recommendation: Investigate VP calculation inputs and phase detection logic")
                elif vp_class in ['VP0', 'VP1'] and explorer_phase == 'genesis':
                    parts.append("✓ Phase-VP Consistency: Normal (low VP during Genesis)")
                elif vp_class in ['VP2', 'VP3', 'VP4'] and explorer_phase == 'sovereign':
                    parts.append("✓ Phase-VP Consistency: Normal (higher VP during Sovereign)")
                
                # Network-Evolution correlation
                if 'network' in data and 'evolution' in data:
                    n = data['network']
                    e = data['evolution']
                    organisms = n.get('organisms', 0)
                    connections = n.get('connections', 0)
                    population = e.get('population_size', 0)
                    best_fitness = e.get('best_fitness', 0)
                    generation = e.get('generation', 0)
                    
                    parts.append(f"\n# Network-Evolution Correlation")
                    parts.append(f"Network: {organisms:,} organisms, {connections:,} connections")
                    parts.append(f"Evolution: Generation {generation}, Population {population:,}, Best Fitness {best_fitness:.4f}")
                    
                    if organisms > 0:
                        conn_per_org = connections / organisms
                        parts.append(f"Connections per Organism: {conn_per_org:.3f}")
                        if conn_per_org < 0.7:
                            parts.append("⚠️ Sparse Connectivity: <0.7 connections/organism may indicate fragmentation")
                    
                    if population > 0:
                        org_pop_ratio = organisms / population
                        parts.append(f"Organism/Population Ratio: {org_pop_ratio:.3f}")
                        if org_pop_ratio > 1.0:
                            parts.append("⚠️ More organisms than population - possible data inconsistency")
                    
                    # Fitness maturity check
                    if generation > 0 and best_fitness >= 1.0:
                        parts.append(f"⚠️ Fitness Maturity Check: Best fitness {best_fitness:.4f} at generation {generation}")
                        parts.append("  High fitness early may indicate premature convergence or calibration issue")
            
            return "\n".join(parts)
        except Exception as e:
            logger.error(f"Error loading shared state: {e}", exc_info=True)
            return f"Error loading shared state: {e}"
    
    def _load_recent_logs(self) -> str:
        """Load and summarize recent log entries"""
        log_data = self.log_parser.parse_all_logs(max_lines_per_file=500)
        return self.log_parser.summarize_logs(log_data)
    
    def _get_graph_context(self, selected_event: str = None) -> str:
        """Get causation graph context with detailed statistics"""
        if not self.explorer:
            return "Causation Explorer not available."
        
        try:
            parts = []
            total_events = len(self.explorer.events)
            total_links = self.explorer.causation_graph.number_of_edges()
            
            parts.append(f"# Causation Graph Statistics")
            parts.append(f"Total Events: {total_events:,}")
            parts.append(f"Total Causation Links: {total_links:,}")
            
            if total_events > 0:
                # Calculate link density
                max_possible_links = total_events * (total_events - 1) / 2
                link_density = (total_links / max_possible_links * 100) if max_possible_links > 0 else 0
                parts.append(f"Link Density: {link_density:.2f}% ({total_links:,} of {max_possible_links:,.0f} possible)")
            
            # Component distribution
            if self.explorer.events:
                component_counts = {}
                event_type_counts = {}
                for event_id, event in self.explorer.events.items():
                    comp = event.component
                    component_counts[comp] = component_counts.get(comp, 0) + 1
                    etype = event.event_type
                    event_type_counts[etype] = event_type_counts.get(etype, 0) + 1
                
                parts.append(f"\n# Component Distribution")
                for comp, count in sorted(component_counts.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / total_events * 100) if total_events > 0 else 0
                    parts.append(f"  {comp}: {count:,} events ({percentage:.1f}%)")
                
                parts.append(f"\n# Event Type Distribution (Top 10)")
                for etype, count in sorted(event_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                    percentage = (count / total_events * 100) if total_events > 0 else 0
                    parts.append(f"  {etype}: {count:,} ({percentage:.1f}%)")
            
            # Causation type distribution (if available in links)
            try:
                causation_type_counts = {}
                for edge in self.explorer.causation_graph.edges(data=True):
                    causation_type = edge[2].get('causation_type', 'unknown')
                    causation_type_counts[causation_type] = causation_type_counts.get(causation_type, 0) + 1
                
                if causation_type_counts:
                    parts.append(f"\n# Causation Type Distribution")
                    for ctype, count in sorted(causation_type_counts.items(), key=lambda x: x[1], reverse=True):
                        percentage = (count / total_links * 100) if total_links > 0 else 0
                        parts.append(f"  {ctype}: {count:,} links ({percentage:.1f}%)")
            except Exception:
                pass  # Skip if causation types not available
            
            # Temporal analysis
            if self.explorer.events:
                timestamps = [event.timestamp for event in self.explorer.events.values()]
                if timestamps:
                    min_time = min(timestamps)
                    max_time = max(timestamps)
                    time_span = max_time - min_time
                    parts.append(f"\n# Temporal Analysis")
                    parts.append(f"Time Span: {time_span:.2f} seconds")
                    parts.append(f"Events/Second: {total_events / time_span:.2f}" if time_span > 0 else "Events/Second: N/A")
                    parts.append(f"Links/Second: {total_links / time_span:.2f}" if time_span > 0 else "Links/Second: N/A")
            
            # Recent events summary
            if self.explorer.events:
                parts.append(f"\n# Recent Events (Last 10)")
                # Get last 10 events by timestamp
                recent_events = sorted(self.explorer.events.items(), 
                                      key=lambda x: x[1].timestamp, 
                                      reverse=True)[:10]
                for event_id, event in recent_events:
                    parts.append(f"  [{event.timestamp:.2f}] {event.component}: {event.event_type} (ID: {event_id[:8]}...)")
            
            # Selected event details with causal context
            if selected_event and selected_event in self.explorer.events:
                event = self.explorer.events[selected_event]
                parts.append(f"\n# Selected Event Details")
                parts.append(f"Event ID: {selected_event}")
                parts.append(f"Component: {event.component}")
                parts.append(f"Type: {event.event_type}")
                parts.append(f"Timestamp: {event.timestamp:.2f}")
                
                # Get causal connections
                in_degree = self.explorer.causation_graph.in_degree(selected_event)
                out_degree = self.explorer.causation_graph.out_degree(selected_event)
                parts.append(f"Causal Connections: {in_degree} incoming, {out_degree} outgoing")
                
                # Get immediate causes (incoming edges)
                if in_degree > 0:
                    causes = list(self.explorer.causation_graph.predecessors(selected_event))[:5]
                    parts.append(f"Immediate Causes (sample): {', '.join(c[:8] + '...' for c in causes[:5])}")
                
                # Get immediate effects (outgoing edges)
                if out_degree > 0:
                    effects = list(self.explorer.causation_graph.successors(selected_event))[:5]
                    parts.append(f"Immediate Effects (sample): {', '.join(e[:8] + '...' for e in effects[:5])}")
            
            return "\n".join(parts)
        except Exception as e:
            logger.error(f"Error getting graph context: {e}", exc_info=True)
            return f"Error getting graph context: {e}"


class SystemKnowledgeBase:
    """Load and provide system knowledge from documentation"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self._knowledge = None
    
    def load_knowledge(self) -> str:
        """Load system knowledge from documentation"""
        if self._knowledge:
            return self._knowledge
        
        parts = []
        
        # Load ARCHITECTURE.md if available
        arch_path = self.project_root / 'ARCHITECTURE.md'
        if arch_path.exists():
            try:
                with open(arch_path, 'r', encoding='utf-8') as f:
                    arch_content = f.read()
                    # Take first 3000 chars (summary)
                    parts.append(f"# System Architecture\n{arch_content[:3000]}...\n")
            except Exception as e:
                logger.warning(f"Could not load ARCHITECTURE.md: {e}")
        
        # Load README.md if available
        readme_path = self.project_root / 'README.md'
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                    # Take first 3000 chars (summary)
                    parts.append(f"# System Overview\n{readme_content[:3000]}...\n")
            except Exception as e:
                logger.warning(f"Could not load README.md: {e}")
        
        # Add system component descriptions
        parts.append(self._get_component_descriptions())
        
        self._knowledge = "\n".join(parts)
        return self._knowledge
    
    def _get_component_descriptions(self) -> str:
        """Get descriptions of system components"""
        return """
# Butterfly System Components

## Reality Simulator (Left Wing)
- Simulates quantum field, particle lattice, evolution, and network dynamics
- Network: Organisms (nodes) with connections (edges)
- Evolution: Generational selection and fitness
- Quantum: State field representation
- Lattice: Particle positions and interactions

## Explorer (Central Body / Breath Engine)
- Primary driver for all three systems
- Breath-driven execution cycles
- Causation graph exploration
- Phase tracking (Genesis/Sovereign)
- VP (Violation Pressure) calculations

## Djinn Kernel (Right Wing)
- UTM (Universal Turing Machine) kernel
- Akashic Ledger (immutable tape-based history)
- VP classification and calculations
- Trait convergence tracking
- Tape cell management

## Settings and Parameters
- Modularity: Network clustering metric (0.0-1.0)
- Clustering Coefficient: Node connectivity (0.0-1.0)
- Violation Pressure: System state indicator (0.0-1.0)
- VP Classifications: VP0 (<0.25), VP1 (0.25-0.50), VP2 (0.50-0.75), VP3 (0.75-0.99), VP4 (>=0.99)
- Breath Cycle: Explorer execution cycle
- Breath Depth: Depth of exploration phase
"""


class ChangeDetector:
    """Detect changes between graph snapshots"""
    
    def compare_snapshots(self, snapshot1: Dict[str, Any], snapshot2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two snapshots and return detected changes"""
        changes = {
            'node_changes': {
                'added': [],
                'removed': [],
                'modified': []
            },
            'link_changes': {
                'added': [],
                'removed': []
            },
            'metric_changes': {}
        }
        
        nodes1 = {n['id']: n for n in snapshot1.get('nodes', [])}
        nodes2 = {n['id']: n for n in snapshot2.get('nodes', [])}
        
        # Detect node changes
        node_ids1 = set(nodes1.keys())
        node_ids2 = set(nodes2.keys())
        
        added_nodes = node_ids2 - node_ids1
        removed_nodes = node_ids1 - node_ids2
        
        for node_id in added_nodes:
            changes['node_changes']['added'].append({
                'id': node_id,
                'component': nodes2[node_id].get('component'),
                'type': nodes2[node_id].get('type')
            })
        
        for node_id in removed_nodes:
            changes['node_changes']['removed'].append({
                'id': node_id,
                'component': nodes1[node_id].get('component'),
                'type': nodes1[node_id].get('type')
            })
        
        # Detect link changes
        links1 = {(l.get('source', {}).get('id', l.get('source')), 
                   l.get('target', {}).get('id', l.get('target'))) 
                  for l in snapshot1.get('links', [])}
        links2 = {(l.get('source', {}).get('id', l.get('source')), 
                   l.get('target', {}).get('id', l.get('target'))) 
                  for l in snapshot2.get('links', [])}
        
        added_links = links2 - links1
        removed_links = links1 - links2
        
        for source, target in added_links:
            changes['link_changes']['added'].append({
                'source': source,
                'target': target
            })
        
        for source, target in removed_links:
            changes['link_changes']['removed'].append({
                'source': source,
                'target': target
            })
        
        # Detect metric changes
        metrics1 = snapshot1.get('metrics', {})
        metrics2 = snapshot2.get('metrics', {})
        
        all_metrics = set(metrics1.keys()) | set(metrics2.keys())
        for metric in all_metrics:
            val1 = metrics1.get(metric, 0)
            val2 = metrics2.get(metric, 0)
            if val1 != val2:
                changes['metric_changes'][metric] = {
                    'before': val1,
                    'after': val2,
                    'change': val2 - val1,
                    'change_percent': ((val2 - val1) / val1 * 100) if val1 != 0 else 0
                }
        
        return changes


class ComparativeAnalyzer:
    """Compare different runs or sessions to identify differences"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.runs_dir = storage_dir / 'runs'
        self.runs_dir.mkdir(parents=True, exist_ok=True)
    
    def save_run_summary(self, run_id: str, summary: Dict[str, Any]):
        """Save a run summary for later comparison"""
        run_file = self.runs_dir / f"{run_id}.json"
        try:
            with open(run_file, 'w') as f:
                json.dump(summary, f, indent=2)
            return True
        except Exception as e:
            logger.warning(f"Could not save run summary: {e}")
            return False
    
    def load_run_summaries(self, max_runs: int = 10) -> List[Dict[str, Any]]:
        """Load recent run summaries"""
        run_files = sorted(self.runs_dir.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
        runs = []
        
        for run_file in run_files[:max_runs]:
            try:
                with open(run_file, 'r') as f:
                    runs.append(json.load(f))
            except Exception as e:
                logger.debug(f"Could not load run {run_file}: {e}")
        
        return runs
    
    def compare_runs(self, run1: Dict[str, Any], run2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two runs and return differences"""
        comparison = {
            'metrics_differences': {},
            'graph_differences': {},
            'event_differences': {}
        }
        
        # Compare metrics
        metrics1 = run1.get('metrics', {})
        metrics2 = run2.get('metrics', {})
        
        all_metrics = set(metrics1.keys()) | set(metrics2.keys())
        for metric in all_metrics:
            val1 = metrics1.get(metric, 0)
            val2 = metrics2.get(metric, 0)
            if val1 != val2:
                comparison['metrics_differences'][metric] = {
                    'run1_value': val1,
                    'run2_value': val2,
                    'difference': val2 - val1,
                    'percent_change': ((val2 - val1) / val1 * 100) if val1 != 0 else 0
                }
        
        # Compare graph stats
        graph1 = run1.get('graph_stats', {})
        graph2 = run2.get('graph_stats', {})
        
        comparison['graph_differences'] = {
            'nodes': {
                'run1': graph1.get('nodes', 0),
                'run2': graph2.get('nodes', 0),
                'difference': graph2.get('nodes', 0) - graph1.get('nodes', 0)
            },
            'links': {
                'run1': graph1.get('links', 0),
                'run2': graph2.get('links', 0),
                'difference': graph2.get('links', 0) - graph1.get('links', 0)
            }
        }
        
        # Compare event counts
        events1 = run1.get('event_count', 0)
        events2 = run2.get('event_count', 0)
        
        comparison['event_differences'] = {
            'run1_count': events1,
            'run2_count': events2,
            'difference': events2 - events1
        }
        
        return comparison
    
    def generate_comparison_report(self, run1_id: str, run2_id: str) -> str:
        """Generate a formatted comparison report"""
        runs = self.load_run_summaries(max_runs=20)
        run1 = next((r for r in runs if r.get('run_id') == run1_id), None)
        run2 = next((r for r in runs if r.get('run_id') == run2_id), None)
        
        if not run1 or not run2:
            return "Could not find one or both runs for comparison."
        
        comparison = self.compare_runs(run1, run2)
        
        parts = []
        parts.append(f"# Run Comparison Report")
        parts.append(f"Run 1: {run1_id} (from {run1.get('timestamp', 'unknown')})")
        parts.append(f"Run 2: {run2_id} (from {run2.get('timestamp', 'unknown')})")
        parts.append("\n## Metrics Differences")
        
        for metric, diff in comparison['metrics_differences'].items():
            parts.append(f"  {metric}: {diff['run1_value']:.3f} → {diff['run2_value']:.3f} "
                        f"({diff['percent_change']:+.2f}%)")
        
        parts.append("\n## Graph Differences")
        parts.append(f"  Nodes: {comparison['graph_differences']['nodes']['run1']} → "
                    f"{comparison['graph_differences']['nodes']['run2']} "
                    f"({comparison['graph_differences']['nodes']['difference']:+d})")
        parts.append(f"  Links: {comparison['graph_differences']['links']['run1']} → "
                    f"{comparison['graph_differences']['links']['run2']} "
                    f"({comparison['graph_differences']['links']['difference']:+d})")
        
        return "\n".join(parts)


class AlertSystem:
    """Monitor metrics and trigger alerts when thresholds are exceeded"""
    
    def __init__(self):
        self.thresholds = {
            'djinn_vp': {'min': 0.0, 'max': 0.99, 'alert_on_exceed': True},
            'explorer_vp': {'min': 0.0, 'max': 0.99, 'alert_on_exceed': True},
            'network_modularity': {'min': 0.0, 'max': 1.0, 'alert_on_exceed': False},
            'evolution_best_fitness': {'min': 0.0, 'max': float('inf'), 'alert_on_exceed': False},
            'event_frequency': {'min': 0, 'max': 10000, 'alert_on_exceed': True}
        }
        self.active_alerts = []
        self.alert_history = []
    
    def check_thresholds(self, metrics: Dict[str, float], time_series_tracker: 'TimeSeriesTracker') -> List[Dict[str, Any]]:
        """Check if any metrics exceed thresholds and return alerts"""
        alerts = []
        
        for metric_name, value in metrics.items():
            if metric_name not in self.thresholds:
                continue
            
            threshold = self.thresholds[metric_name]
            
            # Check min threshold
            if value < threshold['min']:
                alert = {
                    'metric': metric_name,
                    'value': value,
                    'threshold': threshold['min'],
                    'type': 'below_minimum',
                    'severity': 'warning',
                    'message': f"{metric_name} ({value:.3f}) below minimum threshold ({threshold['min']:.3f})",
                    'timestamp': time.time()
                }
                alerts.append(alert)
            
            # Check max threshold
            if threshold['alert_on_exceed'] and value > threshold['max']:
                alert = {
                    'metric': metric_name,
                    'value': value,
                    'threshold': threshold['max'],
                    'type': 'above_maximum',
                    'severity': 'critical' if value > threshold['max'] * 1.5 else 'warning',
                    'message': f"{metric_name} ({value:.3f}) exceeded maximum threshold ({threshold['max']:.3f})",
                    'timestamp': time.time()
                }
                alerts.append(alert)
        
        # Check for spikes using time-series tracker
        key_metrics = ['djinn_vp', 'explorer_vp', 'network_modularity']
        for metric in key_metrics:
            if metric in metrics:
                spikes = time_series_tracker.detect_spikes(metric, threshold_multiplier=3.0)  # Higher threshold for alerts
                if spikes:
                    latest_spike = spikes[-1]
                    alert = {
                        'metric': metric,
                        'value': latest_spike['value'],
                        'threshold': latest_spike['threshold'],
                        'type': 'spike_detected',
                        'severity': 'critical',
                        'message': f"{metric} spike detected: {latest_spike['value']:.3f} ({latest_spike['deviation']:.2f}σ above average)",
                        'timestamp': latest_spike['timestamp']
                    }
                    alerts.append(alert)
        
        # Update alert history
        self.alert_history.extend(alerts)
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
        
        self.active_alerts = alerts
        return alerts


class PersistentContext:
    """Save and load chat history and snapshots across sessions"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.chat_history_file = storage_dir / 'chat_history.json'
        self.snapshots_dir = storage_dir / 'snapshots'
        self.snapshots_dir.mkdir(exist_ok=True)
    
    def save_chat_message(self, role: str, message: str, timestamp: float = None):
        """Save a chat message to history"""
        if timestamp is None:
            timestamp = time.time()
        
        # Load existing history
        history = self.load_chat_history()
        
        # Add new message
        history.append({
            'timestamp': timestamp,
            'role': role,
            'message': message
        })
        
        # Save back
        try:
            with open(self.chat_history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save chat history: {e}")
    
    def load_chat_history(self) -> List[Dict[str, Any]]:
        """Load chat history from disk"""
        if not self.chat_history_file.exists():
            return []
        
        try:
            with open(self.chat_history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load chat history: {e}")
            return []
    
    def save_snapshot(self, snapshot_data: Dict[str, Any], snapshot_id: str = None):
        """Save a graph snapshot"""
        if snapshot_id is None:
            snapshot_id = f"snapshot_{int(time.time())}"
        
        snapshot_file = self.snapshots_dir / f"{snapshot_id}.json"
        try:
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot_data, f, indent=2)
            return snapshot_id
        except Exception as e:
            logger.warning(f"Could not save snapshot: {e}")
            return None
    
    def load_snapshots(self, max_snapshots: int = 10) -> List[Dict[str, Any]]:
        """Load recent snapshots"""
        snapshot_files = sorted(self.snapshots_dir.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
        snapshots = []
        
        for snapshot_file in snapshot_files[:max_snapshots]:
            try:
                with open(snapshot_file, 'r') as f:
                    snapshots.append(json.load(f))
            except Exception as e:
                logger.debug(f"Could not load snapshot {snapshot_file}: {e}")
        
        return snapshots


class PredictiveAnalyzer:
    """Generate predictive insights based on time-series trends"""
    
    def __init__(self, time_series_tracker: 'TimeSeriesTracker'):
        self.tracker = time_series_tracker
    
    def predict_future_value(self, metric_name: str, steps_ahead: int = 10) -> Optional[float]:
        """Predict future value based on linear trend"""
        trend = self.tracker.get_trend(metric_name, window_size=20)
        if trend.get('trend') == 'insufficient_data':
            return None
        
        history = self.tracker.metrics_history.get(metric_name, [])
        if len(history) < 2:
            return None
        
        # Simple linear extrapolation using change percentage
        current_value = trend.get('current_value', 0)
        change_percent = trend.get('change_percent', 0)
        
        # Calculate predicted value based on percentage change
        # Assume change_percent is per window, so scale by steps_ahead
        if change_percent != 0:
            predicted_value = current_value * (1 + (change_percent / 100) * (steps_ahead / 10))
            return predicted_value
        else:
            # If no change, return current value
            return current_value
    
    def generate_insights(self) -> Dict[str, Any]:
        """Generate predictive insights for key metrics"""
        insights = {}
        
        key_metrics = ['djinn_vp', 'explorer_vp', 'network_modularity', 'evolution_best_fitness']
        
        for metric in key_metrics:
            trend = self.tracker.get_trend(metric, window_size=20)
            if trend.get('trend') == 'insufficient_data':
                continue
            
            prediction = self.predict_future_value(metric, steps_ahead=10)
            
            insight = {
                'current_trend': trend.get('trend'),
                'change_percent': trend.get('change_percent', 0),
                'current_value': trend.get('current_value'),
                'predicted_value': prediction,
                'confidence': 'low'  # Simple model, low confidence
            }
            
            # Add qualitative prediction
            if trend.get('trend') == 'increasing':
                if trend.get('change_percent', 0) > 5:
                    insight['prediction'] = f"{metric} is rapidly increasing - expect continued growth"
                else:
                    insight['prediction'] = f"{metric} is gradually increasing - slow positive trend"
            elif trend.get('trend') == 'decreasing':
                if trend.get('change_percent', 0) < -5:
                    insight['prediction'] = f"{metric} is rapidly decreasing - monitor closely"
                else:
                    insight['prediction'] = f"{metric} is gradually decreasing - slow negative trend"
            else:
                insight['prediction'] = f"{metric} is stable - no significant change expected"
            
            insights[metric] = insight
        
        return insights


class TimeSeriesTracker:
    """Track metrics over time for trend analysis and anomaly detection"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history = defaultdict(list)  # metric_name -> [(timestamp, value), ...]
        self.last_update_time = None
    
    def record_metric(self, metric_name: str, value: float, timestamp: float = None):
        """Record a metric value at a given timestamp"""
        if timestamp is None:
            timestamp = time.time()
        
        history = self.metrics_history[metric_name]
        history.append((timestamp, value))
        
        # Keep only last max_history entries
        if len(history) > self.max_history:
            history.pop(0)
    
    def extract_metrics_from_state(self, state: Dict[str, Any], timestamp: float = None):
        """Extract all metrics from shared state and record them"""
        if timestamp is None:
            timestamp = time.time()
        
        data = state.get('data', {})
        
        # Frame-level metrics
        self.record_metric('frame_count', state.get('frame_count', 0), timestamp)
        self.record_metric('simulation_fps', state.get('simulation_fps', 0.0), timestamp)
        self.record_metric('simulation_time', state.get('simulation_time', 0.0), timestamp)
        
        # Quantum metrics
        if 'quantum' in data:
            q = data['quantum']
            self.record_metric('quantum_states', q.get('states', 0), timestamp)
            self.record_metric('quantum_energy', q.get('energy', 0.0), timestamp)
            self.record_metric('quantum_entropy', q.get('entropy', 0.0), timestamp)
        
        # Lattice metrics
        if 'lattice' in data:
            l = data['lattice']
            self.record_metric('lattice_particles', l.get('particles', 0), timestamp)
            self.record_metric('lattice_cpu_usage', l.get('cpu_usage', 0.0), timestamp)
            self.record_metric('lattice_temperature', l.get('temperature', 0.0), timestamp)
        
        # Evolution metrics
        if 'evolution' in data:
            e = data['evolution']
            self.record_metric('evolution_generation', e.get('generation', 0), timestamp)
            self.record_metric('evolution_population', e.get('population_size', 0), timestamp)
            self.record_metric('evolution_best_fitness', e.get('best_fitness', 0.0), timestamp)
            self.record_metric('evolution_avg_fitness', e.get('avg_fitness', 0.0), timestamp)
        
        # Network metrics
        if 'network' in data:
            n = data['network']
            self.record_metric('network_organisms', n.get('organisms', 0), timestamp)
            self.record_metric('network_connections', n.get('connections', 0), timestamp)
            self.record_metric('network_modularity', n.get('modularity', 0.0), timestamp)
            self.record_metric('network_clustering', n.get('clustering_coefficient', 0.0), timestamp)
        
        # Explorer metrics
        if 'explorer' in data:
            ex = data['explorer']
            self.record_metric('explorer_vp', ex.get('current_vp', 0.0), timestamp)
            self.record_metric('explorer_phase', self._phase_to_number(ex.get('phase', 'unknown')), timestamp)
            self.record_metric('explorer_breath_cycle', ex.get('breath_cycle', 0), timestamp)
        
        # Djinn Kernel metrics
        if 'djinn_kernel' in data:
            dk = data['djinn_kernel']
            self.record_metric('djinn_vp', dk.get('violation_pressure', 0.0), timestamp)
            self.record_metric('djinn_tape_cells', dk.get('tape_cells', 0), timestamp)
        
        self.last_update_time = timestamp
    
    def _phase_to_number(self, phase: str) -> float:
        """Convert phase name to number for tracking"""
        phase_map = {'unknown': 0, 'exploration': 1, 'analysis': 2, 'synthesis': 3}
        return phase_map.get(phase.lower(), 0)
    
    def get_trend(self, metric_name: str, window_size: int = 10) -> Dict[str, Any]:
        """Calculate trend statistics for a metric"""
        history = self.metrics_history.get(metric_name, [])
        if len(history) < 2:
            return {'trend': 'insufficient_data', 'slope': 0, 'change_percent': 0}
        
        # Get recent window
        recent = history[-window_size:] if len(history) >= window_size else history
        
        values = [v for _, v in recent]
        timestamps = [t for t, _ in recent]
        
        # Calculate slope (simple linear regression)
        n = len(values)
        if n < 2:
            return {'trend': 'insufficient_data', 'slope': 0, 'change_percent': 0}
        
        sum_x = sum(timestamps)
        sum_y = sum(values)
        sum_xy = sum(t * v for t, v in zip(timestamps, values))
        sum_x2 = sum(t * t for t in timestamps)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0
        
        # Calculate percentage change
        first_value = values[0]
        last_value = values[-1]
        change_percent = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0
        
        # Determine trend direction
        if abs(slope) < 1e-6:
            trend = 'stable'
        elif slope > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'
        
        return {
            'trend': trend,
            'slope': slope,
            'change_percent': change_percent,
            'current_value': last_value,
            'previous_value': values[-2] if len(values) >= 2 else first_value,
            'min_value': min(values),
            'max_value': max(values),
            'avg_value': sum(values) / len(values),
            'data_points': len(recent)
        }
    
    def get_all_trends(self, window_size: int = 10) -> Dict[str, Dict[str, Any]]:
        """Get trend statistics for all tracked metrics"""
        return {metric: self.get_trend(metric, window_size) for metric in self.metrics_history.keys()}
    
    def detect_spikes(self, metric_name: str, threshold_multiplier: float = 2.0) -> List[Dict[str, Any]]:
        """Detect spikes in a metric (values > threshold_multiplier * average)"""
        history = self.metrics_history.get(metric_name, [])
        if len(history) < 10:
            return []
        
        values = [v for _, v in history]
        avg = sum(values) / len(values)
        std_dev = (sum((v - avg) ** 2 for v in values) / len(values)) ** 0.5
        threshold = avg + (threshold_multiplier * std_dev)
        
        spikes = []
        for timestamp, value in history:
            if value > threshold:
                spikes.append({
                    'timestamp': timestamp,
                    'value': value,
                    'threshold': threshold,
                    'deviation': (value - avg) / std_dev if std_dev > 0 else 0
                })
        
        return spikes


# Initialize Ollama Bridge and Context Builder
project_root = Path(__file__).parent
log_dir = project_root / 'data' / 'logs'
shared_state_path = project_root / 'data' / '.shared_simulation_state.json'
# Load Ollama config from file if available
config_dir = project_root / 'data' / 'causation_explorer'
config_dir.mkdir(parents=True, exist_ok=True)
config_file = config_dir / 'ollama_config.json'

ollama_config = {}
if config_file.exists():
    try:
        with open(config_file, 'r') as f:
            ollama_config = json.load(f)
        logger.info(f"Loaded Ollama config from {config_file}")
    except Exception as e:
        logger.warning(f"Could not load Ollama config: {e}")

# Initialize OllamaBridge with config file settings (env vars take precedence)
ollama_bridge = OllamaBridge(
    base_url=os.getenv("OLLAMA_BASE_URL") or ollama_config.get("base_url"),
    timeout=float(os.getenv("OLLAMA_TIMEOUT", str(ollama_config.get("timeout", 30.0)))),
    api_key=ollama_config.get("api_key") or os.getenv("OLLAMA_API_KEY")
)

context_builder = SystemContextBuilder(log_dir, shared_state_path, explorer)
knowledge_base = SystemKnowledgeBase(project_root)
time_series_tracker = TimeSeriesTracker(max_history=1000)

# Initialize persistent context and predictive analyzer
storage_dir = project_root / 'data' / 'causation_explorer'
persistent_context = PersistentContext(storage_dir)
predictive_analyzer = PredictiveAnalyzer(time_series_tracker)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'explorer_initialized': explorer is not None,
        'template_path': str(Path(__file__).parent / 'templates' / 'causation_explorer.html'),
        'template_exists': (Path(__file__).parent / 'templates' / 'causation_explorer.html').exists()
    })


@app.route('/favicon.ico')
def favicon():
    """Serve favicon (blank to prevent 404)"""
    return '', 204  # No content


@app.route('/')
def index():
    """Main interface"""
    try:
        # Verify template exists
        template_path = Path(__file__).parent / 'templates' / 'causation_explorer.html'
        if not template_path.exists():
            error_msg = f"Error: Template not found at {template_path}. Please ensure templates/causation_explorer.html exists."
            logger.error(error_msg)
            return f"<html><body><h1>{error_msg}</h1></body></html>", 500
        
        logger.info(f"Rendering template from: {template_path}")
        return render_template('causation_explorer.html')
    except Exception as e:
        error_msg = f"Error rendering template: {e}"
        logger.error(error_msg, exc_info=True)
        return f"<html><body><h1>{error_msg}</h1><pre>{traceback.format_exc()}</pre></body></html>", 500


@app.route('/api/events/search')
def search_events():
    """Search events"""
    if explorer is None:
        return jsonify({'error': 'Causation Explorer not initialized'}), 500
    try:
        query = request.args.get('q', '')
        results = explorer.search_events(query)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error searching events: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/events/<event_id>')
def get_event(event_id):
    """Get event details"""
    if explorer is None:
        return jsonify({'error': 'Causation Explorer not initialized'}), 500
    try:
        summary = explorer.get_event_summary(event_id)
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error getting event {event_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/events/<event_id>/backwards')
def explore_backwards(event_id):
    """Explore what caused this event"""
    if explorer is None:
        return jsonify({'error': 'Causation Explorer not initialized'}), 500
    try:
        max_depth = int(request.args.get('depth', 10))
        trail = explorer.explore_backwards(event_id, max_depth)
        return jsonify(trail)
    except Exception as e:
        logger.error(f"Error exploring backwards for {event_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/events/<event_id>/forwards')
def explore_forwards(event_id):
    """Explore what this event caused"""
    if explorer is None:
        return jsonify({'error': 'Causation Explorer not initialized'}), 500
    try:
        max_depth = int(request.args.get('depth', 10))
        trail = explorer.explore_forwards(event_id, max_depth)
        return jsonify(trail)
    except Exception as e:
        logger.error(f"Error exploring forwards for {event_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/path/<from_id>/<to_id>')
def find_path(from_id, to_id):
    """Find path between two events"""
    if explorer is None:
        return jsonify({'path': None, 'events': [], 'error': 'Causation Explorer not initialized'}), 200
    try:
        path = explorer.find_path(from_id, to_id)
        if path:
            events = [explorer.events[eid].to_dict() for eid in path]
            return jsonify({'path': path, 'events': events})
        return jsonify({'path': None, 'events': []})
    except Exception as e:
        logger.error(f"Error finding path from {from_id} to {to_id}: {e}", exc_info=True)
        return jsonify({'path': None, 'events': [], 'error': str(e)}), 200


@app.route('/api/stats')
def get_stats():
    """Get causation graph statistics"""
    if explorer is None:
        return jsonify({'error': 'Causation Explorer not initialized', 'total_events': 0, 'total_links': 0}), 200
    try:
        stats = explorer.get_causation_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return jsonify({'error': str(e), 'total_events': 0, 'total_links': 0}), 200


@app.route('/api/live/status')
def get_live_status():
    """
    Check if system is in live mode (receiving events from unified_entry.py)
    
    ⚠️ CURRENT BEHAVIOR (NOT ACTUALLY LIVE):
    - Accesses: explorer.events{} (loaded from log files on startup)
    - Checks: If any events have recent timestamps (within 10 seconds)
    - Returns: {"live": true/false} based on timestamp check
    - Problem: Only checks already-loaded events, doesn't connect to running backend
    
    🔍 DATA SOURCES ACCESSED:
    - explorer.events{} - Dictionary of all events loaded from:
      1. Akashic Ledger (if available) - data/kernel/akashic_ledger/
      2. Log files (fallback) - data/logs/*.log
      ❌ NOT: Shared state file (data/.shared_simulation_state.json)
      ❌ NOT: Real-time events from unified_entry.py
    
    💡 TO MAKE IT ACTUALLY LIVE:
    - Add event feeding from unified_entry.py (Phase 2)
    - Add shared state file loading
    - Poll for updates from running backend
    """
    # Check if CausationExplorer has recent events (within last 5 seconds)
    if explorer is None or not explorer.events:
        return jsonify({'live': False, 'last_event_time': None, 'event_count': 0})
    
    try:
        # DATA ACCESS: Get most recent event timestamp from explorer.events{}
        # This is loaded from log files on startup, NOT from running backend
        recent_events = sorted(explorer.events.values(), key=lambda e: e.timestamp, reverse=True)
        if recent_events:
            last_event_time = recent_events[0].timestamp
            current_time = time.time()
            # Consider live if last event was within last 10 seconds
            # ⚠️ This just checks timestamps of already-loaded events, not actual backend connection
            is_live = (current_time - last_event_time) < 10
            return jsonify({
                'live': is_live,
                'last_event_time': last_event_time,
                'event_count': len(explorer.events),  # Total events loaded from logs/Akashic
                'events_since_start': len(recent_events)
            })
        return jsonify({'live': False, 'last_event_time': None, 'event_count': 0})
    except Exception as e:
        logger.error(f"Error checking live status: {e}", exc_info=True)
        return jsonify({'live': False, 'error': str(e)})


@app.route('/api/live/events')
def get_new_events():
    """
    Get events since a given timestamp (for live updates)
    
    ⚠️ CURRENT BEHAVIOR (NOT ACTUALLY LIVE):
    - Accesses: explorer.events{} (loaded from log files on startup)
    - Filters: Events where event.timestamp > since_timestamp
    - Returns: Filtered subset of already-loaded events
    - Problem: Only returns events that were loaded on startup, not new events from backend
    
    🔍 DATA SOURCES ACCESSED:
    - explorer.events{} - Dictionary of all events loaded from:
      1. Akashic Ledger (if available) - data/kernel/akashic_ledger/
      2. Log files (fallback) - data/logs/*.log
      ❌ NOT: Shared state file (data/.shared_simulation_state.json)
      ❌ NOT: Real-time events from unified_entry.py
    
    💡 TO MAKE IT ACTUALLY LIVE:
    - Add event feeding from unified_entry.py (Phase 2)
    - Add shared state file polling
    - Stream new events from running backend
    """
    if explorer is None:
        return jsonify({'events': [], 'event_count': 0})
    
    try:
        since_timestamp = float(request.args.get('since', 0))
        # DATA ACCESS: Filter explorer.events{} for events after timestamp
        # ⚠️ This only filters already-loaded events from log files, not new events from backend
        new_events = [
            e.to_dict() for e in explorer.events.values()
            if e.timestamp > since_timestamp
        ]
        # Sort by timestamp
        new_events.sort(key=lambda e: e['timestamp'])
        
        return jsonify({
            'events': new_events,
            'event_count': len(new_events),
            'latest_timestamp': max([e['timestamp'] for e in new_events]) if new_events else since_timestamp
        })
    except Exception as e:
        logger.error(f"Error getting new events: {e}", exc_info=True)
        return jsonify({'events': [], 'error': str(e)})


@app.route('/api/graph')
def get_graph():
    """
    Get full causation graph for visualization
    
    🔍 DATA SOURCES ACCESSED:
    - explorer.events{} - Dictionary of all events loaded from:
      1. Akashic Ledger (if available) - data/kernel/akashic_ledger/
      2. Log files (fallback) - data/logs/*.log
      ❌ NOT: Shared state file (data/.shared_simulation_state.json)
      ❌ NOT: Real-time events from unified_entry.py
    
    - explorer.causation_graph - NetworkX DiGraph containing:
      - Nodes: Event IDs (from explorer.events{})
      - Edges: Causation links (threshold, correlation, direct, temporal)
      - Created when events are added via add_event()
      - Causations detected automatically when events are loaded
    
    📊 WHAT GETS VISUALIZED:
    - Nodes: All events from explorer.events{}
      - id, component, type, data, timestamp
    - Links: All causation links from explorer.causation_graph
      - source, target, type, strength, explanation
    
    ✅ Phase 2: REAL-TIME UPDATES (IMPLEMENTED):
    - Loads latest state from shared state file on each graph request (incremental)
    - Shows new events from running unified_entry.py in real-time
    - Thread-safe access to event graph (snapshots prevent iteration errors)
    """
    global _graph_cache, _graph_cache_time
    
    if explorer is None:
        return jsonify({'nodes': [], 'links': [], 'error': 'Causation Explorer not initialized'}), 200
    
    # Return cached graph if available and fresh
    current_time = time.time()
    if _graph_cache and (current_time - _graph_cache_time) < CACHE_DURATION:
        logger.info("Returning cached graph data")
        return jsonify(_graph_cache)
    
    try:
        # Phase 2: Load latest state from shared state file ONLY if simulation is running
        # Check simulation control file to see if simulation is actually running
        # IMPORTANT: unified_entry.py runs autonomously, so we must check the control file
        # to know if the user has started the simulation via the web UI
        try:
            control_file = project_root / 'data' / '.simulation_control.json'
            simulation_running = False
            if control_file.exists():
                with open(control_file, 'r') as f:
                    control = json.load(f)
                    simulation_running = bool(control.get('running', False))

            # CRITICAL: Only load from shared state if simulation is actually running
            # If stopped, return existing graph data only (no new events from shared state)
            if simulation_running:
                shared_state_path = Path('data/.shared_simulation_state.json')
                if shared_state_path.exists():
                    # Check file modification time to see if it's been updated recently
                    import os
                    file_mtime = os.path.getmtime(shared_state_path)
                    current_time = time.time()

                    # If file was modified in the last 10 seconds, definitely reload
                    if (current_time - file_mtime) < 10:
                        logger.info(f"Shared state file recently updated ({current_time - file_mtime:.1f}s ago), loading...")
                        explorer._load_from_shared_state(force_reload=True)  # Force reload recent data
                    else:
                        # File exists but might be old, still try incremental load
                        explorer._load_from_shared_state(force_reload=False)
                else:
                    logger.debug("Shared state file does not exist yet")
            else:
                logger.info("Simulation is stopped - returning existing graph data only (not loading from shared state)")
        except Exception as e:
            logger.warning(f"Could not check simulation status: {e}", exc_info=True)
            # On error, default to NOT loading from shared state (safer)
            logger.debug("Error checking simulation status - not loading from shared state")
        
        nodes = []
        links = []
        
        # DATA ACCESS: Read all events from explorer.events{}
        # This includes:
        # - Log files loaded on startup
        # - Akashic Ledger loaded on startup
        # - Shared state file (just loaded above for live updates)
        # Add nodes (use lock for thread safety)
        with explorer.graph_lock:
            events_snapshot = dict(explorer.events)  # Create snapshot inside lock
            edges_snapshot = list(explorer.causation_graph.edges(data=True))  # Create snapshot inside lock
        
        # Process snapshots outside lock
        if events_snapshot:
            component_counts = {}  # Debug: track component distribution
            for event_id, event in events_snapshot.items():
                # Normalize component names to match color mapping in HTML
                component = (event.component or 'unknown').lower().strip()
                # Map variations to standard names
                if 'reality' in component or 'sim' in component:
                    component = 'reality_sim'
                elif 'explorer' in component:
                    component = 'explorer'
                elif 'djinn' in component or 'kernel' in component or 'utm' in component:
                    component = 'djinn_kernel'
                elif 'breath' in component:
                    component = 'breath'
                elif 'system' in component:
                    component = 'system'
                else:
                    component = component  # Keep as-is (will default to orange)
                
                component_counts[component] = component_counts.get(component, 0) + 1
                nodes.append({
                    'id': event_id,
                    'component': component,  # Normalized component name
                    'type': event.event_type,
                    'data': event.data,
                    'timestamp': event.timestamp
                })
            # Log component distribution for debugging
            if component_counts:
                logger.info(f"Graph nodes by component: {component_counts}")
                logger.info(f"Total nodes: {len(nodes)} (from {len(events_snapshot)} total), Total links: {len(links)}")
        
        # DATA ACCESS: Read all causation links from explorer.causation_graph (snapshot)
        # This is a NetworkX DiGraph built when events are added
        # Causation links are detected automatically (threshold, correlation, direct, temporal)
        # Add links
        if edges_snapshot:
            for u, v, data in edges_snapshot:
                links.append({
                    'source': u,
                    'target': v,
                    'type': data.get('causation_type', 'unknown'),
                    'strength': data.get('strength', 0.0),
                    'explanation': data.get('explanation', '')
                })
        
        # Add diagnostic info if no data
        diagnostic_info = {}
        if len(nodes) == 0:
            shared_state_path = Path('data/.shared_simulation_state.json')
            diagnostic_info['no_data'] = True
            diagnostic_info['data_sources_checked'] = {
                'shared_state_exists': shared_state_path.exists(),
                'log_dir_exists': explorer.log_dir.exists() if explorer else False,
                'log_files_count': len(list(explorer.log_dir.glob('*.log'))) if explorer and explorer.log_dir.exists() else 0,
                'events_in_memory': len(explorer.events) if explorer else 0,
            }
            if shared_state_path.exists():
                import os
                file_mtime = os.path.getmtime(shared_state_path)
                file_age = time.time() - file_mtime
                diagnostic_info['data_sources_checked']['shared_state_age_seconds'] = file_age
            diagnostic_info['message'] = 'No events found. Make sure the simulation is running and generating data.'
            logger.warning(f"Graph request returned 0 nodes. Diagnostics: {diagnostic_info}")
        else:
            logger.info(f"Graph request returned {len(nodes)} nodes and {len(links)} links")
        
        return jsonify({
            'nodes': nodes,
            'links': links,
            'diagnostic': diagnostic_info if diagnostic_info else None
        })
    except Exception as e:
        logger.error(f"Error getting graph: {e}", exc_info=True)
        return jsonify({'nodes': [], 'links': [], 'error': str(e)}), 200


# ============================================================================
# CONVERGENCE RESEARCH ASSISTANT - FLASK ENDPOINTS
# ============================================================================

@app.route('/api/ollama/config', methods=['GET'])
def get_ollama_config():
    """Get current Ollama configuration"""
    try:
        return jsonify({
            'base_url': ollama_bridge.base_url,
            'is_cloud': ollama_bridge.is_cloud,
            'has_api_key': bool(ollama_bridge.api_key),
            'timeout': ollama_bridge.timeout
        })
    except Exception as e:
        logger.error(f"Error getting Ollama config: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/ollama/config', methods=['POST'])
def set_ollama_config():
    """Update Ollama configuration"""
    try:
        data = request.get_json()
        base_url = data.get('base_url')
        api_key = data.get('api_key')
        timeout = data.get('timeout')
        
        # Validate base_url
        if base_url:
            if base_url.startswith("https://ollama.com"):
                if not api_key:
                    return jsonify({'error': 'API key required for cloud mode'}), 400
            elif not base_url.startswith("http://"):
                return jsonify({'error': 'Invalid base URL. Use http://localhost:11434 or https://ollama.com'}), 400
        
        # Update OllamaBridge (only update provided values)
        update_kwargs = {}
        if base_url is not None:
            update_kwargs['base_url'] = base_url
        if api_key is not None:
            update_kwargs['api_key'] = api_key
        if timeout is not None:
            update_kwargs['timeout'] = float(timeout)
        
        if update_kwargs:
            ollama_bridge.update_config(**update_kwargs)
        
        # Save to config file
        config_data = {
            'base_url': ollama_bridge.base_url,
            'api_key': ollama_bridge.api_key,
            'timeout': ollama_bridge.timeout
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"Saved Ollama config to {config_file}")
        except Exception as e:
            logger.warning(f"Could not save Ollama config: {e}")
        
        return jsonify({
            'success': True,
            'config': {
                'base_url': ollama_bridge.base_url,
                'is_cloud': ollama_bridge.is_cloud,
                'has_api_key': bool(ollama_bridge.api_key),
                'timeout': ollama_bridge.timeout
            }
        })
    except Exception as e:
        logger.error(f"Error setting Ollama config: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/ollama/test', methods=['POST'])
def test_ollama_connection():
    """Test Ollama connection"""
    try:
        models = ollama_bridge.list_models()
        if models or ollama_bridge.is_cloud:
            return jsonify({
                'success': True,
                'connected': True,
                'model_count': len(models),
                'mode': 'cloud' if ollama_bridge.is_cloud else 'local'
            })
        else:
            return jsonify({
                'success': False,
                'connected': False,
                'error': 'Could not connect to Ollama'
            }), 503
    except Exception as e:
        logger.error(f"Error testing Ollama connection: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'connected': False,
            'error': str(e)
        }), 503


@app.route('/api/ollama/models')
def list_ollama_models():
    """List available Ollama models"""
    try:
        models_data = ollama_bridge.list_models()
        # models_data is a list of model objects from Ollama API
        # Each model has: {'name': 'model-name', 'modified_at': '...', 'size': ...}
        
        # Separate vision models from text models (heuristic)
        vision_models = []
        text_models = []
        all_models = []
        
        for model in models_data:
            # Handle both dict format and string format
            if isinstance(model, dict):
                model_name = model.get('name', '')
            else:
                model_name = str(model)
            
            if not model_name:
                continue
            
            # Normalize model name (remove tags like :latest, :7b, etc for comparison)
            name_lower = model_name.lower()
            
            # Common vision model patterns
            # Ollama Cloud only supports Qwen3-VL for vision (in preview)
            # Local Ollama supports: llava, bakllava, moondream, minicpm-v, etc.
            if any(keyword in name_lower for keyword in ['vision', 'llava', 'clip', 'minicpm-v', 'bakllava', 'moondream', 'qwen3-vl', 'qwen-vl', 'qwen3vl']):
                vision_models.append({'name': model_name, 'model': model_name})
            else:
                text_models.append({'name': model_name, 'model': model_name})
            
            all_models.append({'name': model_name, 'model': model_name})
        
        # NO FALLBACKS - only real vision models allowed
        
        # For Ollama Cloud, prioritize Qwen3-VL for vision (it's the only supported vision model)
        if ollama_bridge.is_cloud:
            # Find Qwen3-VL models and move them to front
            qwen_models = [m for m in vision_models if 'qwen3-vl' in m.get('name', '').lower() or 'qwen-vl' in m.get('name', '').lower()]
            if qwen_models:
                # Remove Qwen models from their current position
                vision_models = [m for m in vision_models if 'qwen3-vl' not in m.get('name', '').lower() and 'qwen-vl' not in m.get('name', '').lower()]
                # Add Qwen models to front
                vision_models = qwen_models + vision_models
        
        return jsonify({
            'models': all_models,
            'text_models': text_models,
            'vision_models': vision_models,
            'is_cloud': ollama_bridge.is_cloud,
            'cloud_vision_hint': 'Qwen3-VL' if ollama_bridge.is_cloud else None
        })
    except Exception as e:
        logger.error(f"Error listing Ollama models: {e}", exc_info=True)
        return jsonify({'error': str(e), 'models': [], 'text_models': [], 'vision_models': []}), 500


@app.route('/api/ollama/chat', methods=['POST'])
def ollama_chat():
    """Send message to research assistant with complete context"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        model = data.get('model', 'llama2')
        view_state = data.get('view_state', {})
        selected_event = data.get('selected_event')
        graph_image = data.get('graph_image')  # base64 image if provided
        evolutionary_snapshots = data.get('evolutionary_snapshots', [])  # List of historical snapshots
        user_api_key = data.get('api_key')  # User-provided API key (optional)
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Use user's API key if provided, otherwise use server default
        bridge_to_use = ollama_bridge
        if user_api_key:
            bridge_to_use = OllamaBridge(
                base_url=ollama_bridge.base_url,
                timeout=ollama_bridge.timeout,
                api_key=user_api_key
            )
        
        # Update time-series tracker with current state
        try:
            if shared_state_path.exists():
                with open(shared_state_path, 'r') as f:
                    current_state = json.load(f)
                time_series_tracker.extract_metrics_from_state(current_state)
        except Exception as e:
            logger.debug(f"Could not update time-series tracker: {e}")
        
        # Build context
        context = context_builder.build_context(view_state=view_state, selected_event=selected_event)
        
        # Add system knowledge
        context['system_knowledge'] = knowledge_base.load_knowledge()
        
        # Add time-series trends and anomaly detection
        context['time_series_trends'] = time_series_tracker.get_all_trends(window_size=20)
        
        # Detect anomalies/spikes in key metrics
        anomalies = {}
        key_metrics = ['djinn_vp', 'explorer_vp', 'network_modularity', 'evolution_best_fitness']
        for metric in key_metrics:
            spikes = time_series_tracker.detect_spikes(metric, threshold_multiplier=2.0)
            if spikes:
                anomalies[metric] = spikes[-5:]  # Last 5 spikes
        
        if anomalies:
            context['anomalies'] = anomalies
        
        # If graph image provided, analyze it with vision model (images only, no context)
        # Vision model gets ONLY images. CRA gets vision analysis + all context.
        visual_description = None
        vision_error = None
        images_trimmed_warning = None  # Initialize for trimming feedback
        if graph_image and data.get('vision_model'):
            vision_model = data.get('vision_model')
            
            # Collect all images: current + evolutionary snapshots
            # Strategy: Send up to 10 snapshots for evolution analysis
            # We use analyze_sequence to bypass the 150KB cloud payload limit per request
            MAX_VISION_IMAGES = 10  # Target: 10 images for deep evolutionary analysis
            
            all_images = []
            
            # Track original count for trimming feedback
            original_snapshot_count = len(evolutionary_snapshots) if evolutionary_snapshots else 0
            images_trimmed = False
            
            # Add evolutionary snapshots first (they're older)
            # CRA → Vision Model feedback loop: Generate contextual summaries for each snapshot
            snapshot_contexts = []  # Store CRA-generated context for each snapshot
            if evolutionary_snapshots:
                # Extract images from snapshots (already sorted oldest to newest)
                # Filter out blank/empty images (too small = likely blank)
                MIN_VALID_IMAGE_SIZE = 20000  # Minimum 20KB base64 - blank images are ~7-10KB
                snapshot_images = []
                for snapshot in evolutionary_snapshots:
                    if isinstance(snapshot, dict) and 'image' in snapshot:
                        img = snapshot['image']
                        if img and len(img) >= MIN_VALID_IMAGE_SIZE:  # Only add non-empty, meaningful images
                            snapshot_images.append(img)
                            # Generate CRA contextual summary for this snapshot
                            snapshot_timestamp = snapshot.get('timestamp')
                            snapshot_context = context_builder.generate_snapshot_context(snapshot_timestamp)
                            snapshot_contexts.append(snapshot_context)
                            logger.debug(f"Valid snapshot: {len(img)/1024:.1f}KB | Context: {snapshot_context[:50]}...")
                        else:
                            logger.warning(f"Filtered out blank/empty snapshot: {len(img)/1024:.1f}KB (minimum: {MIN_VALID_IMAGE_SIZE/1024:.1f}KB)")
                    elif isinstance(snapshot, str) and len(snapshot) >= MIN_VALID_IMAGE_SIZE:
                        snapshot_images.append(snapshot)
                        # Generate context for string snapshots too
                        snapshot_contexts.append(context_builder.generate_snapshot_context())
                
                # Ensure we have a gradual evolution - if we have too many, sample evenly
                # Target: MAX_VISION_IMAGES total images (N-1 historical + 1 current)
                target_historical = MAX_VISION_IMAGES - 1 
                if len(snapshot_images) > target_historical:
                    images_trimmed = True
                    # Sample evenly across the timeline for better evolution representation
                    # Instead of just taking the most recent, sample evenly to show gradual progression
                    if len(snapshot_images) > target_historical * 2:
                        # If we have many snapshots, sample evenly across the timeline
                        step = len(snapshot_images) / target_historical
                        sampled = []
                        for i in range(target_historical):
                            idx = int(i * step)
                            sampled.append(snapshot_images[idx])
                        snapshot_images = sampled
                        logger.debug(f"Evenly sampled {len(snapshot_images)} snapshots from {len(evolutionary_snapshots)} for gradual evolution")
                    else:
                        # If we have fewer, just take evenly spaced from the end
                        snapshot_images = snapshot_images[-target_historical:]
                        logger.debug(f"Limited evolutionary snapshots from {len(evolutionary_snapshots)} to {len(snapshot_images)} (target: {target_historical} for {MAX_VISION_IMAGES} total)")
                
                all_images.extend(snapshot_images)
            
            # Add current image last (it's the newest)
            # CRITICAL: This should be the FRESH, CURRENT graph state
            if graph_image:
                # Validate current image is meaningful
                if len(graph_image) >= 20000:  # Minimum 20KB
                    all_images.append(graph_image)
                    # Generate CRA contextual summary for current image
                    current_context = context_builder.generate_snapshot_context()
                    snapshot_contexts.append(current_context)
                    logger.info(f"Added CURRENT graph image: {len(graph_image)/1024:.1f}KB (fresh capture) | Context: {current_context[:50]}...")
                else:
                    logger.warning(f"Current graph image too small ({len(graph_image)/1024:.1f}KB), may be blank/cached. Skipping.")
            
            # Final limit check - never send more than MAX
            if len(all_images) > MAX_VISION_IMAGES:
                # CRITICAL: If we need to trim, keep the CURRENT image (last one) and trim oldest historical
                if graph_image and len(graph_image) >= 20000:
                    # Keep current image + most recent historical
                    all_images = all_images[-(MAX_VISION_IMAGES-1):]  # Keep last N-1 historical
                    all_images.append(graph_image)  # Always include current (fresh) image
                    logger.debug(f"Final limit: kept {len(all_images)-1} historical + 1 current (fresh) image")
                else:
                    # No current image, just trim to most recent
                    all_images = all_images[-MAX_VISION_IMAGES:]
                    logger.debug(f"Final limit: keeping {MAX_VISION_IMAGES} most recent images (no current image)")
            
            if not all_images:
                vision_error = "No images available for vision analysis."
            else:
                # Log what we're sending with size info and freshness
                total_size_kb = sum(len(img.encode('utf-8')) for img in all_images) / 1024
                if len(all_images) > 1:
                    logger.info(f"Vision model: Analyzing {len(all_images)} snapshots for evolution (current + {len(all_images)-1} historical, total {total_size_kb:.1f}KB)")
                    # Log image order and sizes for debugging
                    for i, img in enumerate(all_images):
                        size_kb = len(img.encode('utf-8')) / 1024
                        if i == len(all_images) - 1:
                            logger.info(f"  Image {i+1}/{len(all_images)}: {size_kb:.1f}KB [CURRENT - FRESH CAPTURE]")
                        else:
                            logger.info(f"  Image {i+1}/{len(all_images)}: {size_kb:.1f}KB [Historical snapshot]")
                else:
                    logger.info(f"Vision model: Analyzing 1 snapshot (current state only, {total_size_kb:.1f}KB) - no history available yet")
                    if graph_image:
                        logger.info(f"  [CURRENT - FRESH CAPTURE: {len(graph_image.encode('utf-8'))/1024:.1f}KB]")
                
                # Minimal prompt for vision model - ONLY asks it to describe what it sees
                # NO system context - that goes to CRA instead
                # ENHANCED PROMPT: Make it crystal clear this is a network graph, not biological artwork
                system_context = """IMPORTANT: You are analyzing a NETWORK GRAPH visualization, not biological artwork or organisms. This is a data visualization showing:
- NODES (colored circles/dots) = Events in a computational system
- EDGES/LINKS (lines connecting nodes) = Causation relationships between events
- COLORS = Different system components (realitysim, explorer, djinnkernel, etc.)
- LAYOUT = Force-directed graph layout showing event relationships

CRITICAL: "Butterfly System" is ONLY a CONCEPTUAL NAME for this computational system - it does NOT mean the graph looks like a butterfly shape. Do NOT look for butterfly-shaped patterns, wings, or biological structures. This is purely a technical network graph with nodes and edges. The name "Butterfly" refers to the "butterfly effect" concept in chaos theory, NOT a visual shape.

This is the Butterfly System's Causation Explorer - a network graph showing how events cause other events in a complex computational system. The graph shows the structure and evolution of event causation over time. Look for:
- Graph topology (how nodes are connected)
- Network structure (clusters, isolated nodes, branching patterns)
- Connection density and patterns
- Node distribution and clustering
- Changes in graph structure over time

DO NOT interpret this as biological artwork, organisms, organic structures, or butterfly shapes. This is a technical network diagram showing computational event causation."""
                
                annotation_instruction = """

ANNOTATION REQUEST: After your analysis, provide annotations in JSON format to highlight key features you described. Use annotations like a sports commentator drawing on screen - circles for clusters, arrows for flows, text labels for important nodes/patterns:
{
  "annotations": [
    {"type": "circle", "x": 100, "y": 200, "radius": 50, "color": "#FF0000", "label": "Dense cluster"},
    {"type": "arrow", "x1": 150, "y1": 250, "x2": 300, "y2": 400, "color": "#00FF00", "label": "Causation flow"},
    {"type": "text", "x": 400, "y": 300, "text": "Key node", "color": "#0000FF"}
  ]
}
Annotation types: "circle" (highlight areas), "arrow" (show direction/flow), "text" (label features). Coordinates are in pixels (0,0 = top-left). Use annotations to visually emphasize your key observations."""
                
                if len(all_images) >= 3:
                    vision_prompt = f"""{system_context}

These {len(all_images)} images show the evolution of a causation graph network over time (oldest to newest). Compare all {len(all_images)} images and describe: What changes do you see in the NETWORK STRUCTURE? How does the graph topology, node positions, connections, and patterns evolve? Describe the evolution timeline from oldest to newest. Pay attention to: node movement, cluster formation/dissolution, connection changes, network density changes, and overall structural evolution of the graph.{annotation_instruction}"""
                elif len(all_images) == 2:
                    vision_prompt = f"""{system_context}

These 2 images show the evolution of a causation graph network over time (oldest to newest). Compare them and describe: What changes do you see in the NETWORK STRUCTURE? How does the graph topology, node positions, connections, and patterns evolve? Describe the evolution timeline from oldest to newest.{annotation_instruction}"""
                else:
                    # Single image - describe current state, note that this is the first snapshot
                    vision_prompt = f"""{system_context}

This is a single snapshot of a causation graph network visualization (no previous snapshots available for comparison yet). Describe what you see in the NETWORK GRAPH: What are the node colors and what system components do they represent? What is the graph structure and topology? Are there clusters, isolated nodes, or branching patterns? What do the connections show about event causation? How dense is the network? Note: This is the first snapshot, so no evolutionary analysis is possible yet.{annotation_instruction}"""
                
                # Vision model gets images + CRA contextual summaries (feedback loop)
                # CRA → Vision Model: CRA provides context about what each snapshot means
                # Vision Model → CRA: Vision model provides enhanced analysis with context
                try:
                    # Use sequential analysis for multiple images to bypass payload limits
                    # and ensure high quality for each image
                    if len(all_images) > 1:
                        logger.info(f"Using sequential analysis for {len(all_images)} images with CRA contextual summaries")
                        # Pass snapshot contexts to analyze_sequence for CRA → Vision feedback loop
                        visual_description = bridge_to_use.analyze_sequence(vision_model, all_images, vision_prompt, snapshot_contexts)
                    else:
                        # Single image - include CRA context in prompt
                        if snapshot_contexts and len(snapshot_contexts) > 0:
                            cra_context = snapshot_contexts[0]
                            context_section = f"""

📊 SYSTEM CONTEXT (from CRA analysis):
{cra_context}

Use this context to understand what the graph structure means. Match the visual patterns you see with the system state described above."""
                            vision_prompt = vision_prompt + context_section
                        visual_description = bridge_to_use.vision(vision_model, all_images, vision_prompt)
                    
                    if visual_description:
                        # Parse annotations from vision response
                        annotations = None
                        try:
                            # Try to extract JSON annotations from the response
                            # Look for JSON object with "annotations" key
                            json_match = re.search(r'\{[^{}]*"annotations"[^{}]*\[.*?\].*?\}', visual_description, re.DOTALL)
                            if json_match:
                                annotations = json.loads(json_match.group(0))
                                logger.info(f"Extracted {len(annotations.get('annotations', []))} annotations from vision response")
                        except Exception as e:
                            logger.debug(f"Could not parse annotations from vision response: {e}")
                        
                        # Add metadata about snapshots for CRA context
                        if len(all_images) > 1:
                            visual_description = f"[Visual Evolution Analysis - {len(all_images)} snapshots]\n{visual_description}"
                        else:
                            visual_description = f"[Visual Analysis - Single Snapshot (no evolution data available yet)]\n{visual_description}"
                        
                        # Pass vision analysis to CRA context (CRA has all the data points)
                        context['visual_description'] = visual_description
                        if annotations:
                            context['vision_annotations'] = annotations
                except Exception as e:
                    vision_error = f"Vision model error: {str(e)}"
                    logger.error(f"Vision model call failed: {e}", exc_info=True)
                    visual_description = None
                
                # Check if images were trimmed and set warning
                if original_snapshot_count > MAX_VISION_IMAGES - 1:
                    images_trimmed_warning = f"⚠️ Note: {original_snapshot_count} snapshots available, but only {len(all_images)} were sent for analysis (limit: {MAX_VISION_IMAGES} images)."
        elif data.get('vision_model') and not graph_image:
            vision_error = "Vision model selected but no graph image captured. Try adjusting graph view or filters."
        
        # Build messages for chat
        messages = [{"role": "user", "content": message}]
        
        # Send to research assistant
        response = bridge_to_use.chat(model, messages, context)
        
        if response is None:
            return jsonify({'error': 'Failed to get response from Ollama'}), 500
        
        # Save chat messages to persistent context
        try:
            persistent_context.save_chat_message('user', message)
            persistent_context.save_chat_message('assistant', response)
            if visual_description:
                persistent_context.save_chat_message('vision', visual_description)
            
            # Save run summary periodically (every 10 messages or so)
            history = persistent_context.load_chat_history()
            if len(history) % 10 == 0:
                run_summary = {
                    'run_id': f"run_{int(time.time())}",
                    'timestamp': time.time(),
                    'metrics': current_metrics if current_metrics else {},
                    'graph_stats': {
                        'nodes': len(explorer.events) if explorer else 0,
                        'links': explorer.causation_graph.number_of_edges() if explorer else 0
                    },
                    'event_count': len(explorer.events) if explorer else 0
                }
                comparative_analyzer.save_run_summary(run_summary['run_id'], run_summary)
        except Exception as e:
            logger.debug(f"Could not save chat history: {e}")
        
        # Prepare evolutionary snapshots for display (with images)
        display_snapshots = []
        if evolutionary_snapshots:
            for i, snapshot in enumerate(evolutionary_snapshots[-4:]):  # Show last 4 snapshots
                if isinstance(snapshot, dict) and 'image' in snapshot:
                    display_snapshots.append({
                        'index': i + 1,
                        'timestamp': snapshot.get('timestamp', 0),
                        'age_seconds': snapshot.get('age_seconds', 0),
                        'image': snapshot['image'],
                        'view_state': snapshot.get('view_state', {})
                    })

        return jsonify({
            'response': response,
            'visual_description': visual_description,
            'vision_error': vision_error,  # Include vision errors for frontend display
            'evolutionary_snapshots': display_snapshots,  # Include actual images for display
            'vision_annotations': context.get('vision_annotations'),  # Include annotations for image overlay
            'images_trimmed_warning': images_trimmed_warning,  # Feedback about trimming
            'context_sources': {
                'shared_state': shared_state_path.exists(),
                'log_files': len(list(log_dir.glob('*.log'))) if log_dir.exists() else 0,
                'graph_events': len(explorer.events) if explorer else 0
            },
            'trends': context.get('time_series_trends', {}),
            'anomalies': len(context.get('anomalies', {})),
            'alerts': len(context.get('alerts', [])),
            'predictions': len(context.get('predictive_insights', {}))
        })
    except Exception as e:
        logger.error(f"Error in Ollama chat: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/ollama/vision', methods=['POST'])
def ollama_vision():
    """Analyze graph view with vision model"""
    try:
        data = request.get_json()
        image_base64 = data.get('image')
        model = data.get('model', 'qwen3-vl:235b-instruct')
        prompt = data.get('prompt', 'Describe what you see in this causation graph visualization.')
        user_api_key = data.get('api_key')  # User-provided API key (optional)
        
        if not image_base64:
            return jsonify({'error': 'Image is required'}), 400
        
        # Use user's API key if provided, otherwise use server default
        bridge_to_use = ollama_bridge
        if user_api_key:
            bridge_to_use = OllamaBridge(
                base_url=ollama_bridge.base_url,
                timeout=ollama_bridge.timeout,
                api_key=user_api_key
            )
        
        try:
            response = bridge_to_use.vision(model, image_base64, prompt)
            if response is None:
                return jsonify({'error': 'Failed to get response from vision model'}), 500
            return jsonify({'description': response})
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in Ollama vision: {error_msg}", exc_info=True)
            return jsonify({'error': error_msg}), 500
    except Exception as e:
        logger.error(f"Error in Ollama vision endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/vision/annotate', methods=['POST'])
def annotate_image():
    """Apply annotations to an image and return annotated version"""
    try:
        data = request.get_json()
        image_base64 = data.get('image')
        annotations = data.get('annotations', [])
        
        if not image_base64:
            return jsonify({'error': 'Image is required'}), 400
        
        if not PIL_AVAILABLE:
            return jsonify({'error': 'PIL/Pillow not available for image annotation'}), 500
        
        try:
            # Decode base64 image
            import base64
            from io import BytesIO
            
            # Remove data URL prefix if present
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]
            
            image_data = base64.b64decode(image_base64)
            img = Image.open(BytesIO(image_data))
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Draw annotations
            from PIL import ImageDraw, ImageFont
            
            draw = ImageDraw.Draw(img)
            
            # Try to load a font, fallback to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            for ann in annotations:
                ann_type = ann.get('type')
                color = ann.get('color', '#FF0000')
                
                # Convert hex color to RGB tuple
                if color.startswith('#'):
                    color = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
                else:
                    color = (255, 0, 0)  # Default red
                
                if ann_type == 'circle':
                    x = ann.get('x', 0)
                    y = ann.get('y', 0)
                    radius = ann.get('radius', 20)
                    label = ann.get('label', '')
                    
                    # Draw circle
                    bbox = [x - radius, y - radius, x + radius, y + radius]
                    draw.ellipse(bbox, outline=color, width=3)
                    
                    # Draw label if provided
                    if label:
                        draw.text((x + radius + 5, y - 10), label, fill=color, font=font)
                
                elif ann_type == 'arrow':
                    x1 = ann.get('x1', 0)
                    y1 = ann.get('y1', 0)
                    x2 = ann.get('x2', 0)
                    y2 = ann.get('y2', 0)
                    label = ann.get('label', '')
                    
                    # Draw arrow line
                    draw.line([(x1, y1), (x2, y2)], fill=color, width=3)
                    
                    # Draw arrowhead (simple triangle)
                    import math
                    angle = math.atan2(y2 - y1, x2 - x1)
                    arrow_size = 10
                    arrow_x1 = x2 - arrow_size * math.cos(angle - math.pi/6)
                    arrow_y1 = y2 - arrow_size * math.sin(angle - math.pi/6)
                    arrow_x2 = x2 - arrow_size * math.cos(angle + math.pi/6)
                    arrow_y2 = y2 - arrow_size * math.sin(angle + math.pi/6)
                    draw.polygon([(x2, y2), (arrow_x1, arrow_y1), (arrow_x2, arrow_y2)], fill=color)
                    
                    # Draw label at midpoint
                    if label:
                        mid_x = (x1 + x2) / 2
                        mid_y = (y1 + y2) / 2
                        draw.text((mid_x, mid_y - 15), label, fill=color, font=font)
                
                elif ann_type == 'text':
                    x = ann.get('x', 0)
                    y = ann.get('y', 0)
                    text = ann.get('text', '')
                    
                    # Draw text with background for visibility
                    bbox = draw.textbbox((x, y), text, font=font)
                    padding = 4
                    draw.rectangle(
                        [bbox[0] - padding, bbox[1] - padding, bbox[2] + padding, bbox[3] + padding],
                        fill=(0, 0, 0, 180)  # Semi-transparent black background
                    )
                    draw.text((x, y), text, fill=color, font=font)
            
            # Convert back to base64
            output = BytesIO()
            img.save(output, format='PNG')
            output.seek(0)
            annotated_base64 = base64.b64encode(output.getvalue()).decode('utf-8')
            
            return jsonify({
                'annotated_image': f'data:image/png;base64,{annotated_base64}',
                'annotations_applied': len(annotations)
            })
            
        except Exception as e:
            logger.error(f"Error annotating image: {e}", exc_info=True)
            return jsonify({'error': f'Failed to annotate image: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Error in annotate_image endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/runs/compare', methods=['POST'])
def compare_runs_endpoint():
    """Compare two runs"""
    try:
        data = request.get_json()
        run1_id = data.get('run1_id')
        run2_id = data.get('run2_id')
        
        if not run1_id or not run2_id:
            return jsonify({'error': 'Both run1_id and run2_id are required'}), 400
        
        report = comparative_analyzer.generate_comparison_report(run1_id, run2_id)
        return jsonify({'report': report})
    except Exception as e:
        logger.error(f"Error comparing runs: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/runs/list')
def list_runs_endpoint():
    """List all saved runs"""
    try:
        runs = comparative_analyzer.load_run_summaries(max_runs=20)
        return jsonify({'runs': runs, 'count': len(runs)})
    except Exception as e:
        logger.error(f"Error listing runs: {e}", exc_info=True)
        return jsonify({'error': str(e), 'runs': []}), 500


@app.route('/api/chat/history')
def get_chat_history_endpoint():
    """Get chat history from persistent storage"""
    try:
        history = persistent_context.load_chat_history()
        return jsonify({'history': history, 'count': len(history)})
    except Exception as e:
        logger.error(f"Error loading chat history: {e}", exc_info=True)
        return jsonify({'error': str(e), 'history': []}), 500


@app.route('/api/system/context')
def get_system_context():
    """Get current system context (for debugging)"""
    try:
        view_state = request.args.get('view_state')
        selected_event = request.args.get('selected_event')
        
        view_state_dict = json.loads(view_state) if view_state else {}
        context = context_builder.build_context(view_state=view_state_dict, selected_event=selected_event)
        context['system_knowledge'] = knowledge_base.load_knowledge()[:1000] + "..."  # Truncated for display
        
        return jsonify(context)
    except Exception as e:
        logger.error(f"Error getting system context: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/simulation/status', methods=['GET'])
def get_simulation_status():
    """Get simulation running status"""
    try:
        control_file = project_root / 'data' / '.simulation_control.json'
        control_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create control file with default STOPPED state if it doesn't exist
        if not control_file.exists():
            with open(control_file, 'w') as f:
                json.dump({'running': False, 'paused': True, 'timestamp': time.time()}, f, indent=2)
            return jsonify({'running': False, 'paused': True})
        
        with open(control_file, 'r') as f:
            control = json.load(f)
            return jsonify({
                'running': control.get('running', False),
                'paused': control.get('paused', True)
            })
    except Exception as e:
        logger.error(f"Error getting simulation status: {e}", exc_info=True)
        return jsonify({'running': False, 'paused': True, 'error': str(e)}), 500


@app.route('/api/simulation/start', methods=['POST'])
def start_simulation():
    """Start the simulation"""
    try:
        control_file = project_root / 'data' / '.simulation_control.json'
        control_file.parent.mkdir(parents=True, exist_ok=True)
        control = {
            'running': True,
            'paused': False,
            'timestamp': time.time()
        }
        with open(control_file, 'w') as f:
            json.dump(control, f, indent=2)

        # Start event streaming for CRA
        start_event_streaming()

        # Publish event about simulation control
        publish_cra_event('simulation_control', {
            'action': 'start',
            'status': 'signal_sent',
            'timestamp': datetime.now().isoformat()
        })

        logger.info("Simulation start signal sent - CRA event streaming activated")
        return jsonify({'success': True, 'message': 'Simulation start signal sent - CRA event streaming activated'})
    except Exception as e:
        logger.error(f"Error starting simulation: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/simulation/stop', methods=['POST'])
def stop_simulation():
    """Stop/pause the simulation"""
    try:
        control_file = project_root / 'data' / '.simulation_control.json'
        control_file.parent.mkdir(parents=True, exist_ok=True)
        control = {
            'running': False,
            'paused': True,
            'timestamp': time.time()
        }
        with open(control_file, 'w') as f:
            json.dump(control, f, indent=2)
        logger.info("Simulation stop signal sent")
        return jsonify({'success': True, 'message': 'Simulation stop signal sent'})
    except Exception as e:
        logger.error(f"Error stopping simulation: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export/create_evolutionary_video', methods=['POST'])
def create_evolutionary_video():
    """Create high-quality evolutionary video using vision model analysis"""
    try:
        import subprocess
        import tempfile
        import shutil

        # Check FFmpeg availability
        try:
            subprocess.run(['ffmpeg', '-version'],
                          capture_output=True,
                          check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return jsonify({
                'error': 'FFmpeg not found. Please install FFmpeg to create videos.',
                'install_help': {
                    'windows': 'Download from https://ffmpeg.org/download.html or use: winget install ffmpeg',
                    'mac': 'brew install ffmpeg',
                    'linux': 'sudo apt-get install ffmpeg'
                }
            }), 400

        # Get parameters
        data = request.json
        evolution_duration = data.get('evolution_duration', 300)  # Default 5 minutes
        fps = data.get('fps', 2)  # Slower for evolution viewing
        quality = data.get('quality', 'high')  # high, medium, low
        include_narration = data.get('include_narration', True)

        # Collect evolutionary snapshots from server-side accumulation
        evolutionary_snapshots = []

        try:
            # Get accumulated snapshots from server storage
            snapshots_dir = Path('data/snapshots')
            index_file = snapshots_dir / 'snapshot_index.json'

            if index_file.exists():
                with open(index_file, 'r') as f:
                    index = json.load(f)

                # Load snapshot data for video creation
                # For fluid videos, use ALL available snapshots (up to reasonable limit)
                # Calculate based on video duration and FPS: duration_seconds * fps = needed frames
                max_snapshots_for_video = min(10000, len(index['snapshots']))  # Up to 10,000 snapshots for long videos
                current_snapshots = []
                for snapshot_info in index['snapshots'][-max_snapshots_for_video:]:  # Use all available snapshots
                    snapshot_file = snapshots_dir / snapshot_info['filename']
                    if snapshot_file.exists():
                        with open(snapshot_file, 'r') as f:
                            snapshot = json.load(f)
                            current_snapshots.append(snapshot)

                logger.info(f"Loaded {len(current_snapshots)} snapshots for evolutionary video creation")
            else:
                current_snapshots = []

        except Exception as e:
            logger.error(f"Error loading evolutionary snapshots: {e}")
            current_snapshots = []

        if not current_snapshots or len(current_snapshots) < 10:
            return jsonify({
                'error': f'Insufficient evolutionary data. Need at least 10 snapshots for meaningful evolution video. Currently have: {len(current_snapshots)}',
                'recommendation': 'Start evolution recording first, then run evolution to accumulate snapshots.',
                'current_snapshots': len(current_snapshots),
                'troubleshooting': [
                    '1. Click "🎬 START EVOLUTION RECORDING" to begin accumulation',
                    '2. Start the simulation and let it run for several minutes',
                    '3. Check "📊 STATS" to see snapshot accumulation progress',
                    '4. Try creating video again once you have 10+ snapshots'
                ]
            }), 400

        # Quality settings
        if quality == 'high':
            video_quality = ['-crf', '18', '-preset', 'slow']
        elif quality == 'medium':
            video_quality = ['-crf', '23', '-preset', 'medium']
        else:  # low
            video_quality = ['-crf', '28', '-preset', 'fast']

        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            frame_files = []

            # Process each evolutionary snapshot
            for i, snapshot in enumerate(current_snapshots):
                # Extract base64 image data
                if isinstance(snapshot, dict) and 'image' in snapshot:
                    image_data = snapshot['image']
                    if image_data.startswith('data:image/png;base64,'):
                        image_data = image_data.split(',')[1]

                    # Decode and save frame
                    frame_bytes = base64.b64decode(image_data)
                    frame_path = os.path.join(temp_dir, f'frame_{i:04d}.png')

                    with open(frame_path, 'wb') as f:
                        f.write(frame_bytes)
                    frame_files.append(frame_path)

            if not frame_files:
                logger.error(f"No valid image frames found. Processed {len(current_snapshots)} snapshots but extracted 0 frames.")
                logger.error("This usually means snapshots don't contain valid 'image' data in base64 format.")
                return jsonify({
                    'error': 'No valid image frames found in snapshots',
                    'snapshots_processed': len(current_snapshots),
                    'frames_extracted': 0,
                    'troubleshooting': [
                        '1. Verify snapshots contain valid base64 image data',
                        '2. Check snapshot format: should have "image" field with data:image/png;base64,...',
                        '3. Ensure snapshots were captured correctly during evolution recording',
                        '4. Try checking snapshot files manually in data/snapshots/ directory'
                    ]
                }), 400

            # Create output filename
            output_name = f'butterfly_evolution_{int(time.time())}.mp4'
            output_path = os.path.join(temp_dir, output_name)

            # Create video with smooth transitions
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite
                '-framerate', str(fps),
                '-i', os.path.join(temp_dir, 'frame_%04d.png'),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-vf', f'fps={fps},scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
                '-tune', 'animation',
                '-movflags', '+faststart'
            ] + video_quality + [output_path]

            # Run FFmpeg
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            logger.info(f"Processing {len(frame_files)} frames at {fps} FPS")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=temp_dir)

            if result.returncode != 0:
                logger.error(f"FFmpeg failed with return code {result.returncode}")
                logger.error(f"FFmpeg stderr: {result.stderr}")
                logger.error(f"FFmpeg stdout: {result.stdout}")
                return jsonify({
                    'error': 'FFmpeg video encoding failed',
                    'ffmpeg_error': result.stderr,
                    'ffmpeg_stdout': result.stdout,
                    'return_code': result.returncode,
                    'command': ' '.join(cmd),
                    'frames_processed': len(frame_files),
                    'troubleshooting': [
                        '1. Verify FFmpeg is correctly installed: ffmpeg -version',
                        '2. Check that all frame images are valid PNG files',
                        '3. Ensure sufficient disk space for output video',
                        '4. Try reducing video quality or FPS settings',
                        '5. Check FFmpeg error message above for specific issues'
                    ]
                }), 500

            # Read and return video
            with open(output_path, 'rb') as f:
                video_data = base64.b64encode(f.read()).decode('utf-8')

            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB

            # Create evolution analysis using vision model - REQUIRED
            evolution_analysis = ""
            if include_narration:
                if len(current_snapshots) < 3:
                    return jsonify({
                        'error': 'At least 3 snapshots required for evolution analysis',
                        'current_snapshots': len(current_snapshots)
                    }), 400

                try:
                    logger.info(f"Generating REQUIRED evolution analysis for {len(current_snapshots)} snapshots...")
                    # Use vision model to analyze the full evolution - NO FALLBACKS
                    vision_analysis = analyze_evolution_with_vision(current_snapshots)
                    evolution_analysis = vision_analysis.get('description', '')

                    if not evolution_analysis or vision_analysis.get('error'):
                        return jsonify({
                            'error': 'Evolution analysis failed - cannot create video without proper vision model narration',
                            'vision_error': vision_analysis.get('description', 'Vision model returned no analysis'),
                            'snapshots_available': len(current_snapshots)
                        }), 500

                    logger.info("Evolution analysis generated successfully - proceeding with video creation")

                except Exception as e:
                    logger.error(f"Evolution analysis failed: {e}")
                    return jsonify({
                        'error': f'Vision model analysis failed: {str(e)} - cannot create video without proper narration',
                        'cause': 'Vision model unavailable or failing',
                        'solution': 'Ensure Ollama vision model is running and accessible'
                    }), 500

            # Success! Return the video data
            result_data = {
                'success': True,
                'video_data': video_data,
                'filename': output_name,
                'size_mb': round(file_size, 2),
                'frames': len(frame_files),
                'fps': fps,
                'duration_seconds': round(len(frame_files) / fps, 2),
                'evolution_analysis': evolution_analysis,
                'quality': quality,
                'resolution': '1920x1080',
                'snapshots_used': len(current_snapshots),
                'message': f'Created {quality} quality evolutionary video of the Butterfly System unfolding'
            }

            logger.info(f"Evolutionary video created successfully: {output_name} ({file_size:.1f}MB, {len(frame_files)} frames)")
            return jsonify(result_data)

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error creating evolutionary video: {e}", exc_info=True)
        logger.error(f"Full traceback:\n{error_trace}")
        return jsonify({
            'error': f'Video creation failed: {str(e)}',
            'error_type': type(e).__name__,
            'traceback': error_trace,
            'troubleshooting': [
                '1. Check that FFmpeg is installed and accessible',
                '2. Verify snapshots exist in data/snapshots/ directory',
                '3. Ensure vision model is available for narration',
                '4. Check server logs for detailed error information',
                '5. Verify sufficient disk space for temporary video files'
            ]
        }), 500

def analyze_evolution_with_vision(snapshots):
    """Use vision model to create comprehensive evolution analysis for video narration"""
    try:
        if not snapshots or len(snapshots) < 3:
            return {'description': 'Insufficient snapshots for detailed evolution analysis.'}

        # Prepare images for vision analysis (use every 5th snapshot for overview)
        analysis_snapshots = snapshots[::max(1, len(snapshots) // 10)]  # Up to 10 key snapshots

        all_images = []
        for snapshot in analysis_snapshots:
            if isinstance(snapshot, dict) and 'image' in snapshot:
                all_images.append(snapshot['image'])

        if not all_images:
            return {'description': 'No valid images found for evolution analysis.'}

        # Create comprehensive evolution prompt
        evolution_prompt = f"""
        Analyze this sequence of {len(all_images)} causation graph snapshots showing the evolution of a complex system over time.

        Provide a detailed, cinematic narration suitable for a documentary video about the "unfolding of the butterfly" - the emergence of consciousness and complexity from simple beginnings.

        Focus on:
        1. The transformation from simple to complex structures
        2. Key evolutionary milestones and phase transitions
        3. The emergence of patterns, hierarchies, and self-organization
        4. Metaphors for consciousness emergence and complexity theory
        5. The beauty and inevitability of complex system evolution

        Make it poetic, scientific, and inspiring - like David Attenborough narrating the evolution of life itself, but for artificial consciousness emergence.

        Structure as a cohesive narrative suitable for voiceover narration in a high-quality documentary video.
        """

        # Call vision model with comprehensive evolution analysis
        try:
            ollama_response = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json={
                'model': 'gemma3:4b',  # Use vision-capable model
                'messages': [{
                    'role': 'user',
                    'content': evolution_prompt,
                    'images': all_images  # Send all evolution snapshots
                }],
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'num_predict': 1500  # Shorter for reliability
                }
            }, headers={'Content-Type': 'application/json'}, timeout=60)  # Shorter timeout
        except requests.exceptions.Timeout:
            return {'description': 'Vision analysis timed out. Video created without narration.'}
        except requests.exceptions.RequestException as e:
            return {'description': f'Vision analysis failed: {str(e)}. Video created without narration.'}

        if ollama_response.status_code == 200:
            result = ollama_response.json()
            description = result.get('message', {}).get('content', '')

            if not description or len(description.strip()) < 50:  # Require substantial analysis
                return {
                    'description': '',
                    'error': 'Vision model returned insufficient analysis',
                    'snapshots_analyzed': len(all_images)
                }

            return {
                'description': description,
                'snapshots_analyzed': len(all_images),
                'model_used': 'gemma3:4b'
            }
        else:
            return {
                'description': '',
                'error': f'Vision API failed: {ollama_response.status_code} - {ollama_response.text[:200]}',
                'snapshots_analyzed': len(all_images)
            }

    except Exception as e:
        logger.error(f"Error in evolution vision analysis: {e}")
        return {
            'description': '',
            'error': f'Vision analysis completely failed: {str(e)}',
            'snapshots_analyzed': len(all_images)
        }

@app.route('/api/export/create_video', methods=['POST'])
def create_video_from_frames():
    """Create MP4 video from uploaded PNG frames"""
    try:
        import subprocess
        import tempfile
        import shutil
        
        # Check if FFmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'], 
                          capture_output=True, 
                          check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return jsonify({
                'error': 'FFmpeg not found. Please install FFmpeg to create videos.',
                'install_help': {
                    'windows': 'Download from https://ffmpeg.org/download.html or use: winget install ffmpeg',
                    'mac': 'brew install ffmpeg',
                    'linux': 'sudo apt-get install ffmpeg'
                }
            }), 400
        
        # Get frames from request (base64 encoded PNGs)
        data = request.json
        frames = data.get('frames', [])  # Array of base64 PNG strings
        fps = data.get('fps', 30)
        output_name = data.get('output_name', f'causation_video_{int(time.time())}.mp4')
        
        if not frames:
            return jsonify({'error': 'No frames provided'}), 400
        
        # Create temporary directory for frames
        with tempfile.TemporaryDirectory() as temp_dir:
            frame_files = []
            
            # Save each frame as PNG file
            for i, frame_data in enumerate(frames):
                # Remove data URL prefix if present
                if ',' in frame_data:
                    frame_data = frame_data.split(',')[1]
                
                # Decode base64
                frame_bytes = base64.b64decode(frame_data)
                frame_path = os.path.join(temp_dir, f'frame_{i:04d}.png')
                
                with open(frame_path, 'wb') as f:
                    f.write(frame_bytes)
                frame_files.append(frame_path)
            
            # Create video using FFmpeg
            output_path = os.path.join(temp_dir, output_name)
            
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output
                '-framerate', str(fps),
                '-i', os.path.join(temp_dir, 'frame_%04d.png'),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-r', str(fps),
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return jsonify({
                    'error': 'FFmpeg encoding failed',
                    'details': result.stderr
                }), 500
            
            # Read video file and return as base64
            with open(output_path, 'rb') as f:
                video_data = base64.b64encode(f.read()).decode('utf-8')
            
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            
            return jsonify({
                'success': True,
                'video_data': video_data,
                'filename': output_name,
                'size_mb': round(file_size, 2),
                'frames': len(frames),
                'fps': fps,
                'duration': round(len(frames) / fps, 2)
            })
            
    except Exception as e:
        logger.error(f"Error creating video: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Create templates directory if needed
    templates_dir = Path(__file__).parent / 'templates'
# ============================================================================
# CONVERGENCE RESEARCH ASSISTANT - REAL-TIME EVENT STREAMING
# ============================================================================

# Background thread for event streaming
event_streaming_active = False
event_streaming_thread = None

def event_streaming_worker():
    """Background worker to stream events to connected CRA clients"""
    global event_streaming_active
    while event_streaming_active:
        try:
            # Get events from queue with timeout
            event = cra_event_queue.get(timeout=1.0)

            # Emit to all connected CRA clients
            if SOCKETIO_AVAILABLE:
                socketio.emit('cra_event', event, namespace='/cra')

            cra_event_queue.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Event streaming error: {e}")
            time.sleep(1.0)

def start_event_streaming():
    """Start the event streaming background thread"""
    global event_streaming_active, event_streaming_thread
    if not event_streaming_active:
        event_streaming_active = True
        event_streaming_thread = threading.Thread(target=event_streaming_worker, daemon=True)
        event_streaming_thread.start()
        logger.info("CRA event streaming started")

        # Start custodian health monitoring
        start_custodian_monitoring()

def start_custodian_monitoring():
    """Start the custodian's continuous health monitoring"""

    def custodian_monitor():
        """Continuous system health monitoring by the custodian"""
        import psutil  # Import here to ensure it's available in thread
        import time    # Import time for sleep functionality

        try:
            print("Custodian health monitoring activated")
        except:
            pass  # Fallback if print doesn't work

        while event_streaming_active:
            try:
                # Perform health check every 60 seconds
                time.sleep(60)

                if not event_streaming_active:
                    break

                # Quick health assessment
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()

                health_issues = []
                if cpu_percent > 85:
                    health_issues.append(f'High CPU: {cpu_percent}%')
                if memory.percent > 85:
                    health_issues.append(f'High memory: {memory.percent}%')

                if health_issues:
                    publish_cra_event('custodian_alert', {
                        'alert_type': 'resource_warning',
                        'issues': health_issues,
                        'severity': 'high' if cpu_percent > 90 or memory.percent > 90 else 'medium',
                        'timestamp': datetime.now().isoformat()
                    })

                # Note: Simulation status checking removed from background monitor
                # to avoid Flask application context issues. Use API endpoints instead.

            except Exception as e:
                try:
                    print(f"Custodian monitoring error: {e}")
                except:
                    pass  # Silent fallback
                time.sleep(30)  # Wait before retrying

    # Start monitoring thread
    monitor_thread = threading.Thread(target=custodian_monitor, daemon=True)
    monitor_thread.start()
    try:
        logger.info("Custodian continuous monitoring started")
    except:
        print("Custodian continuous monitoring started")

def stop_event_streaming():
    """Stop the event streaming background thread"""
    global event_streaming_active, event_streaming_thread
    event_streaming_active = False
    if event_streaming_thread:
        event_streaming_thread.join(timeout=2.0)
        logger.info("CRA event streaming stopped")

def publish_cra_event(event_type: str, data: Dict[str, Any]):
    """Publish an event to the CRA event stream"""
    try:
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'data': data
        }
        cra_event_queue.put_nowait(event)
    except queue.Full:
        try:
            print("CRA event queue full - dropping event")
        except:
            pass  # Silent fallback
    except Exception as e:
        try:
            print(f"CRA event publishing error: {e}")
        except:
            pass  # Silent fallback

# WebSocket event handlers
if SOCKETIO_AVAILABLE:
    @socketio.on('connect', namespace='/cra')
    def handle_cra_connect():
        """Handle CRA client connection"""
        logger.info("CRA client connected for real-time event streaming")
        emit('status', {'message': 'Connected to CRA event stream', 'timestamp': datetime.now().isoformat()})

    @socketio.on('disconnect', namespace='/cra')
    def handle_cra_disconnect():
        """Handle CRA client disconnection"""
        logger.info("CRA client disconnected from event stream")

    @socketio.on('subscribe', namespace='/cra')
    def handle_cra_subscribe(data):
        """Handle CRA subscription requests"""
        logger.info(f"CRA subscribed to events: {data}")
        emit('subscription_confirmed', {
            'message': f'Subscribed to: {data}',
            'timestamp': datetime.now().isoformat()
        })

# ============================================================================
# CONVERGENCE RESEARCH ASSISTANT - DIRECT API ACCESS
# ============================================================================

@app.route('/api/cra/data')
def cra_get_data():
    """Direct API access for Convergence Research Assistant - provides comprehensive system data"""
    try:
        import psutil
        from pathlib import Path

        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        memory_used_gb = memory.used / (1024**3)

        # Get simulation status from control file directly (avoid Flask context issues)
        try:
            control_file = project_root / 'data' / '.simulation_control.json'
            if control_file.exists():
                with open(control_file, 'r') as f:
                    control = json.load(f)
                    simulation_status = {
                        'running': control.get('running', False),
                        'paused': control.get('paused', True)
                    }
            else:
                simulation_status = {'running': False, 'paused': True}
        except Exception as e:
            simulation_status = {'running': False, 'paused': True, 'error': str(e)}

        # Get system state from logs (latest entries)
        logs_dir = Path('data/logs')
        latest_logs = {}

        if logs_dir.exists():
            for log_file in ['system.log', 'reality_sim.log', 'explorer.log', 'djinn_kernel.log']:
                log_path = logs_dir / log_file
                if log_path.exists():
                    try:
                        with open(log_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()[-10:]  # Last 10 entries
                            latest_logs[log_file] = [line.strip() for line in lines]
                    except Exception as e:
                        latest_logs[log_file] = [f"Error reading log: {e}"]

        # Get configuration data
        config_data = {}
        try:
            with open('config.json', 'r') as f:
                config_data = json.load(f)
        except Exception as e:
            config_data = {'error': f'Could not read config.json: {e}'}

        # Get causation graph stats
        graph_stats = get_stats().get_json()

        # Get recent events
        recent_events = get_new_events().get_json()

        # Compile comprehensive data package
        data = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_total_gb': round(memory_gb, 2),
                'memory_used_gb': round(memory_used_gb, 2),
                'platform': os.sys.platform
            },
            'simulation': simulation_status,
            'logs': latest_logs,
            'config': config_data,
            'graph': graph_stats,
            'recent_events': recent_events,
            'causation_explorer': {
                'initialized': explorer is not None,
                'event_count': graph_stats.get('total_events', 0),
                'link_count': graph_stats.get('total_links', 0)
            }
        }

        # Publish event about data access
        publish_cra_event('data_access', {
            'endpoints_accessed': ['system_metrics', 'simulation_status', 'logs', 'config', 'graph_stats'],
            'data_size': len(json.dumps(data)),
            'timestamp': datetime.now().isoformat()
        })

        return jsonify({
            'success': True,
            'data': data,
            'message': 'Direct API access granted to Convergence Research Assistant'
        })

    except Exception as e:
        logger.error(f"CRA API error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Error providing data to Convergence Research Assistant'
        }), 500

@app.route('/api/cra/system/state')
def cra_get_system_state():
    """Get current system state for CRA analysis with PC resource correlation"""
    try:
        import psutil
        # Get comprehensive PC system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get per-CPU usage for detailed analysis
        cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        
        # Get process-specific stats (this Python process)
        process = psutil.Process()
        process_memory = process.memory_info()
        process_cpu = process.cpu_percent(interval=0.1)

        # Get simulation status from control file directly
        try:
            control_file = project_root / 'data' / '.simulation_control.json'
            if control_file.exists():
                with open(control_file, 'r') as f:
                    control = json.load(f)
                    sim_status = {
                        'running': control.get('running', False),
                        'paused': control.get('paused', True)
                    }
            else:
                sim_status = {'running': False, 'paused': True}
        except Exception as e:
            sim_status = {'running': False, 'paused': True, 'error': str(e)}

        # Get Butterfly System metrics from shared state
        butterfly_metrics = {}
        try:
            shared_state_path = project_root / 'data' / 'shared_state.json'
            if shared_state_path.exists():
                with open(shared_state_path, 'r') as f:
                    shared_state = json.load(f)
                    data = shared_state.get('data', {})
                    
                    # Extract Butterfly System resource usage
                    if 'lattice' in data:
                        l = data['lattice']
                        butterfly_metrics['lattice_cpu'] = l.get('cpu_usage', 0)
                        butterfly_metrics['lattice_ram'] = l.get('ram_usage', 0)
                    
                    butterfly_metrics['frame_count'] = shared_state.get('frame_count', 0)
                    butterfly_metrics['simulation_fps'] = shared_state.get('simulation_fps', 0.0)
        except Exception as e:
            logger.warning(f"Could not load Butterfly System metrics: {e}")

        # Get graph data
        graph_data = get_graph().get_json()

        # Calculate resource correlation
        correlation = {
            'butterfly_cpu_vs_total': butterfly_metrics.get('lattice_cpu', 0) / max(cpu_percent, 1) if cpu_percent > 0 else 0,
            'butterfly_ram_vs_total': butterfly_metrics.get('lattice_ram', 0) / max(memory.used / (1024*1024), 1) if memory.used > 0 else 0,
            'resource_efficiency': {
                'nodes_per_cpu_percent': graph_data.get('total_nodes', 0) / max(cpu_percent, 1) if cpu_percent > 0 else 0,
                'links_per_mb_ram': graph_data.get('total_links', 0) / max(memory.used / (1024*1024), 1) if memory.used > 0 else 0
            }
        }

        state = {
            'timestamp': datetime.now().isoformat(),
            'simulation': {
                'running': sim_status.get('running', False),
                'paused': sim_status.get('paused', True),
                'frame': butterfly_metrics.get('frame_count', 0),
                'fps': butterfly_metrics.get('simulation_fps', 0.0),
                'phase': sim_status.get('phase', 'unknown')
            },
            'pc_resources': {
                'cpu': {
                    'total_percent': cpu_percent,
                    'per_core': cpu_per_core,
                    'core_count': cpu_count,
                    'process_cpu': process_cpu
                },
                'memory': {
                    'total_gb': memory.total / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'percent': memory.percent,
                    'process_mb': process_memory.rss / (1024**2)
                },
                'disk': {
                    'total_gb': disk.total / (1024**3),
                    'used_gb': disk.used / (1024**3),
                    'free_gb': disk.free / (1024**3),
                    'percent': disk.percent
                }
            },
            'butterfly_system': {
                'lattice_cpu_percent': butterfly_metrics.get('lattice_cpu', 0),
                'lattice_ram_mb': butterfly_metrics.get('lattice_ram', 0),
                'total_nodes': graph_data.get('total_nodes', 0),
                'total_links': graph_data.get('total_links', 0)
            },
            'correlation': correlation,
            'warnings': []
        }

        # Generate warnings if PC is being overtaxed
        if cpu_percent > 85:
            state['warnings'].append(f'⚠️ High CPU usage: {cpu_percent:.1f}% - Consider reducing simulation complexity or render quality')
        if memory.percent > 85:
            state['warnings'].append(f'⚠️ High memory usage: {memory.percent:.1f}% - Consider reducing max visible elements')
        if correlation['butterfly_cpu_vs_total'] > 0.8:
            state['warnings'].append('⚠️ Butterfly System using >80% of total CPU - system may be overtaxed')
        if correlation['butterfly_ram_vs_total'] > 0.5:
            state['warnings'].append('⚠️ Butterfly System using >50% of total RAM - consider optimization')

        return jsonify({
            'success': True,
            'state': state
        })

    except Exception as e:
        logger.error(f"CRA system state error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cra/logs')
def cra_get_logs():
    """Provide log file access to CRA"""
    try:
        from pathlib import Path

        logs_dir = Path('data/logs')
        log_data = {}

        if logs_dir.exists():
            for log_file in ['system.log', 'reality_sim.log', 'explorer.log', 'djinn_kernel.log', 'application.log']:
                log_path = logs_dir / log_file
                if log_path.exists():
                    try:
                        with open(log_path, 'r', encoding='utf-8') as f:
                            # Get last 50 lines to avoid overwhelming
                            lines = f.readlines()[-50:]
                            log_data[log_file] = {
                                'entries': len(lines),
                                'last_modified': os.path.getmtime(log_path),
                                'content': [line.strip() for line in lines]
                            }
                    except Exception as e:
                        log_data[log_file] = {'error': str(e)}

        return jsonify({
            'success': True,
            'logs': log_data,
            'message': f'Log data provided to CRA: {len(log_data)} log files'
        })

    except Exception as e:
        logger.error(f"CRA logs error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cra/config')
def cra_get_config():
    """Provide configuration access to CRA"""
    try:
        config_files = {}

        # Main config
        try:
            with open('config.json', 'r') as f:
                config_files['config.json'] = json.load(f)
        except Exception as e:
            config_files['config.json'] = {'error': str(e)}

        # Ollama config
        try:
            with open('data/causation_explorer/ollama_config.json', 'r') as f:
                config_files['ollama_config.json'] = json.load(f)
        except Exception as e:
            config_files['ollama_config.json'] = {'error': str(e)}

        # Publish event about config access
        publish_cra_event('config_access', {
            'files_accessed': list(config_files.keys()),
            'timestamp': datetime.now().isoformat()
        })

        return jsonify({
            'success': True,
            'config': config_files,
            'message': 'Configuration data provided to CRA'
        })

    except Exception as e:
        logger.error(f"CRA config error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cra/events/stream')
def cra_event_stream():
    """Server-Sent Events stream for CRA real-time data"""
    def generate():
        while True:
            try:
                # Get event from queue with timeout
                event = cra_event_queue.get(timeout=30.0)

                # Format as SSE
                yield f"data: {json.dumps(event)}\n\n"
                cra_event_queue.task_done()

            except queue.Empty:
                # Send heartbeat every 30 seconds
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
            except GeneratorExit:
                break

    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/cra/events/recent')
def cra_get_recent_events():
    """Get recent events from the CRA event queue"""
    try:
        events = []
        # Get up to 50 recent events without blocking
        for _ in range(min(50, cra_event_queue.qsize())):
            try:
                event = cra_event_queue.get_nowait()
                events.append(event)
                # Put it back since we're just reading
                cra_event_queue.put_nowait(event)
            except queue.Empty:
                break

        return jsonify({
            'success': True,
            'events': events,
            'count': len(events),
            'message': f'Retrieved {len(events)} recent CRA events'
        })

    except Exception as e:
        logger.error(f"CRA recent events error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cra/health/check')
def cra_health_check():
    """Comprehensive system health check by the custodian"""
    try:
        import psutil
        from pathlib import Path

        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': 'healthy',
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }

        # System resource check
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        if cpu_percent > 90:
            health_status['critical_issues'].append(f'CPU usage critically high: {cpu_percent}%')
            health_status['overall_health'] = 'critical'
        elif cpu_percent > 75:
            health_status['warnings'].append(f'High CPU usage: {cpu_percent}%')

        if memory.percent > 90:
            health_status['critical_issues'].append(f'Memory usage critically high: {memory.percent}%')
            health_status['overall_health'] = 'critical'
        elif memory.percent > 80:
            health_status['warnings'].append(f'High memory usage: {memory.percent}%')

        # Log file health check
        logs_dir = Path('data/logs')
        if logs_dir.exists():
            total_log_size = sum(f.stat().st_size for f in logs_dir.glob('*.log') if f.exists())
            if total_log_size > 100 * 1024 * 1024:  # 100MB
                health_status['warnings'].append(f'Large log files: {total_log_size/1024/1024:.1f}MB')
                health_status['recommendations'].append('Consider log rotation or cleanup')

        # Configuration integrity check
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            # Check for required sections
            required_sections = ['simulation', 'quantum', 'evolution', 'network']
            missing_sections = [s for s in required_sections if s not in config]
            if missing_sections:
                health_status['critical_issues'].append(f'Missing config sections: {missing_sections}')
                health_status['overall_health'] = 'critical'
        except Exception as e:
            health_status['critical_issues'].append(f'Config file corrupted: {e}')
            health_status['overall_health'] = 'critical'

        # Simulation state check
        try:
            control_file = project_root / 'data' / '.simulation_control.json'
            if control_file.exists():
                with open(control_file, 'r') as f:
                    control = json.load(f)
                    sim_running = control.get('running', False)
                    if not sim_running:
                        health_status['warnings'].append('Simulation not currently running')
            else:
                health_status['warnings'].append('Simulation control file missing')
        except Exception as e:
            health_status['warnings'].append(f'Cannot check simulation status: {e}')

        # Publish health check event
        publish_cra_event('health_check', {
            'overall_health': health_status['overall_health'],
            'critical_count': len(health_status['critical_issues']),
            'warning_count': len(health_status['warnings']),
            'timestamp': datetime.now().isoformat()
        })

        return jsonify(health_status)

    except Exception as e:
        logger.error(f"Custodian health check error: {e}", exc_info=True)
        return jsonify({
            'overall_health': 'error',
            'error': str(e),
            'custodian_status': 'health_check_failed'
        }), 500

@app.route('/api/cra/guardian/mode', methods=['POST'])
def cra_guardian_mode():
    """Enable guardian/custodian mode for protective monitoring"""
    try:
        data = request.get_json() or {}
        mode = data.get('mode', 'enable')

        if mode == 'enable':
            # Enable enhanced monitoring
            start_event_streaming()
            publish_cra_event('guardian_mode', {
                'status': 'activated',
                'capabilities': ['continuous_monitoring', 'anomaly_detection', 'protective_actions'],
                'timestamp': datetime.now().isoformat()
            })
            return jsonify({
                'status': 'guardian_mode_activated',
                'message': 'Custodian protective monitoring enabled',
                'capabilities': [
                    'Real-time system monitoring',
                    'Anomaly detection and alerting',
                    'Configuration integrity protection',
                    'Resource usage monitoring',
                    'Automatic health assessments'
                ]
            })
        else:
            # Could add disable logic here
            return jsonify({'status': 'guardian_mode_unchanged'})

    except Exception as e:
        logger.error(f"Guardian mode error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/snapshots/store', methods=['POST'])
def store_evolutionary_snapshot():
    """Store evolutionary snapshot on server for long-term accumulation"""
    try:
        data = request.get_json()
        snapshot = data.get('snapshot')

        if not snapshot or not isinstance(snapshot, dict):
            return jsonify({'error': 'Invalid snapshot data'}), 400

        # Create snapshots directory if it doesn't exist
        snapshots_dir = Path('data/snapshots')
        snapshots_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = snapshot.get('timestamp', int(time.time() * 1000))
        filename = f'snapshot_{timestamp}.json'
        filepath = snapshots_dir / filename

        # Add server metadata
        snapshot['server_received'] = int(time.time() * 1000)
        snapshot['evolution_sequence'] = data.get('evolution_sequence', 0)

        # Save snapshot
        with open(filepath, 'w') as f:
            json.dump(snapshot, f, indent=2)

        # Maintain snapshot index
        index_file = snapshots_dir / 'snapshot_index.json'
        if index_file.exists():
            with open(index_file, 'r') as f:
                index = json.load(f)
        else:
            index = {'snapshots': [], 'total_count': 0, 'evolution_sequences': {}}

        index['snapshots'].append({
            'filename': filename,
            'timestamp': timestamp,
            'evolution_sequence': snapshot.get('evolution_sequence', 0)
        })
        index['total_count'] = len(index['snapshots'])

        # Keep last 10,000 snapshots for fluid video creation (allows ~5-10 minute videos at 30 FPS)
        # Each snapshot ~50-150KB, so 10,000 = ~500MB-1.5GB (reasonable for video production)
        MAX_SNAPSHOTS_STORAGE = 10000
        if len(index['snapshots']) > MAX_SNAPSHOTS_STORAGE:
            # Remove oldest files
            oldest_snapshots = index['snapshots'][:len(index['snapshots']) - MAX_SNAPSHOTS_STORAGE]
            for old_snapshot in oldest_snapshots:
                old_file = snapshots_dir / old_snapshot['filename']
                if old_file.exists():
                    old_file.unlink()
            index['snapshots'] = index['snapshots'][-MAX_SNAPSHOTS_STORAGE:]

        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)

        return jsonify({
            'success': True,
            'snapshot_stored': filename,
            'total_snapshots': index['total_count'],
            'message': f'Evolutionary snapshot stored. Total accumulated: {index["total_count"]}'
        })

    except Exception as e:
        logger.error(f"Error storing evolutionary snapshot: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/snapshots/list')
def list_evolutionary_snapshots():
    """List all accumulated evolutionary snapshots"""
    try:
        snapshots_dir = Path('data/snapshots')
        index_file = snapshots_dir / 'snapshot_index.json'

        if not index_file.exists():
            return jsonify({
                'snapshots': [],
                'total_count': 0,
                'message': 'No evolutionary snapshots accumulated yet'
            })

        with open(index_file, 'r') as f:
            index = json.load(f)

        # Add file size information
        for snapshot in index['snapshots']:
            filepath = snapshots_dir / snapshot['filename']
            if filepath.exists():
                snapshot['file_size_kb'] = round(filepath.stat().st_size / 1024, 1)
            else:
                snapshot['file_size_kb'] = 0

        return jsonify({
            'snapshots': index['snapshots'],
            'total_count': index['total_count'],
            'evolution_sequences': list(set(s['evolution_sequence'] for s in index['snapshots'])),
            'message': f'Found {index["total_count"]} evolutionary snapshots'
        })

    except Exception as e:
        logger.error(f"Error listing evolutionary snapshots: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/snapshots/get/<filename>')
def get_evolutionary_snapshot(filename):
    """Retrieve a specific evolutionary snapshot"""
    try:
        snapshots_dir = Path('data/snapshots')
        filepath = snapshots_dir / filename

        if not filepath.exists():
            return jsonify({'error': 'Snapshot not found'}), 404

        with open(filepath, 'r') as f:
            snapshot = json.load(f)

        return jsonify({
            'success': True,
            'snapshot': snapshot,
            'filename': filename
        })

    except Exception as e:
        logger.error(f"Error retrieving evolutionary snapshot: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/snapshots/clear', methods=['POST'])
def clear_evolutionary_snapshots():
    """Clear all accumulated evolutionary snapshots"""
    try:
        snapshots_dir = Path('data/snapshots')

        if snapshots_dir.exists():
            # Remove all snapshot files
            for file in snapshots_dir.glob('*.json'):
                file.unlink()

        return jsonify({
            'success': True,
            'message': 'All evolutionary snapshots cleared'
        })

    except Exception as e:
        logger.error(f"Error clearing evolutionary snapshots: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/cra/status')
def cra_custodian_status():
    """Get the current status of the system custodian"""
    try:
        custodian_status = {
            'timestamp': datetime.now().isoformat(),
            'role': 'System Custodian',
            'status': 'active',
            'capabilities': [
                'continuous_health_monitoring',
                'real_time_event_streaming',
                'configuration_validation',
                'anomaly_detection',
                'resource_protection',
                'system_integrity_guardian'
            ],
            'active_endpoints': [
                '/api/cra/health/check',
                '/api/cra/guardian/mode',
                '/api/cra/data',
                '/api/cra/system/state',
                '/api/cra/logs',
                '/api/cra/config',
                '/api/cra/events/stream',
                '/api/cra/events/recent',
                '/api/cra/config/validate'
            ],
            'monitoring': {
                'event_streaming': event_streaming_active,
                'websocket_support': SOCKETIO_AVAILABLE,
                'health_checks': True,
                'anomaly_detection': True
            },
            'last_health_check': datetime.now().isoformat(),
            'protection_status': 'active'
        }

        return jsonify({
            'custodian': custodian_status,
            'message': 'System Custodian status report'
        })

    except Exception as e:
        logger.error(f"Custodian status error: {e}", exc_info=True)
        return jsonify({
            'custodian': {'status': 'error', 'error': str(e)},
            'message': 'Custodian status unavailable'
        }), 500

@app.route('/api/cra/graph/filters', methods=['GET'])
def cra_get_graph_filters():
    """Get current graph filter settings for CRA to read"""
    try:
        # Return current filter state (frontend maintains this, but we can provide defaults)
        return jsonify({
            'components': {
                'reality_sim': True,
                'reality_simulator': True,
                'explorer': True,
                'djinn_kernel': True,
                'utm_kernel': True,
                'breath': True,
                'system': True
            },
            'causation_types': {
                'threshold': True,
                'correlation': True,
                'direct': True,
                'temporal': True
            },
            'display': {
                'show_labels': True,
                'show_links': True,
                'show_temporal_paths': False
            },
            'message': 'Graph filter settings. Use POST to update them.'
        })
    except Exception as e:
        logger.error(f"Error getting graph filters: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/cra/diagnostics/vp_history', methods=['GET'])
def cra_get_vp_history():
    """Get historical VP calculation values for CRA deep-dive analysis"""
    try:
        # Get number of breaths to retrieve (default 50)
        breaths = int(request.args.get('breaths', 50))
        
        # Try to load VP history from shared state or logs
        vp_history = []
        
        # Method 1: Try to read from shared state if it contains VP history
        if shared_state_path.exists():
            try:
                with open(shared_state_path, 'r') as f:
                    state = json.load(f)
                    # Check if VP history is embedded in state
                    if 'vp_history' in state.get('data', {}).get('djinn_kernel', {}):
                        vp_history = state['data']['djinn_kernel']['vp_history'][-breaths:]
            except:
                pass
        
        # Method 2: Parse from logs if available
        if not vp_history:
            logs_dir = Path('data/logs')
            djinn_log = logs_dir / 'djinn_kernel.log'
            if djinn_log.exists():
                try:
                    with open(djinn_log, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[-500:]  # Last 500 lines
                        for line in lines:
                            if 'violation_pressure' in line.lower() or 'vp=' in line.lower():
                                # Try to extract VP value
                                import re
                                vp_match = re.search(r'vp[=:]?\s*([0-9.]+)', line.lower())
                                if vp_match:
                                    vp_value = float(vp_match.group(1))
                                    # Extract timestamp if available
                                    timestamp_match = re.search(r'(\d{2}:\d{2}:\d{2})', line)
                                    timestamp = timestamp_match.group(1) if timestamp_match else None
                                    vp_history.append({
                                        'vp': vp_value,
                                        'timestamp': timestamp,
                                        'raw_line': line.strip()
                                    })
                    # Limit to requested breaths
                    vp_history = vp_history[-breaths:]
                except Exception as e:
                    logger.debug(f"Could not parse VP history from logs: {e}")
        
        return jsonify({
            'success': True,
            'vp_history': vp_history,
            'count': len(vp_history),
            'requested_breaths': breaths,
            'message': f'VP history for last {len(vp_history)} breath cycles'
        })
    except Exception as e:
        logger.error(f"Error getting VP history: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'vp_history': []
        }), 500

@app.route('/api/cra/diagnostics/network_trends', methods=['GET'])
def cra_get_network_trends():
    """Get network modularity and clustering coefficient trends"""
    try:
        # Get number of data points (default 50)
        points = int(request.args.get('points', 50))
        
        trends = {
            'modularity': [],
            'clustering_coefficient': [],
            'connections_per_organism': [],
            'organism_count': []
        }
        
        # Parse from logs
        logs_dir = Path('data/logs')
        reality_log = logs_dir / 'reality_sim.log'
        if reality_log.exists():
            try:
                with open(reality_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-1000:]  # Last 1000 lines for better coverage
                    for line in lines:
                        # Extract modularity
                        mod_match = re.search(r'mod(ularity)?[=:]?\s*([0-9.]+)', line.lower())
                        if mod_match:
                            trends['modularity'].append({
                                'value': float(mod_match.group(2)),
                                'timestamp': re.search(r'(\d{2}:\d{2}:\d{2})', line).group(1) if re.search(r'(\d{2}:\d{2}:\d{2})', line) else None
                            })
                        
                        # Extract clustering
                        clust_match = re.search(r'clust(ering)?[=:]?\s*([0-9.]+)', line.lower())
                        if clust_match:
                            trends['clustering_coefficient'].append({
                                'value': float(clust_match.group(2)),
                                'timestamp': re.search(r'(\d{2}:\d{2}:\d{2})', line).group(1) if re.search(r'(\d{2}:\d{2}:\d{2})', line) else None
                            })
                        
                        # Extract organism count
                        org_match = re.search(r'org(anisms)?[=:]?\s*(\d+)', line.lower())
                        if org_match:
                            trends['organism_count'].append({
                                'value': int(org_match.group(2)),
                                'timestamp': re.search(r'(\d{2}:\d{2}:\d{2})', line).group(1) if re.search(r'(\d{2}:\d{2}:\d{2})', line) else None
                            })
                        
                        # Extract connections
                        conn_match = re.search(r'conn(ections)?[=:]?\s*(\d+)', line.lower())
                        if conn_match and trends['organism_count']:
                            conn_count = int(conn_match.group(2))
                            # Calculate connections per organism
                            if trends['organism_count'][-1]['value'] > 0:
                                trends['connections_per_organism'].append({
                                    'value': conn_count / trends['organism_count'][-1]['value'],
                                    'timestamp': re.search(r'(\d{2}:\d{2}:\d{2})', line).group(1) if re.search(r'(\d{2}:\d{2}:\d{2})', line) else None
                                })
                
                # Limit to requested points
                for key in trends:
                    trends[key] = trends[key][-points:]
            except Exception as e:
                logger.debug(f"Could not parse network trends from logs: {e}")
        
        return jsonify({
            'success': True,
            'trends': trends,
            'points': points,
            'message': 'Network metrics trends extracted from logs'
        })
    except Exception as e:
        logger.error(f"Error getting network trends: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'trends': {}
        }), 500

@app.route('/api/cra/diagnostics/memory_breakdown', methods=['GET'])
def cra_get_memory_breakdown():
    """Get component-level memory allocation breakdown"""
    try:
        import psutil
        import os
        
        breakdown = {
            'total_memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'used_memory_gb': round(psutil.virtual_memory().used / (1024**3), 2),
            'available_memory_gb': round(psutil.virtual_memory().available / (1024**3), 2),
            'memory_percent': psutil.virtual_memory().percent,
            'components': {}
        }
        
        # Try to get process-specific memory if possible
        try:
            current_process = psutil.Process(os.getpid())
            breakdown['process_memory_mb'] = round(current_process.memory_info().rss / (1024**2), 2)
        except:
            pass
        
        # Parse component memory from logs if available
        logs_dir = Path('data/logs')
        for log_file in ['reality_sim.log', 'explorer.log', 'djinn_kernel.log']:
            log_path = logs_dir / log_file
            if log_path.exists():
                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[-100:]
                        for line in lines:
                            # Look for RAM/memory mentions
                            ram_match = re.search(r'ram[=:]?\s*([0-9.]+)\s*(mb|gb)?', line.lower())
                            if ram_match:
                                component = log_file.replace('.log', '')
                                if component not in breakdown['components']:
                                    breakdown['components'][component] = {
                                        'memory_mb': float(ram_match.group(1)),
                                        'last_seen': re.search(r'(\d{2}:\d{2}:\d{2})', line).group(1) if re.search(r'(\d{2}:\d{2}:\d{2})', line) else None
                                    }
                except:
                    pass
        
        return jsonify({
            'success': True,
            'memory_breakdown': breakdown,
            'message': 'Component-level memory allocation breakdown'
        })
    except Exception as e:
        logger.error(f"Error getting memory breakdown: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'memory_breakdown': {}
        }), 500

@app.route('/api/cra/diagnostics/event_throughput', methods=['GET'])
def cra_get_event_throughput():
    """Get event bus throughput metrics"""
    try:
        throughput = {
            'events_per_second': 0,
            'total_events': 0,
            'causation_links': 0,
            'event_types': {},
            'component_distribution': {}
        }
        
        # Get graph stats
        if explorer:
            throughput['total_events'] = len(explorer.events)
            throughput['causation_links'] = explorer.causation_graph.number_of_edges()
            
            # Calculate events per second from graph
            if explorer.events:
                timestamps = [event.timestamp for event in explorer.events.values()]
                if timestamps:
                    time_span = max(timestamps) - min(timestamps)
                    if time_span > 0:
                        throughput['events_per_second'] = len(explorer.events) / time_span
            
            # Event type distribution
            for event_id, event in explorer.events.items():
                etype = event.event_type
                throughput['event_types'][etype] = throughput['event_types'].get(etype, 0) + 1
                comp = event.component
                throughput['component_distribution'][comp] = throughput['component_distribution'].get(comp, 0) + 1
        
        return jsonify({
            'success': True,
            'throughput': throughput,
            'message': 'Event bus throughput metrics'
        })
    except Exception as e:
        logger.error(f"Error getting event throughput: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'throughput': {}
        }), 500

@app.route('/api/cra/diagnostics/breath_cycles', methods=['GET'])
def cra_get_breath_cycles():
    """Get breath cycle duration statistics"""
    try:
        cycles = {
            'total_cycles': 0,
            'average_duration_seconds': 0,
            'cycle_history': [],
            'inhale_exhale_ratio': 0
        }
        
        # Parse from logs
        logs_dir = Path('data/logs')
        explorer_log = logs_dir / 'explorer.log'
        if explorer_log.exists():
            try:
                with open(explorer_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-1000:]
                    breath_times = []
                    inhale_count = 0
                    exhale_count = 0
                    
                    for i, line in enumerate(lines):
                        # Look for breath cycle mentions
                        if 'breath' in line.lower() and 'cycle' in line.lower():
                            cycle_match = re.search(r'cycle[=:]?\s*(\d+)', line.lower())
                            if cycle_match:
                                cycle_num = int(cycle_match.group(1))
                                timestamp_match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d+)', line)
                                if timestamp_match:
                                    breath_times.append({
                                        'cycle': cycle_num,
                                        'timestamp': timestamp_match.group(1)
                                    })
                        
                        # Count inhale/exhale
                        if 'inhale' in line.lower():
                            inhale_count += 1
                        elif 'exhale' in line.lower():
                            exhale_count += 1
                    
                    cycles['total_cycles'] = breath_times[-1]['cycle'] if breath_times else 0
                    cycles['inhale_exhale_ratio'] = inhale_count / exhale_count if exhale_count > 0 else 0
                    
                    # Calculate average duration
                    if len(breath_times) >= 2:
                        # Parse timestamps and calculate intervals
                        intervals = []
                        for i in range(1, len(breath_times)):
                            try:
                                # Simple time difference (assuming HH:MM:SS format)
                                t1_parts = breath_times[i-1]['timestamp'].split(':')
                                t2_parts = breath_times[i]['timestamp'].split(':')
                                if len(t1_parts) == 3 and len(t2_parts) == 3:
                                    t1_sec = float(t1_parts[0])*3600 + float(t1_parts[1])*60 + float(t1_parts[2])
                                    t2_sec = float(t2_parts[0])*3600 + float(t2_parts[1])*60 + float(t2_parts[2])
                                    intervals.append(abs(t2_sec - t1_sec))
                            except:
                                pass
                        
                        if intervals:
                            cycles['average_duration_seconds'] = sum(intervals) / len(intervals)
                            cycles['cycle_history'] = breath_times[-50:]  # Last 50 cycles
            except Exception as e:
                logger.debug(f"Could not parse breath cycles from logs: {e}")
        
        # Also check shared state
        if shared_state_path.exists():
            try:
                with open(shared_state_path, 'r') as f:
                    state = json.load(f)
                    explorer_data = state.get('data', {}).get('explorer', {})
                    if 'breath_cycle' in explorer_data:
                        cycles['total_cycles'] = explorer_data['breath_cycle']
            except:
                pass
        
        return jsonify({
            'success': True,
            'breath_cycles': cycles,
            'message': 'Breath cycle duration statistics'
        })
    except Exception as e:
        logger.error(f"Error getting breath cycles: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'breath_cycles': {}
        }), 500

@app.route('/api/cra/graph/filters', methods=['POST'])
def cra_set_graph_filters():
    """Set graph filter settings - allows CRA to manipulate graph view when explicitly requested"""
    try:
        data = request.get_json()
        
        # Validate request structure
        if not data:
            return jsonify({'error': 'No filter data provided'}), 400
        
        # Extract filter settings
        components = data.get('components', {})
        causation_types = data.get('causation_types', {})
        display = data.get('display', {})
        
        # Build response with instructions for frontend
        filter_update = {
            'components': {
                'reality_sim': components.get('reality_sim', components.get('reality_simulator', True)),
                'reality_simulator': components.get('reality_simulator', components.get('reality_sim', True)),
                'explorer': components.get('explorer', True),
                'djinn_kernel': components.get('djinn_kernel', True),
                'utm_kernel': components.get('utm_kernel', components.get('djinn_kernel', True)),
                'breath': components.get('breath', True),
                'system': components.get('system', True)
            },
            'causation_types': {
                'threshold': causation_types.get('threshold', True),
                'correlation': causation_types.get('correlation', True),
                'direct': causation_types.get('direct', True),
                'temporal': causation_types.get('temporal', True)
            },
            'display': {
                'show_labels': display.get('show_labels', True),
                'show_links': display.get('show_links', True),
                'show_temporal_paths': display.get('show_temporal_paths', False)
            }
        }
        
        logger.info(f"CRA requested graph filter update: {filter_update}")
        
        return jsonify({
            'success': True,
            'filters': filter_update,
            'message': 'Graph filters updated. Frontend should apply these settings.',
            'frontend_instructions': {
                'note': 'The frontend JavaScript should listen for these updates and apply them to the graph view.',
                'checkboxes_to_update': {
                    'components': {
                        'filter-reality_sim': filter_update['components']['reality_sim'],
                        'filter-explorer': filter_update['components']['explorer'],
                        'filter-djinn_kernel': filter_update['components']['djinn_kernel'],
                        'filter-breath': filter_update['components']['breath'],
                        'filter-system': filter_update['components']['system']
                    },
                    'causation_types': {
                        'filter-threshold': filter_update['causation_types']['threshold'],
                        'filter-correlation': filter_update['causation_types']['correlation'],
                        'filter-direct': filter_update['causation_types']['direct'],
                        'filter-temporal': filter_update['causation_types']['temporal']
                    },
                    'display': {
                        'show-labels': filter_update['display']['show_labels'],
                        'show-links': filter_update['display']['show_links'],
                        'show-temporal-paths': filter_update['display']['show_temporal_paths']
                    }
                },
                'functions_to_call': [
                    'applyFilters()',
                    'toggleLabels()',
                    'toggleLinks()',
                    'toggleTemporalPaths()'
                ]
            }
        })
    except Exception as e:
        logger.error(f"Error setting graph filters: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/cra/graph/viz-settings', methods=['GET'])
def cra_get_viz_settings():
    """Get current visualization settings for CRA to read"""
    try:
        # Return default visualization settings structure
        return jsonify({
            'linkBaseWidth': 2.5,
            'linkMaxWidth': 16,
            'linkMinOpacity': 0.35,
            'linkMaxOpacity': 1.0,
            'linkDensityMultiplier': 6.0,
            'linkDepthMultiplier': 3.0,
            'linkNodeConnMultiplier': 2.0,
            'nodeBaseSize': 8,
            'nodeMaxSize': 12,
            'nodeMinOpacity': 0.6,
            'nodeMaxOpacity': 1.0,
            'nodeDepthSizeMultiplier': 4.0,
            'nodeStrokeWidth': 3,
            'nodeStrokeOpacity': 1.0,
            'depthStrength': 1.0,
            'depthOpacityRange': 0.5,
            'depthSizeRange': 0.4,
            'depthParallaxAmount': 0.5,
            'enableShadows': True,
            'enableGlow': True,
            'shadowOffset': 2,
            'shadowBlur': 3,
            'glowIntensity': 2,
            'frontColorBrightness': 1.0,
            'backColorBrightness': 0.7,
            'colorSaturation': 1.0,
            'maxVisibleLinks': 10000,
            'maxVisibleNodes': 5000,
            'renderQuality': 'high',
            'enableTransitions': True,
            'transitionDuration': 300,
            'animationSpeed': 1.0,
            'message': 'Visualization settings structure. Frontend maintains actual values.'
        })
    except Exception as e:
        logger.error(f"Error getting viz settings: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/cra/graph/viz-settings', methods=['POST'])
def cra_set_viz_settings():
    """Set visualization settings - allows CRA to manipulate visualization when explicitly requested"""
    try:
        data = request.get_json()
        
        # Validate request structure
        if not data:
            return jsonify({'error': 'No visualization settings data provided'}), 400
        
        # Extract visualization settings (all optional, only update what's provided)
        viz_settings = {}
        
        # Link appearance
        if 'linkBaseWidth' in data:
            viz_settings['linkBaseWidth'] = float(data['linkBaseWidth'])
        if 'linkMaxWidth' in data:
            viz_settings['linkMaxWidth'] = float(data['linkMaxWidth'])
        if 'linkMinOpacity' in data:
            viz_settings['linkMinOpacity'] = float(data['linkMinOpacity'])
        if 'linkMaxOpacity' in data:
            viz_settings['linkMaxOpacity'] = float(data['linkMaxOpacity'])
        if 'linkDensityMultiplier' in data:
            viz_settings['linkDensityMultiplier'] = float(data['linkDensityMultiplier'])
        if 'linkDepthMultiplier' in data:
            viz_settings['linkDepthMultiplier'] = float(data['linkDepthMultiplier'])
        if 'linkNodeConnMultiplier' in data:
            viz_settings['linkNodeConnMultiplier'] = float(data['linkNodeConnMultiplier'])
        
        # Node appearance
        if 'nodeBaseSize' in data:
            viz_settings['nodeBaseSize'] = float(data['nodeBaseSize'])
        if 'nodeMaxSize' in data:
            viz_settings['nodeMaxSize'] = float(data['nodeMaxSize'])
        if 'nodeMinOpacity' in data:
            viz_settings['nodeMinOpacity'] = float(data['nodeMinOpacity'])
        if 'nodeMaxOpacity' in data:
            viz_settings['nodeMaxOpacity'] = float(data['nodeMaxOpacity'])
        if 'nodeDepthSizeMultiplier' in data:
            viz_settings['nodeDepthSizeMultiplier'] = float(data['nodeDepthSizeMultiplier'])
        if 'nodeStrokeWidth' in data:
            viz_settings['nodeStrokeWidth'] = float(data['nodeStrokeWidth'])
        if 'nodeStrokeOpacity' in data:
            viz_settings['nodeStrokeOpacity'] = float(data['nodeStrokeOpacity'])
        
        # Depth effects
        if 'depthStrength' in data:
            viz_settings['depthStrength'] = float(data['depthStrength'])
        if 'depthOpacityRange' in data:
            viz_settings['depthOpacityRange'] = float(data['depthOpacityRange'])
        if 'depthSizeRange' in data:
            viz_settings['depthSizeRange'] = float(data['depthSizeRange'])
        if 'depthParallaxAmount' in data:
            viz_settings['depthParallaxAmount'] = float(data['depthParallaxAmount'])
        
        # Visual effects
        if 'enableShadows' in data:
            viz_settings['enableShadows'] = bool(data['enableShadows'])
        if 'enableGlow' in data:
            viz_settings['enableGlow'] = bool(data['enableGlow'])
        if 'shadowOffset' in data:
            viz_settings['shadowOffset'] = float(data['shadowOffset'])
        if 'shadowBlur' in data:
            viz_settings['shadowBlur'] = float(data['shadowBlur'])
        if 'glowIntensity' in data:
            viz_settings['glowIntensity'] = float(data['glowIntensity'])
        
        # Color settings
        if 'frontColorBrightness' in data:
            viz_settings['frontColorBrightness'] = float(data['frontColorBrightness'])
        if 'backColorBrightness' in data:
            viz_settings['backColorBrightness'] = float(data['backColorBrightness'])
        if 'colorSaturation' in data:
            viz_settings['colorSaturation'] = float(data['colorSaturation'])
        
        # Performance
        if 'maxVisibleLinks' in data:
            viz_settings['maxVisibleLinks'] = int(data['maxVisibleLinks'])
        if 'maxVisibleNodes' in data:
            viz_settings['maxVisibleNodes'] = int(data['maxVisibleNodes'])
        if 'renderQuality' in data:
            viz_settings['renderQuality'] = str(data['renderQuality'])
        
        # Animation
        if 'enableTransitions' in data:
            viz_settings['enableTransitions'] = bool(data['enableTransitions'])
        if 'transitionDuration' in data:
            viz_settings['transitionDuration'] = int(data['transitionDuration'])
        if 'animationSpeed' in data:
            viz_settings['animationSpeed'] = float(data['animationSpeed'])
        
        # Component colors
        component_color_keys = ['componentColor_reality_sim', 'componentColor_explorer', 'componentColor_djinn_kernel', 
                               'componentColor_breath', 'componentColor_system']
        for key in component_color_keys:
            if key in data:
                viz_settings[key] = str(data[key])
        
        # Link colors
        link_color_keys = ['linkColor_threshold', 'linkColor_correlation', 'linkColor_direct', 'linkColor_temporal', 'linkColor_unknown']
        for key in link_color_keys:
            if key in data:
                viz_settings[key] = str(data[key])
        
        logger.info(f"CRA requested visualization settings update: {viz_settings}")
        
        return jsonify({
            'success': True,
            'viz_settings': viz_settings,
            'message': 'Visualization settings updated. Frontend should apply these settings.',
            'frontend_instructions': {
                'note': 'The frontend JavaScript should apply these settings using applyVizSettingsFromCRA() function.',
                'marker_format': '[[VIZ_SETTINGS_UPDATE: {...}]]',
                'settings': viz_settings
            }
        })
    except Exception as e:
        logger.error(f"Error setting visualization settings: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/cra/config/validate', methods=['POST'])
def cra_validate_config():
    """Validate configuration files for CRA"""
    try:
        # Get config to validate from request or use current configs
        data = request.get_json() or {}
        config_to_validate = data.get('config')

        validation_results = {}

        # Validate main config structure
        required_main_keys = ['simulation', 'quantum', 'evolution', 'network', 'agency', 'rendering']
        if config_to_validate and 'config.json' in config_to_validate:
            main_config = config_to_validate['config.json']
            missing_keys = [key for key in required_main_keys if key not in main_config]
            validation_results['config.json'] = {
                'valid': len(missing_keys) == 0,
                'missing_keys': missing_keys,
                'structure_check': 'passed' if len(missing_keys) == 0 else 'failed'
            }
        else:
            # Validate current config
            try:
                with open('config.json', 'r') as f:
                    current_config = json.load(f)
                missing_keys = [key for key in required_main_keys if key not in current_config]
                validation_results['config.json'] = {
                    'valid': len(missing_keys) == 0,
                    'missing_keys': missing_keys,
                    'structure_check': 'passed' if len(missing_keys) == 0 else 'failed'
                }
            except Exception as e:
                validation_results['config.json'] = {
                    'valid': False,
                    'error': str(e)
                }

        # Validate Ollama config
        required_ollama_keys = ['base_url', 'timeout']
        if config_to_validate and 'ollama_config.json' in config_to_validate:
            ollama_config = config_to_validate['ollama_config.json']
            missing_keys = [key for key in required_ollama_keys if key not in ollama_config]
            validation_results['ollama_config.json'] = {
                'valid': len(missing_keys) == 0,
                'missing_keys': missing_keys,
                'structure_check': 'passed' if len(missing_keys) == 0 else 'failed'
            }
        else:
            # Validate current ollama config
            try:
                with open('data/causation_explorer/ollama_config.json', 'r') as f:
                    current_ollama = json.load(f)
                missing_keys = [key for key in required_ollama_keys if key not in current_ollama]
                validation_results['ollama_config.json'] = {
                    'valid': len(missing_keys) == 0,
                    'missing_keys': missing_keys,
                    'structure_check': 'passed' if len(missing_keys) == 0 else 'failed'
                }
            except Exception as e:
                validation_results['ollama_config.json'] = {
                    'valid': False,
                    'error': str(e)
                }

        overall_valid = all(result.get('valid', False) for result in validation_results.values())

        # Publish validation event
        publish_cra_event('config_validation', {
            'overall_valid': overall_valid,
            'results': validation_results,
            'timestamp': datetime.now().isoformat()
        })

        return jsonify({
            'success': True,
            'validation': validation_results,
            'overall_valid': overall_valid,
            'message': 'Configuration validation completed for CRA'
        })

    except Exception as e:
        logger.error(f"CRA config validation error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# MAIN APPLICATION
# ============================================================================

if __name__ == '__main__':
    templates_dir.mkdir(exist_ok=True)

    # Initialize CRA event streaming on startup
    start_event_streaming()

    print("🔬 Causation Explorer Web UI")
    print("Open http://localhost:5000 in your browser")
    print("🛡️  SYSTEM CUSTODIAN - Autonomous Guardian Active")
    print("🤖 Custodian Real-time API Endpoints:")
    print("   /api/cra/status - Custodian status and capabilities")
    print("   /api/cra/health/check - Comprehensive system health")
    print("   /api/cra/guardian/mode - Enable protective monitoring")
    print("   /api/cra/data - Comprehensive system data")
    print("   /api/cra/system/state - Current system state")
    print("   /api/cra/logs - Log file access")
    print("   /api/cra/config - Configuration access")
    print("   /api/cra/events/stream - Real-time event stream")
    print("   /api/cra/events/recent - Recent events")
    print("   /api/cra/config/validate - Config validation")

    try:
        if SOCKETIO_AVAILABLE:
            print("🔌 WebSocket support enabled for CRA real-time streaming")
            # Use_reloader=False to avoid threading issues on Windows during development
            # Set to True if you want auto-reload (may show socket errors on Windows)
            socketio.run(app, debug=True, port=5000, use_reloader=False)
        else:
            print("📡 WebSocket not available - using HTTP polling for CRA")
            # Use_reloader=False to avoid threading issues on Windows during development
            app.run(debug=True, port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down gracefully...")
    finally:
        # Cleanup on shutdown
        stop_event_streaming()
        print("✅ Cleanup complete")

