import logging
import os
from typing import Dict, Any
from src.infrastructure.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class LandingGenerator:
    """Генератор лендингів на основі гіпотез."""
    
    def __init__(self, ollama_client: OllamaClient, output_dir: str = "landings"):
        self.ollama = ollama_client
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    async def generate(self, hypothesis_id: str, hypothesis_data: Dict[str, Any]) -> str:
        """
        Генерує HTML-код лендингу для гіпотези та зберігає у файл.
        Повертає шлях до збереженого файлу.
        """
        problem = hypothesis_data.get("description", "Unknown problem")
        mvp = hypothesis_data.get("mvp", "MVP not specified")
        headline = hypothesis_data.get("landing_headline", "New Solution for Your Problem")
        cta = hypothesis_data.get("cta", "Get Started")

        prompt = f"""
        Generate a modern landing page HTML for the following product hypothesis.
        
        Problem: {problem}
        MVP Solution: {mvp}
        Headline: {headline}
        Call to Action: {cta}
        
        Requirements:
        - Use only HTML and inline CSS (no external dependencies)
        - Modern, clean design with a dark or light theme (choose what fits best)
        - Include a simple email capture form (no backend, just form with action="#")
        - Use the headline prominently at the top
        - Describe the problem and solution in a clear way
        - Include a button for the call to action
        - Make it responsive and mobile-friendly
        
        Output ONLY the complete HTML code, starting with <!DOCTYPE html>.
        """
        
        system_prompt = "You are a professional web designer and frontend developer. Generate clean, modern HTML landing pages."
        
        response = await self.ollama.generate(prompt, system_prompt)
        
        if not response:
            logger.error("Failed to generate landing page from Ollama")
            return self._fallback_template(hypothesis_id, hypothesis_data)
        
        # Перевіряємо, чи є HTML-тег, якщо ні — обгортаємо
        if "<!DOCTYPE html>" not in response and "<html" not in response:
            logger.warning("Generated response is not valid HTML, using fallback")
            return self._fallback_template(hypothesis_id, hypothesis_data)
        
        # Зберігаємо у файл
        filename = os.path.join(self.output_dir, f"{hypothesis_id}.html")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response)
        
        logger.info(f"✅ Landing page saved: {filename}")
        return filename

    def _fallback_template(self, hypothesis_id: str, data: Dict[str, Any]) -> str:
        """Простий шаблон-заглушка, якщо генерація не вдалася."""
        problem = data.get("description", "Your problem")
        mvp = data.get("mvp", "Our solution")
        headline = data.get("landing_headline", "We solve your problem")
        cta = data.get("cta", "Join now")
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{headline}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0a; color: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 2rem; }}
        .container {{ max-width: 600px; width: 100%; }}
        h1 {{ font-size: 2.5rem; font-weight: 700; margin-bottom: 1.5rem; background: linear-gradient(to right, #f0f0f0, #aaa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        p {{ font-size: 1.2rem; line-height: 1.6; color: #ccc; margin-bottom: 1.5rem; }}
        .cta-button {{ display: inline-block; background: #fff; color: #0a0a0a; padding: 0.8rem 2rem; border-radius: 50px; font-weight: 600; text-decoration: none; margin-top: 1rem; cursor: pointer; border: none; font-size: 1.1rem; }}
        .cta-button:hover {{ background: #e0e0e0; }}
        .form-group {{ margin-top: 2rem; }}
        input[type="email"] {{ width: 100%; padding: 0.8rem; border-radius: 8px; border: 1px solid #333; background: #1a1a1a; color: #fff; font-size: 1rem; }}
        input[type="email"]:focus {{ outline: none; border-color: #888; }}
        .submit-btn {{ margin-top: 0.5rem; }}
        .disclaimer {{ font-size: 0.8rem; color: #666; margin-top: 1rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{headline}</h1>
        <p><strong>Problem:</strong> {problem}</p>
        <p><strong>Solution:</strong> {mvp}</p>
        <form action="#" method="POST">
            <div class="form-group">
                <input type="email" placeholder="Enter your email" required>
                <button type="submit" class="cta-button submit-btn">{cta}</button>
            </div>
        </form>
        <p class="disclaimer">We respect your privacy. No spam.</p>
    </div>
</body>
</html>"""
        
        filename = os.path.join(self.output_dir, f"{hypothesis_id}.html")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        logger.warning(f"⚠️ Used fallback template for {hypothesis_id}")
        return filename
