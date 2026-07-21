import logging
import os
from typing import Dict, Any
from src.infrastructure.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class LandingGenerator:
    """Генератор лендингів на основі шаблону з динамічним контентом."""
    
    def __init__(self, ollama_client: OllamaClient, output_dir: str = "landings"):
        self.ollama = ollama_client
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "landing_template.html")
        with open(template_path, "r", encoding="utf-8") as f:
            self.template = f.read()

    async def generate(self, hypothesis_id: str, hypothesis_data: Dict[str, Any]) -> str:
        problem = hypothesis_data.get("description", "Unknown problem")
        mvp = hypothesis_data.get("mvp", "MVP not specified")
        headline = hypothesis_data.get("landing_headline", "New Solution for Your Problem")
        cta = hypothesis_data.get("cta", "Get Started")
        
        features_html = await self._generate_features(problem, mvp)
        
        html = self.template
        html = html.replace("{{HYPOTHESIS_ID}}", hypothesis_id)
        html = html.replace("{{HEADLINE}}", headline)
        html = html.replace("{{PROBLEM_DESC}}", problem[:200] + "..." if len(problem) > 200 else problem)
        html = html.replace("{{PROBLEM}}", problem)
        html = html.replace("{{MVP}}", mvp)
        html = html.replace("{{CTA}}", cta)
        html = html.replace("{{PRODUCT_NAME}}", "Opportunity Hunter")
        html = html.replace("{{FEATURES}}", features_html)
        
        filename = os.path.join(self.output_dir, f"{hypothesis_id}.html")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        
        logger.info(f"✅ Landing page saved: {filename}")
        return filename

    async def _generate_features(self, problem: str, mvp: str) -> str:
        prompt = f"""
        Generate 3 key features/benefits for a product that solves this problem: "{problem}"
        The solution is: "{mvp}"
        
        Return as 3 short bullet points, each with a short emoji title and 1 sentence description.
        Format:
        <div class="card feature">
            <div class="icon">🚀</div>
            <div>
                <h3>Title</h3>
                <p>Description</p>
            </div>
        </div>
        Use only the HTML structure above, no extra text.
        """
        
        response = await self.ollama.generate(prompt)
        if response and "<div class=\"card feature\">" in response:
            return response
        else:
            return """
            <div class="card feature">
                <div class="icon">🧩</div>
                <div>
                    <h3>Simple & Intuitive</h3>
                    <p>Designed to be easy to use, no learning curve required.</p>
                </div>
            </div>
            <div class="card feature">
                <div class="icon">⚡</div>
                <div>
                    <h3>Fast & Efficient</h3>
                    <p>Get results in minutes, not weeks.</p>
                </div>
            </div>
            <div class="card feature">
                <div class="icon">📊</div>
                <div>
                    <h3>Data-Driven</h3>
                    <p>Every decision backed by real user insights.</p>
                </div>
            </div>
            """
