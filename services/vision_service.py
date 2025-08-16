import anthropic
import os
from typing import Optional

class VisionService:
    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def describe_image(self, image_base64: str, custom_prompt: Optional[str] = None) -> str:
        """Generate visual description of image using Claude API"""
        try:
            # Default prompt for screenshot analysis
            default_prompt = """Analyze this screenshot and provide a detailed description focusing on:
1. UI elements (buttons, menus, forms, dialogs)
2. Text content and layout
3. Visual components (charts, images, icons)
4. Overall purpose and context
5. Any error messages or notifications
6. Color schemes and visual patterns

Be specific about what you see - this will be used for searching screenshots later."""
            
            prompt = custom_prompt or default_prompt
            
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            return message.content[0].text
        
        except Exception as e:
            print(f"Vision analysis failed: {e}")
            return f"Vision analysis unavailable: {str(e)}"
    
    def extract_visual_elements(self, image_base64: str) -> dict:
        """Extract specific visual elements for better search"""
        prompt = """Analyze this screenshot and extract:
1. Colors: List dominant colors
2. UI Elements: buttons, forms, modals, etc.
3. Text Style: headings, body text, code, etc.
4. Layout: grid, sidebar, header, etc.
5. Content Type: dashboard, form, error page, etc.

Format as JSON-like structure for easy parsing."""
        
        try:
            description = self.describe_image(image_base64, prompt)
            return {"detailed_analysis": description}
        except:
            return {"detailed_analysis": "Analysis failed"}