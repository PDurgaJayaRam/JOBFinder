"""Application submission orchestrator - ties form analysis, filling, and submission."""
import os
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.browser_agent.browser_controller import BrowserController
from agents.auto_apply.form_analyzer import FormAnalyzer, FormAnalysis
from agents.auto_apply.question_answerer import ScreeningQuestionAnswerer
from agents.vision_scraper.multi_provider_client import MultiProviderAIClient

logger = logging.getLogger(__name__)


class AutoApplyAgent:
    """Automates job application submission."""

    def __init__(
        self,
        browser: BrowserController,
        ai_client: Optional[MultiProviderAIClient] = None,
    ):
        self.browser = browser
        self.ai_client = ai_client
        self.form_analyzer = FormAnalyzer(ai_client=ai_client)
        self.question_answerer = ScreeningQuestionAnswerer(ai_client=ai_client)

    async def apply_to_job(
        self,
        apply_url: str,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any],
        resume_file_path: Optional[str] = None,
        user_review_required: bool = True,
    ) -> Dict[str, Any]:
        """Execute full application flow for a job."""
        start_time = time.time()
        result = {
            "success": False,
            "url": apply_url,
            "steps_completed": [],
            "errors": [],
            "fields_filled": 0,
            "questions_answered": 0,
            "fields_needing_review": [],
            "submitted": False,
            "time_elapsed_ms": 0,
        }

        try:
            if not self.browser.page:
                await self.browser.start()

            await self.browser.go_to(apply_url, timeout=30000)
            await self.browser.wait(3)
            result["steps_completed"].append("navigation")

            form_analysis = await self.form_analyzer.analyze_form_dom(self.browser.page)
            result["fields_needing_review"] = form_analysis.fields_needing_review
            result["steps_completed"].append("form_analysis")

            if not form_analysis.can_auto_fill and user_review_required:
                result["errors"].append("Form requires manual review")
                result["analysis"] = self._form_analysis_to_dict(form_analysis)
                result["time_elapsed_ms"] = int((time.time() - start_time) * 1000)
                return result

            filled = await self._fill_form(form_analysis, resume_data, job_data)
            result["fields_filled"] = filled
            result["steps_completed"].append("form_filling")

            answered = await self._answer_screening_questions(
                form_analysis.screening_questions,
                resume_data,
                job_data,
            )
            result["questions_answered"] = answered
            result["steps_completed"].append("screening_questions")

            if form_analysis.submit_button:
                await self._submit_application(form_analysis)
                result["submitted"] = True
                result["steps_completed"].append("submission")

            result["success"] = True

        except Exception as e:
            logger.error(f"Application failed: {e}")
            result["errors"].append(str(e))

        result["time_elapsed_ms"] = int((time.time() - start_time) * 1000)
        return result

    async def _fill_form(
        self,
        form_analysis: FormAnalysis,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any],
    ) -> int:
        """Fill form fields using Playwright."""
        filled = 0
        page = self.browser.page

        for field in form_analysis.text_fields:
            if field.needs_user_input:
                continue
            
            value = self._get_field_value(field, resume_data)
            if not value:
                continue
            
            try:
                selector = f'#{field.field_id}' if field.field_id else f'[placeholder="{field.placeholder}"]'
                await page.fill(selector, value, timeout=3000)
                filled += 1
            except Exception:
                try:
                    await page.evaluate(f"""() => {{
                        const el = document.elementFromPoint({field.x_coordinate}, {field.y_coordinate});
                        if (el) {{ el.value = '{value}'; el.dispatchEvent(new Event('input', {{ bubbles: true }})); }}
                    }}""")
                    filled += 1
                except Exception as e:
                    logger.warning(f"Failed to fill field {field.label}: {e}")

        for field in form_analysis.select_fields:
            if field.options and field.field_id:
                try:
                    await page.select_option(f'#{field.field_id}', field.options[0], timeout=3000)
                    filled += 1
                except Exception:
                    pass

        return filled

    async def _answer_screening_questions(
        self,
        questions: List,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any],
    ) -> int:
        """Answer screening questions."""
        answered = 0
        page = self.browser.page

        for q in questions:
            if q.needs_review:
                continue
            
            answer_result = await self.question_answerer.answer_question(
                question=q.question_text,
                question_type=q.question_type,
                options=q.options,
                resume_data=resume_data,
                job_data=job_data,
            )
            
            if answer_result.get("answer"):
                try:
                    await page.evaluate(f"""() => {{
                        const el = document.elementFromPoint({q.x_coordinate}, {q.y_coordinate});
                        if (el) {{
                            const input = el.nextElementSibling?.querySelector('input, textarea') || el.querySelector('input, textarea');
                            if (input) {{ input.value = '{answer_result["answer"]}'; input.dispatchEvent(new Event('input', {{ bubbles: true }})); }}
                        }}
                    }}""")
                    answered += 1
                except Exception as e:
                    logger.warning(f"Failed to answer question: {e}")

        return answered

    async def _submit_application(self, form_analysis: FormAnalysis):
        """Click submit button."""
        page = self.browser.page
        btn = form_analysis.submit_button
        
        try:
            selector = f'#{btn.field_id}' if btn.field_id else None
            if selector:
                await page.click(selector, timeout=5000)
            else:
                await page.evaluate(f"""() => {{
                    const el = document.elementFromPoint({btn.x_coordinate}, {btn.y_coordinate});
                    if (el) el.click();
                }}""")
            await self.browser.wait(3)
        except Exception as e:
            logger.warning(f"Submit click failed: {e}")

    def _get_field_value(self, field, resume_data: Dict[str, Any]) -> str:
        """Get value to fill for a field based on resume data."""
        label_lower = field.label.lower()
        placeholder_lower = field.placeholder.lower()
        text = f"{label_lower} {placeholder_lower}"
        
        if "email" in text:
            return resume_data.get("email", "")
        elif "phone" in text:
            return resume_data.get("phone", "")
        elif "name" in text and "first" in text:
            return resume_data.get("name", "").split()[0] if resume_data.get("name") else ""
        elif "name" in text and "last" in text:
            parts = resume_data.get("name", "").split()
            return parts[-1] if len(parts) > 1 else ""
        elif "name" in text:
            return resume_data.get("name", "")
        elif "linkedin" in text:
            return resume_data.get("linkedin_url", "")
        elif "portfolio" in text or "website" in text:
            return resume_data.get("portfolio_url", "")
        elif "location" in text or "city" in text:
            return resume_data.get("location", "")
        elif "zip" in text or "postal" in text:
            return resume_data.get("zip_code", "")
        elif "salary" in text or "ctc" in text:
            return ""
        elif "experience" in text and "year" in text:
            return str(int(resume_data.get("experience_years", 0)))
        
        return ""

    def _form_analysis_to_dict(self, analysis: FormAnalysis) -> Dict[str, Any]:
        """Convert FormAnalysis to serializable dict."""
        return {
            "url": analysis.url,
            "portal": analysis.portal,
            "total_fields": analysis.total_fields,
            "can_auto_fill": analysis.can_auto_fill,
            "fields_needing_review": analysis.fields_needing_review,
            "estimated_fill_time_seconds": analysis.estimated_fill_time_seconds,
            "screening_questions_count": len(analysis.screening_questions),
            "file_uploads_count": len(analysis.file_uploads),
        }
